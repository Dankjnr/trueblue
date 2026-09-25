from rest_framework.routers import DefaultRouter

from .views import BlocklistEntryViewSet, CleanerViewSet, IncidentViewSet

router = DefaultRouter()
router.register("blocklist", BlocklistEntryViewSet, basename="blocklist-entry")
router.register("incidents", IncidentViewSet, basename="incident")
router.register("", CleanerViewSet, basename="cleaner")

urlpatterns = router.urls
