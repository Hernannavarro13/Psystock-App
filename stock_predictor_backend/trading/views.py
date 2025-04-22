from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from .models import Portfolio, Position, Trade
from stocks.models import Stock
from .serializers import PortfolioSerializer, PositionSerializer, TradeSerializer

class PortfolioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

class PositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Position.objects.filter(portfolio__user=self.request.user)

class TradeViewSet(viewsets.ModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Trade.objects.filter(portfolio__user=self.request.user)
    
    @transaction.atomic
    def perform_create(self, serializer):
        # Get user's portfolio
        portfolio, created = Portfolio.objects.get_or_create(user=self.request.user)
        
        # Get trade details
        stock = serializer.validated_data['stock']
        trade_type = serializer.validated_data['trade_type']
        quantity = serializer.validated_data['quantity']
        price = serializer.validated_data['price']
        total_amount = price * quantity
        
        # Check if user has enough balance for buying
        if trade_type == 'BUY' and portfolio.current_balance < total_amount:
            raise serializers.ValidationError({"error": "Insufficient funds for this trade"})
        
        # Update portfolio balance
        if trade_type == 'BUY':
            portfolio.current_balance -= total_amount
        else:  # SELL
            portfolio.current_balance += total_amount
        
        portfolio.save()
        
        # Create or update position
        position = None
        if trade_type == 'BUY':
            position, created = Position.objects.get_or_create(
                portfolio=portfolio,
                stock=stock,
                position_type='LONG',
                defaults={'quantity': 0, 'entry_price': price}
            )
            
            # Update position
            if not created:
                # Calculate new average entry price
                total_value = (position.quantity * position.entry_price) + total_amount
                new_quantity = position.quantity + quantity
                position.entry_price = total_value / new_quantity if new_quantity > 0 else price
                position.quantity = new_quantity
                position.save()
            else:
                position.quantity = quantity
                position.save()
        
        else:  # SELL
            try:
                position = Position.objects.get(portfolio=portfolio, stock=stock, position_type='LONG')
                
                # Check if user has enough shares to sell
                if position.quantity < quantity:
                    raise serializers.ValidationError({"error": "Not enough shares to sell"})
                
                # Update position
                position.quantity -= quantity
                position.save()
                
                # If all shares are sold, delete the position
                if position.quantity == 0:
                    position.delete()
                    position = None
                    
            except Position.DoesNotExist:
                raise serializers.ValidationError({"error": "No shares to sell"})
        
        # Save the trade
        serializer.save(portfolio=portfolio, total_amount=total_amount, position=position)