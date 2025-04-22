from django.urls import path
from .views import PredictionViewSet

urlpatterns = [
    path('predict/', PredictionViewSet.as_view({'get': 'predict'}), name='stock-prediction'),
]