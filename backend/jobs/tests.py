from django.test import RequestFactory, TestCase

from accounts.models import User
from accounts.views import PromoteAdminView
from customers.models import Customer
from jobs.views import JobViewSet


class JobPermissionTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_customer_can_create_job_request(self):
        user = User.objects.create_user(
            username="customer1",
            password="pass1234567",
            role=User.Role.CUSTOMER,
            phone_number="+2348000000001",
        )
        Customer.objects.create(user=user, full_name="Jane Customer", phone_number=user.phone_number)

        request = self.factory.post(
            "/jobs/",
            {
                "location_summary": "King's Court",
                "cleaners_needed": 1,
                "gender_preference": "any",
                "requested_date": "2026-09-25",
                "requires_access_code": False,
                "access_code_location": "",
                "access_code": "",
                "intake_channel": "app",
            },
        )
        request.user = user

        view = JobViewSet()
        view.action = "create"

        self.assertTrue(all(permission.has_permission(request, view) for permission in view.get_permissions()))

    def test_admin_can_promote_user_by_username(self):
        admin = User.objects.create_user(
            username="admin_promote",
            password="pass1234567",
            role=User.Role.ADMIN,
            phone_number="+2348000000002",
        )
        target = User.objects.create_user(
            username="customer_promote",
            password="pass1234567",
            role=User.Role.CUSTOMER,
            phone_number="+2348000000003",
        )

        request = self.factory.post("/auth/promote-admin/", {"username": "customer_promote"})
        request.user = admin

        response = PromoteAdminView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        target.refresh_from_db()
        self.assertEqual(target.role, User.Role.ADMIN)
