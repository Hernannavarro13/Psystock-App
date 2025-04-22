from rest_framework import serializers
from .models import Portfolio, Position, Transaction, TradingPerformance
from stocks.serializers import StockSerializer

class PositionSerializer(serializers.ModelSerializer):
    """Serializer for stock positions"""
    stock = StockSerializer(read_only=True)
    profit_loss_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'stock', 'quantity', 'average_buy_price', 
            'current_price', 'current_value', 'unrealized_pnl',
            'profit_loss_percentage', 'created_at', 'updated_at'
        ]
    
    def get_profit_loss_percentage(self, obj):
        """Calculate profit/loss percentage"""
        if obj.average_buy_price > 0:
            return ((obj.current_price - obj.average_buy_price) / obj.average_buy_price) * 100
        return 0

class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for trading transactions"""
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)
    stock_name = serializers.CharField(source='stock.name', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_type', 'stock_symbol', 'stock_name',
            'quantity', 'price', 'total_amount', 'timestamp'
        ]

class TradingPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for trading performance metrics"""
    
    class Meta:
        model = TradingPerformance
        fields = [
            'total_realized_pnl', 'total_unrealized_pnl', 
            'total_return_percentage', 'winning_trades',
            'losing_trades', 'win_loss_ratio', 'last_updated'
        ]

class PortfolioSummarySerializer(serializers.Serializer):
    """Serializer for portfolio summary"""
    cash_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    positions_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    positions_count = serializers.IntegerField()
    unrealized_pnl = serializers.DecimalField(max_digits=15, decimal_places=2)
    daily_change = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    daily_change_percentage = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)

class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for user portfolio"""
    username = serializers.CharField(source='user.username', read_only=True)
    positions_count = serializers.SerializerMethodField()
    positions_value = serializers.SerializerMethodField()
    top_positions = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'username', 'cash_balance', 'total_value',
            'positions_count', 'positions_value', 'top_positions',
            'created_at', 'updated_at'
        ]
    
    def get_positions_count(self, obj):
        return obj.positions.count()
    
    def get_positions_value(self, obj):
        return obj.total_value - obj.cash_balance
    
    def get_top_positions(self, obj):
        """Get top 5 positions by value"""
        top_positions = obj.positions.all().order_by('-current_value')[:5]
        return PositionSerializer(top_positions, many=True).data

class TradeSerializer(serializers.Serializer):
    """Serializer for executing trades"""
    symbol = serializers.CharField(max_length=10)
    trade_type = serializers.ChoiceField(choices=['BUY', 'SELL'])
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4)
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value