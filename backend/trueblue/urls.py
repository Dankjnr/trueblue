from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/customers/", include("customers.urls")),
    path("api/cleaners/", include("cleaners.urls")),
    path("api/jobs/", include("jobs.urls")),
    path("api/audit-log/", include("audit.urls")),
]
