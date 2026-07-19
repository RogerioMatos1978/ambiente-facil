from rest_framework.routers import DefaultRouter

from .views import AmbienteViewSet

router = DefaultRouter()
router.register("environments", AmbienteViewSet, basename="ambiente")

urlpatterns = router.urls
