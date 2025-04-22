from django.urls import path
from .views import AuthViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', AuthViewSet, basename='auth')

urlpatterns = router.urls
