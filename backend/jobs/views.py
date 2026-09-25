from django.db import transaction
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from audit.utils import log_action
from cleaners.models import Cleaner
from common.permissions import IsAdmin, IsCleaner
from notifications.services import notify_admin_response, notify_job_offer, notify_job_packet

from .matching import build_shortlist
from .models import Job, JobAssignment, StatusChange
from .serializers import (
    AssignCleanerSerializer,
    JobCreateSerializer,
    JobDetailSerializer,
    JobListSerializer,
    JobPacketSerializer,
    RespondToOfferSerializer,
)


def _record_status_change(job: Job, from_status: str, to_status: str, changed_by, note: str = ""):
    StatusChange.objects.create(job=job, from_status=from_status, to_status=to_status, changed_by=changed_by, note=note)


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.select_related("customer").prefetch_related("assignments__cleaner__user", "status_history")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "requested_date", "gender_preference"]

    def get_serializer_class(self):
        if self.action == "create":
            return JobCreateSerializer
        if self.action == "list":
            return JobListSerializer
        return JobDetailSerializer

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()
        if user.role == "admin":
            return qs
        if user.role == "cleaner":
            return qs.filter(assignments__cleaner__user=user).distinct()
        if user.role == "customer":
            return qs.filter(customer__user=user)
        return qs.none()

    def perform_create(self, serializer):
        user = self.request.user
        admin_user = user if user.role == "admin" else None

        if user.role == "customer":
            customer = user.customer_profile
            serializer.validated_data["customer"] = customer
        elif user.role == "cleaner":
            customer = getattr(user, "customer_profile", None)
            if customer is None:
                raise ValueError("A cleaner account must be linked to a customer profile to create a job.")
            serializer.validated_data["customer"] = customer
        elif user.role == "admin" and not serializer.validated_data.get("customer"):
            raise ValueError("Admin job intake requires a customer record.")

        instance = serializer.save(taken_by_admin=admin_user)
        _record_status_change(instance, "", Job.Status.REQUESTED, self.request.user)
        log_action(self.request.user, "create_job_request", target=instance, metadata={
            "intake_channel": instance.intake_channel,
        })

    # ------------------------------------------------------------------
    # Shortlist: admin asks the system to recommend eligible cleaners.
    # ------------------------------------------------------------------
    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def shortlist(self, request, pk=None):
        job = self.get_object()
        ranked = build_shortlist(job)

        with transaction.atomic():
            JobAssignment.objects.filter(job=job, status=JobAssignment.Status.RECOMMENDED).delete()
            assignments = [
                JobAssignment(job=job, cleaner=r.cleaner, status=JobAssignment.Status.RECOMMENDED,
                               rank_score=r.score, rank_breakdown=r.breakdown)
                for r in ranked
            ]
            JobAssignment.objects.bulk_create(assignments)
            if job.status == Job.Status.REQUESTED:
                job.status = Job.Status.SHORTLISTED
                job.save(update_fields=["status"])
                _record_status_change(job, Job.Status.REQUESTED, Job.Status.SHORTLISTED, request.user)

        log_action(request.user, "generate_shortlist", target=job, metadata={"count": len(ranked)})
        return Response(JobDetailSerializer(job, context={"request": request}).data)

    # ------------------------------------------------------------------
    # Assign: admin picks someone from the shortlist, or overrides with
    # any other eligible cleaner. The system never auto-assigns.
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def assign(self, request, pk=None):
        job = self.get_object()
        serializer = AssignCleanerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cleaner = Cleaner.objects.filter(id=serializer.validated_data["cleaner_id"], is_active=True).first()
        if cleaner is None:
            return Response({"detail": "Cleaner not found or inactive."}, status=status.HTTP_404_NOT_FOUND)

        with transaction.atomic():
            assignment, _ = JobAssignment.objects.update_or_create(
                job=job, cleaner=cleaner,
                defaults={"status": JobAssignment.Status.OFFERED, "offered_at": timezone.now()},
            )
            previous_status = job.status
            job.status = Job.Status.ASSIGNED
            job.assigned_by = request.user
            job.save(update_fields=["status", "assigned_by"])
            _record_status_change(job, previous_status, Job.Status.ASSIGNED, request.user,
                                   note=f"Offered to {cleaner}")

        notify_job_offer(cleaner, job)
        log_action(request.user, "assign_cleaner", target=job, metadata={"cleaner_id": cleaner.id})
        return Response(JobDetailSerializer(job, context={"request": request}).data)

    # ------------------------------------------------------------------
    # Cleaner accepts or declines the offer (SMS "confirm" hits the same
    # endpoint via a small webhook shim — see notifications app).
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsCleaner], url_path="respond")
    def respond(self, request, pk=None):
        job = self.get_object()
        serializer = RespondToOfferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        accept = serializer.validated_data["accept"]

        assignment = job.assignments.filter(
            cleaner__user=request.user, status=JobAssignment.Status.OFFERED
        ).first()
        if assignment is None:
            return Response({"detail": "You have no pending offer for this job."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            assignment.status = JobAssignment.Status.ACCEPTED if accept else JobAssignment.Status.DECLINED
            assignment.responded_at = timezone.now()
            assignment.save(update_fields=["status", "responded_at"])

            previous_status = job.status
            job.status = Job.Status.ACCEPTED if accept else Job.Status.SHORTLISTED
            job.responded_at = timezone.now()
            job.save(update_fields=["status", "responded_at"])
            _record_status_change(
                job, previous_status, job.status, request.user,
                note="Cleaner accepted" if accept else "Cleaner declined — back to admin for reassignment",
            )

        from accounts.models import User
        notify_admin_response(User.objects.filter(role="admin"), job, "accepted" if accept else "declined")
        log_action(request.user, "respond_to_offer", target=job, metadata={"accepted": accept})
        return Response(JobDetailSerializer(job, context={"request": request}).data)

    # ------------------------------------------------------------------
    # Admin submits the post-acceptance detail packet, which is what
    # actually reveals the access code to the accepted cleaner.
    # ------------------------------------------------------------------
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsAdmin])
    def packet(self, request, pk=None):
        job = self.get_object()
        if job.status != Job.Status.ACCEPTED:
            return Response(
                {"detail": "The job packet can only be sent after a cleaner has accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = JobPacketSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        job.start_time = data["start_time"]
        job.timeframe_minutes = data["timeframe_minutes"]
        job.special_instructions = data.get("special_instructions", "")
        if data.get("access_code"):
            job.access_code = data["access_code"]
        previous_status = job.status
        job.status = Job.Status.IN_PROGRESS
        job.packet_sent_at = timezone.now()
        job.save(update_fields=[
            "start_time", "timeframe_minutes", "special_instructions",
            "access_code", "status", "packet_sent_at",
        ])
        _record_status_change(job, previous_status, Job.Status.IN_PROGRESS, request.user, note="Job packet sent")

        assignment = job.assignments.filter(status=JobAssignment.Status.ACCEPTED).first()
        if assignment:
            notify_job_packet(assignment.cleaner, job)

        log_action(request.user, "send_job_packet", target=job)
        return Response(JobDetailSerializer(job, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def complete(self, request, pk=None):
        job = self.get_object()
        user = request.user
        is_assigned_cleaner = job.assignments.filter(cleaner__user=user, status=JobAssignment.Status.ACCEPTED).exists()
        if user.role != "admin" and not is_assigned_cleaner:
            return Response({"detail": "Not permitted."}, status=status.HTTP_403_FORBIDDEN)

        previous_status = job.status
        job.status = Job.Status.COMPLETED
        job.completed_at = timezone.now()
        job.access_code = ""  # hidden again after completion
        job.save(update_fields=["status", "completed_at", "access_code"])
        _record_status_change(job, previous_status, Job.Status.COMPLETED, user)

        assignment = job.assignments.filter(status=JobAssignment.Status.ACCEPTED).first()
        if assignment:
            cleaner = assignment.cleaner
            cleaner.completed_jobs = cleaner.completed_jobs + 1
            cleaner.save(update_fields=["completed_jobs"])

        log_action(user, "complete_job", target=job)
        return Response(JobDetailSerializer(job, context={"request": request}).data)

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated, IsAdmin])
    def access_code(self, request, pk=None):
        """Explicit, separately audited read of the access code — kept apart
        from the general job detail payload so every view is logged."""
        job = self.get_object()
        log_action(request.user, "view_access_code", target=job)
        return Response({"access_code": job.access_code, "access_code_location": job.access_code_location})
