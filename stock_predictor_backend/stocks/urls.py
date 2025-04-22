from django.urls import path
from .views import StockViewSet, StockHistoryAPIView

urlpatterns = [
    path('search/', StockViewSet.as_view({'get': 'search'}), name='stock-search'),
    path('<str:symbol>/', StockViewSet.as_view({'get': 'retrieve'}), name='stock-detail'),
    path('<str:symbol>/history/', StockHistoryAPIView.as_view(), name='stock-history'),
]