"""
Builds a ranked shortlist of eligible cleaners for a job. The system only
ever *recommends* — the admin always makes the final call, with the option
to override and pick any eligible cleaner.

Eligibility (hard filters, applied before ranking):
  - Cleaner is active.
  - Gender matches the job's preference, if one was set.
  - Cleaner is not on this customer's blocklist.
  - Cleaner is not already assigned (accepted) to another job the same day.

Ranking (soft score, used only to order the eligible pool):
  - Proximity to the job location (closer is better).
  - Current workload this week (lighter load is better — spreads jobs out).
  - Rating / past performance.
  - Availability signal (currently: not already offered another job today).

The weights are intentionally simple and documented so an admin or future
developer can retune them without touching the eligibility rules.
"""
from dataclasses import dataclass
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt

from django.utils import timezone

from cleaners.models import BlocklistEntry, Cleaner
from .models import Job, JobAssignment

WEIGHT_PROXIMITY = Decimal("0.40")
WEIGHT_WORKLOAD = Decimal("0.25")
WEIGHT_RATING = Decimal("0.25")
WEIGHT_AVAILABILITY = Decimal("0.10")

MAX_RELEVANT_DISTANCE_KM = Decimal("25")


@dataclass
class RankedCleaner:
    cleaner: Cleaner
    score: Decimal
    breakdown: dict


def _haversine_km(lat1, lon1, lat2, lon2) -> Decimal:
    lat1, lon1, lat2, lon2 = map(radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return Decimal(str(2 * 6371 * asin(sqrt(a))))


def eligible_cleaners(job: Job):
    """Hard filters only — no ranking yet."""
    blocked_ids = BlocklistEntry.objects.filter(customer=job.customer).values_list("cleaner_id", flat=True)

    queryset = Cleaner.objects.select_related("user").filter(is_active=True).exclude(id__in=blocked_ids)

    if job.gender_preference != Job.GenderPreference.ANY:
        queryset = queryset.filter(gender=job.gender_preference)

    already_committed = JobAssignment.objects.filter(
        job__requested_date=job.requested_date,
        status=JobAssignment.Status.ACCEPTED,
    ).exclude(job=job).values_list("cleaner_id", flat=True)
    queryset = queryset.exclude(id__in=already_committed)

    return queryset


def _workload_this_week(cleaner: Cleaner) -> int:
    today = timezone.localdate()
    week_start = today - timezone.timedelta(days=today.weekday())
    week_end = week_start + timezone.timedelta(days=6)
    return JobAssignment.objects.filter(
        cleaner=cleaner,
        status=JobAssignment.Status.ACCEPTED,
        job__requested_date__range=(week_start, week_end),
    ).count()


def _already_offered_today(cleaner: Cleaner, job: Job) -> bool:
    return JobAssignment.objects.filter(
        cleaner=cleaner,
        status__in=[JobAssignment.Status.OFFERED, JobAssignment.Status.RECOMMENDED],
        job__requested_date=job.requested_date,
    ).exclude(job=job).exists()


def build_shortlist(job: Job, limit: int = 5) -> list[RankedCleaner]:
    candidates = eligible_cleaners(job)
    workloads = [_workload_this_week(c) for c in candidates]
    max_workload = max(workloads) if workloads else 0

    ranked = []
    for cleaner in candidates:
        breakdown = {}

        # Proximity — closer scores higher; missing coordinates score neutral (0.5).
        if job.latitude is not None and job.longitude is not None and cleaner.home_latitude is not None:
            distance_km = _haversine_km(job.latitude, job.longitude, cleaner.home_latitude, cleaner.home_longitude)
            proximity_score = max(Decimal("0"), 1 - min(distance_km, MAX_RELEVANT_DISTANCE_KM) / MAX_RELEVANT_DISTANCE_KM)
            breakdown["distance_km"] = round(float(distance_km), 1)
        else:
            proximity_score = Decimal("0.5")
        breakdown["proximity_score"] = float(proximity_score)

        # Workload — fewer jobs this week scores higher.
        workload = _workload_this_week(cleaner)
        workload_score = Decimal("1") if max_workload == 0 else (1 - Decimal(workload) / Decimal(max_workload))
        breakdown["jobs_this_week"] = workload
        breakdown["workload_score"] = float(workload_score)

        # Rating — normalised out of 5.
        rating_score = min(Decimal("1"), cleaner.rating / Decimal("5"))
        breakdown["rating"] = float(cleaner.rating)
        breakdown["rating_score"] = float(rating_score)

        # Availability — penalise a cleaner already juggling an offer today.
        availability_score = Decimal("0.3") if _already_offered_today(cleaner, job) else Decimal("1")
        breakdown["availability_score"] = float(availability_score)

        total = (
            proximity_score * WEIGHT_PROXIMITY
            + workload_score * WEIGHT_WORKLOAD
            + rating_score * WEIGHT_RATING
            + availability_score * WEIGHT_AVAILABILITY
        )
        ranked.append(RankedCleaner(cleaner=cleaner, score=total.quantize(Decimal("0.001")), breakdown=breakdown))

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked[:limit]
