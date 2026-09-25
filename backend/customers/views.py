from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from audit.utils import log_action
from common.permissions import IsAdmin

from .models import Customer
from .serializers import CustomerPublicSerializer, CustomerSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Admins get full CRUD, including creating phone-in customers.
    A logged-in customer can only view/update their own profile.
    """
    queryset = Customer.objects.all().order_by("full_name")
    search_fields = ["full_name", "phone_number"]

    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.role == "admin":
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.user.role == "admin":
            return CustomerSerializer
        return CustomerPublicSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return super().get_queryset()
        return super().get_queryset().filter(user=user)

    def perform_create(self, serializer):
        instance = serializer.save(created_by_admin=True)
        log_action(self.request.user, "create_customer", target=instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        log_action(self.request.user, "update_customer", target=instance)
