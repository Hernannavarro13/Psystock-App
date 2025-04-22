from django.urls import path
from .views import PortfolioViewSet, PositionViewSet, TradeViewSet

urlpatterns = [
    path('portfolio/', PortfolioViewSet.as_view({'get': 'list'}), name='portfolio'),
    path('positions/', PositionViewSet.as_view({'get': 'list'}), name='positions'),
    path('trades/', TradeViewSet.as_view({'get': 'list', 'post': 'create'}), name='trades'),
    path('trades/<int:pk>/', TradeViewSet.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    }), name='trade-detail'),
]