from django.db import models
from stocks.models import Stock

class StockPrediction(models.Model):
    TIMEFRAME_CHOICES = [
        ('1D', '1 Day'),
        ('1W', '1 Week'),
        ('1M', '1 Month'),
        ('3M', '3 Months'),
    ]
    
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    prediction_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_level = models.DecimalField(max_digits=5, decimal_places=2)  # 0-100%
    timeframe = models.CharField(max_length=2, choices=TIMEFRAME_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('stock', 'prediction_date', 'timeframe')
    
    def __str__(self):
        return f"{self.stock.symbol} - {self.prediction_date} ({self.timeframe})"