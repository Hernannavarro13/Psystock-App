from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import StockPrediction
from .serializers import StockPredictionSerializer
from stocks.models import Stock
from .services import predict_stock_price
import datetime

class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockPredictionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return StockPrediction.objects.all()
    
    @action(detail=False, methods=['get'])
    def predict(self, request):
        symbol = request.query_params.get('symbol')
        timeframe = request.query_params.get('timeframe', '1W')
        
        if not symbol:
            return Response({"error": "Stock symbol is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stock = Stock.objects.get(symbol=symbol)
        except Stock.DoesNotExist:
            return Response({"error": f"Stock with symbol {symbol} not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if we already have a recent prediction
        today = datetime.date.today()
        try:
            prediction = StockPrediction.objects.filter(
                stock=stock,
                timeframe=timeframe,
                created_at__date=today
            ).latest('created_at')
            serializer = self.get_serializer(prediction)
            return Response(serializer.data)
        except StockPrediction.DoesNotExist:
            # Generate a new prediction
            prediction_data = predict_stock_price(stock.symbol, timeframe)
            
            if prediction_data:
                prediction = StockPrediction.objects.create(
                    stock=stock,
                    prediction_date=prediction_data['date'],
                    predicted_price=prediction_data['price'],
                    confidence_level=prediction_data['confidence'],
                    timeframe=timeframe
                )
                serializer = self.get_serializer(prediction)
                return Response(serializer.data)
            else:
                return Response({"error": "Failed to generate prediction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)