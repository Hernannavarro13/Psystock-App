from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import Portfolio, Position, Transaction, TradingPerformance
from .serializers import (
    PortfolioSerializer, PositionSerializer, 
    TransactionSerializer, TradingPerformanceSerializer,
    TradeSerializer
)
from stocks.models import Stock
from stocks.utils import get_current_price

class PortfolioViewSet(viewsets.ModelViewSet):
    """API endpoint for user portfolio"""
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create new portfolio or return existing one"""
        if hasattr(request.user, 'portfolio'):
            serializer = self.get_serializer(request.user.portfolio)
            return Response(serializer.data)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        
        # Create trading performance tracker
        portfolio = serializer.instance
        TradingPerformance.objects.create(portfolio=portfolio)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def positions(self, request, pk=None):
        """Get all positions in portfolio"""
        portfolio = self.get_object()
        positions = portfolio.positions.all()
        serializer = PositionSerializer(positions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions in portfolio"""
        portfolio = self.get_object()
        transactions = portfolio.transactions.all().order_by('-timestamp')
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get portfolio performance metrics"""
        portfolio = self.get_object()
        try:
            performance = portfolio.performance
            performance.update_metrics()
            serializer = TradingPerformanceSerializer(performance)
            return Response(serializer.data)
        except TradingPerformance.DoesNotExist:
            return Response(
                {"detail": "Performance metrics not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def trade(self, request, pk=None):
        """Execute a trade (buy/sell)"""
        portfolio = self.get_object()
        serializer = TradeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        trade_data = serializer.validated_data
        ticker = trade_data['symbol']
        trade_type = trade_data['trade_type']
        quantity = Decimal(str(trade_data['quantity']))
        
        try:
            # Get or create stock
            stock, _ = Stock.objects.get_or_create(symbol=ticker)
            
            # Get current price
            current_price = get_current_price(ticker)
            if current_price is None:
                return Response(
                    {"detail": f"Could not get current price for {ticker}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Execute trade
            with transaction.atomic():
                if trade_type == 'BUY':
                    result = self._execute_buy(portfolio, stock, quantity, current_price)
                else:  # SELL
                    result = self._execute_sell(portfolio, stock, quantity, current_price)
                
                if 'error' in result:
                    return Response({"detail": result['error']}, status=status.HTTP_400_BAD_REQUEST)
                
                # Update portfolio value
                portfolio.calculate_total_value()
                
                # Update performance metrics
                if hasattr(portfolio, 'performance'):
                    portfolio.performance.update_metrics()
                
                return Response(result)
                
        except Exception as e:
            return Response(
                {"detail": f"Error executing trade: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _execute_buy(self, portfolio, stock, quantity, price):
        """Execute buy order"""
        total_cost = quantity * price
        
        # Check if user has enough cash
        if portfolio.cash_balance < total_cost:
            return {"error": "Insufficient funds"}
        
        # Create transaction record
        transaction = Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            transaction_type=Transaction.BUY,
            quantity=quantity,
            price=price,
            total_amount=total_cost
        )
        
        # Update portfolio cash balance
        portfolio.cash_balance -= total_cost
        portfolio.save()
        
        # Update or create position
        try:
            position = Position.objects.get(portfolio=portfolio, stock=stock)
            # Update existing position with new average price
            total_shares = position.quantity + quantity
            position.average_buy_price = (
                (position.quantity * position.average_buy_price + quantity * price) / total_shares
            )
            position.quantity = total_shares
            position.current_price = price
            position.current_value = position.quantity * price
            position.unrealized_pnl = position.current_value - (position.quantity * position.average_buy_price)
            position.save()
        except Position.DoesNotExist:
            # Create new position
            position = Position.objects.create(
                portfolio=portfolio,
                stock=stock,
                quantity=quantity,
                average_buy_price=price,
                current_price=price,
                current_value=quantity * price,
                unrealized_pnl=0
            )
        
        return {
            "transaction": TransactionSerializer(transaction).data,
            "position": PositionSerializer(position).data,
            "portfolio": PortfolioSerializer(portfolio).data
        }
    
    def _execute_sell(self, portfolio, stock, quantity, price):
        """Execute sell order"""
        try:
            position = Position.objects.get(portfolio=portfolio, stock=stock)
        except Position.DoesNotExist:
            return {"error": f"No position found for {stock.symbol}"}
        
        # Check if user has enough shares
        if position.quantity < quantity:
            return {"error": f"Insufficient shares. You have {position.quantity} but trying to sell {quantity}"}
        
        total_sale = quantity * price
        
        # Calculate realized P&L for this sale
        realized_pnl = (price - position.average_buy_price) * quantity
        
        # Create transaction record
        transaction = Transaction.objects.create(
            portfolio=portfolio,
            stock=stock,
            transaction_type=Transaction.SELL,
            quantity=quantity,
            price=price,
            total_amount=total_sale
        )
        
        # Update portfolio cash balance
        portfolio.cash_balance += total_sale
        portfolio.save()
        
        # Update position
        position.quantity -= quantity
        position.current_price = price
        position.current_value = position.quantity * price
        position.unrealized_pnl = position.current_value - (position.quantity * position.average_buy_price)
        
        # Update performance metrics
        try:
            performance = portfolio.performance
            performance.total_realized_pnl += realized_pnl
            
            # Update win/loss counters
            if realized_pnl > 0:
                performance.winning_trades += 1
            elif realized_pnl < 0:
                performance.losing_trades += 1
                
            performance.save()
        except TradingPerformance.DoesNotExist:
            pass
        
        # Delete position if no shares left, otherwise save updated position
        if position.quantity == 0:
            position.delete()
            position_data = None
        else:
            position.save()
            position_data = PositionSerializer(position).data
        
        return {
            "transaction": TransactionSerializer(transaction).data,
            "position": position_data,
            "portfolio": PortfolioSerializer(portfolio).data,
            "realized_pnl": float(realized_pnl)
        }

class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for positions"""
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Position.objects.filter(portfolio__user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_price(self, request, pk=None):
        """Update current price for a position"""
        position = self.get_object()
        position.update_current_value()
        return Response(PositionSerializer(position).data)

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for transactions"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(portfolio__user=self.request.user).order_by('-timestamp')