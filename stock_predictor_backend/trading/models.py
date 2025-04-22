# stock_predictor_backend/trading/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Portfolio(models.Model):
    """Model representing a user's portfolio for paper trading."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='portfolio')
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=settings.INITIAL_BALANCE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_stock_value(self):
        """Calculate the total value of all stocks in the portfolio."""
        return sum(position.current_value for position in self.positions.all())
    
    @property
    def total_value(self):
        """Calculate the total portfolio value (cash + stocks)."""
        return self.cash_balance + self.total_stock_value
    
    def __str__(self):
        return f"{self.user.username}'s Portfolio"

class Position(models.Model):
    """Model representing a stock position in a portfolio."""
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='positions')
    ticker = models.CharField(max_length=10)
    quantity = models.IntegerField(default=0)
    average_buy_price = models.DecimalField(max_digits=15, decimal_places=2)
    current_price = models.DecimalField(max_digits=15, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)
    
    @property
    def current_value(self):
        """Calculate the current value of this position."""
        return self.quantity * self.current_price
    
    @property
    def profit_loss(self):
        """Calculate the profit/loss for this position."""
        return self.current_value - (self.quantity * self.average_buy_price)
    
    @property
    def profit_loss_percentage(self):
        """Calculate the profit/loss percentage for this position."""
        if self.quantity == 0 or self.average_buy_price == 0:
            return 0
        return ((self.current_price - self.average_buy_price) / self.average_buy_price) * 100
    
    def __str__(self):
        return f"{self.ticker}: {self.quantity} shares"
    
    class Meta:
        unique_together = ('portfolio', 'ticker')

class Transaction(models.Model):
    """Model representing a trading transaction."""
    BUY = 'BUY'
    SELL = 'SELL'
    
    TRANSACTION_TYPES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]
    
    PENDING = 'PENDING'
    EXECUTED = 'EXECUTED'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (EXECUTED, 'Executed'),
        (CANCELLED, 'Cancelled'),
        (FAILED, 'Failed'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    ticker = models.CharField(max_length=10)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    executed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Set the total amount
        self.total_amount = self.quantity * self.price
        
        # If transaction is being set to executed and doesn't have an executed timestamp
        if self.status == self.EXECUTED and not self.executed_at:
            self.executed_at = timezone.now()
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_type} {self.quantity} {self.ticker} @ {self.price}"

class Order(models.Model):
    """Model representing a stock order."""
    MARKET = 'MARKET'
    LIMIT = 'LIMIT'
    
    ORDER_TYPES = [
        (MARKET, 'Market Order'),
        (LIMIT, 'Limit Order'),
    ]
    
    BUY = 'BUY'
    SELL = 'SELL'
    
    ORDER_SIDES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]
    
    OPEN = 'OPEN'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'
    EXPIRED = 'EXPIRED'
    
    STATUS_CHOICES = [
        (OPEN, 'Open'),
        (FILLED, 'Filled'),
        (CANCELLED, 'Cancelled'),
        (EXPIRED, 'Expired'),
    ]
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='orders')
    ticker = models.CharField(max_length=10)
    side = models.CharField(max_length=4, choices=ORDER_SIDES)
    order_type = models.CharField(max_length=10, choices=ORDER_TYPES)
    quantity = models.IntegerField()
    limit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=OPEN)
    transaction = models.OneToOneField(
        Transaction, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='order'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        if self.order_type == self.LIMIT:
            return f"{self.side} {self.quantity} {self.ticker} @ {self.limit_price} (LIMIT)"
        return f"{self.side} {self.quantity} {self.ticker} (MARKET)"