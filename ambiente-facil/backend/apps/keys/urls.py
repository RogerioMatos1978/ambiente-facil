from rest_framework.routers import DefaultRouter

from .views import ChaveViewSet

router = DefaultRouter()
router.register("guarita/chaves", ChaveViewSet, basename="chave")

urlpatterns = router.urls
