# stock_predictor_backend/trading/services.py
import yfinance as yf
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.db.models import F
from .models import Portfolio, Position, Transaction, Order

class TradingService:
    """Service class to handle trading operations."""
    
    @staticmethod
    def get_current_price(ticker):
        """Get the current price for a stock ticker."""
        try:
            stock = yf.Ticker(ticker)
            todays_data = stock.history(period='1d')
            if not todays_data.empty:
                return Decimal(str(todays_data['Close'].iloc[-1]))
            return None
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return None
    
    @staticmethod
    def update_position_prices(portfolio):
        """Update the current prices for all positions in a portfolio."""
        for position in portfolio.positions.all():
            current_price = TradingService.get_current_price(position.ticker)
            if current_price:
                position.current_price = current_price
                position.save()
    
    @staticmethod
    @transaction.atomic
    def execute_market_order(user, ticker, side, quantity):
        """Execute a market order for buying or selling stocks."""
        try:
            # Get or create portfolio
            portfolio, created = Portfolio.objects.get_or_create(user=user)
            
            # Get current price
            current_price = TradingService.get_current_price(ticker)
            if not current_price:
                return {
                    'success': False,
                    'message': f"Could not get current price for {ticker}"
                }
            
            # Calculate total amount
            total_amount = current_price * Decimal(quantity)
            
            # Create transaction record
            transaction = Transaction(
                portfolio=portfolio,
                ticker=ticker,
                transaction_type=side,
                quantity=quantity,
                price=current_price,
                total_amount=total_amount,
                status=Transaction.PENDING
            )
            
            # Handle buy order
            if side == 'BUY':
                # Check if user has enough cash
                if portfolio.cash_balance < total_amount:
                    transaction.status = Transaction.FAILED
                    transaction.notes = "Insufficient funds"
                    transaction.save()
                    return {
                        'success': False,
                        'message': "Insufficient funds to complete transaction"
                    }
                
                # Update portfolio cash balance
                portfolio.cash_balance -= total_amount
                portfolio.save()
                
                # Update or create position
                position, created = Position.objects.get_or_create(
                    portfolio=portfolio,
                    ticker=ticker,
                    defaults={
                        'quantity': 0,
                        'average_buy_price': 0,
                        'current_price': current_price
                    }
                )
                
                # Update position
                if position.quantity > 0:
                    # Calculate new average buy price
                    total_value = (position.quantity * position.average_buy_price) + total_amount
                    position.quantity += quantity
                    position.average_buy_price = total_value / position.quantity
                else:
                    position.quantity = quantity
                    position.average_buy_price = current_price
                
                position.current_price = current_price
                position.save()
                
            # Handle sell order
            elif side == 'SELL':
                # Check if user has the position and enough shares
                try:
                    position = Position.objects.get(portfolio=portfolio, ticker=ticker)
                    if position.quantity < quantity:
                        transaction.status = Transaction.FAILED
                        transaction.notes = "Insufficient shares"
                        transaction.save()
                        return {
                            'success': False,
                            'message': f"Insufficient shares. You have {position.quantity} shares of {ticker}"
                        }
                except Position.DoesNotExist:
                    transaction.status = Transaction.FAILED
                    transaction.notes = "Position does not exist"
                    transaction.save()
                    return {
                        'success': False,
                        'message': f"You don't own any shares of {ticker}"
                    }
                
                # Update portfolio cash balance
                portfolio.cash_balance += total_amount
                portfolio.save()
                
                # Update position
                position.quantity -= quantity
                position.current_price = current_price
                
                # If all shares are sold, delete the position
                if position.quantity == 0:
                    position.delete()
                else:
                    position.save()
            
            # Mark transaction as executed
            transaction.status = Transaction.EXECUTED
            transaction.executed_at = timezone.now()
            transaction.save()
            
            return {
                'success': True,
                'message': f"Successfully {side.lower()}ed {quantity} shares of {ticker} at ${current_price}",
                'transaction': transaction
            }
            
        except Exception as e:
            print(f"Error executing {side} order for {ticker}: {e}")
            return {
                'success': False,
                'message': f"Error executing order: {str(e)}"
            }
    
    @staticmethod
    @transaction.atomic
    def place_limit_order(user, ticker, side, quantity, limit_price, expiration_days=30):
        """Place a limit order for buying or selling stocks."""
        try:
            # Get or create portfolio
            portfolio, created = Portfolio.objects.get_or_create(user=user)
            
            # Get current price for reference
            current_price = TradingService.get_current_price(ticker)
            if not current_price:
                return {
                    'success': False,
                    'message': f"Could not get current price for {ticker}"
                }
            
            # Convert limit price to Decimal
            limit_price = Decimal(str(limit_price))
            
            # Validate the order
            if side == 'BUY':
                # Check if user has enough cash
                total_amount = limit_price * Decimal(quantity)
                if portfolio.cash_balance < total_amount:
                    return {
                        'success': False,
                        'message': "Insufficient funds to place this limit order"
                    }
                
                # Reserve the funds
                portfolio.cash_balance -= total_amount
                portfolio.save()
                
            elif side == 'SELL':
                # Check if user has the position and enough shares
                try:
                    position = Position.objects.get(portfolio=portfolio, ticker=ticker)
                    if position.quantity < quantity:
                        return {
                            'success': False,
                            'message': f"Insufficient shares. You have {position.quantity} shares of {ticker}"
                        }
                except Position.DoesNotExist:
                    return {
                        'success': False,
                        'message': f"You don't own any shares of {ticker}"
                    }
            
            # Calculate expiration date
            expiration_date = timezone.now() + timezone.timedelta(days=expiration_days)
            
            # Create order
            order = Order.objects.create(
                portfolio=portfolio,
                ticker=ticker,
                side=side,
                order_type=Order.LIMIT,
                quantity=quantity,
                limit_price=limit_price,
                status=Order.OPEN,
                expiration_date=expiration_date
            )
            
            return {
                'success': True,
                'message': f"Successfully placed {side.lower()} limit order for {quantity} shares of {ticker} at ${limit_price}",
                'order': order
            }
            
        except Exception as e:
            print(f"Error placing limit order for {ticker}: {e}")
            return {
                'success': False,
                'message': f"Error placing limit order: {str(e)}"
            }
    
    @staticmethod
    @transaction.atomic
    def cancel_limit_order(order_id, user):
        """Cancel a limit order."""
        try:
            # Get the order
            order = Order.objects.select_related('portfolio').get(id=order_id)
            
            # Check if the order belongs to the user
            if order.portfolio.user != user:
                return {
                    'success': False,
                    'message': "You don't have permission to cancel this order"
                }
            
            # Check if the order is open
            if order.status != Order.OPEN:
                return {
                    'success': False,
                    'message': f"Cannot cancel order with status {order.status}"
                }
            
            # For buy orders, return the reserved funds
            if order.side == Order.BUY:
                total_amount = order.limit_price * Decimal(order.quantity)
                order.portfolio.cash_balance += total_amount
                order.portfolio.save()
            
            # Mark the order as cancelled
            order.status = Order.CANCELLED
            order.save()
            
            return {
                'success': True,
                'message': f"Order cancelled successfully",
                'order': order
            }
            
        except Order.DoesNotExist:
            return {
                'success': False,
                'message': "Order not found"
            }
        except Exception as e:
            print(f"Error cancelling order {order_id}: {e}")
            return {
                'success': False,
                'message': f"Error cancelling order: {str(e)}"
            }
    
    @staticmethod
    def process_limit_orders():
        """Process all open limit orders."""
        # Get all open orders
        open_orders = Order.objects.filter(
            status=Order.OPEN,
            expiration_date__gt=timezone.now()
        ).select_related('portfolio')
        
        for order in open_orders:
            # Get current price
            current_price = TradingService.get_current_price(order.ticker)
            if not current_price:
                continue
            
            # Check if order can be executed
            can_execute = False
            
            if order.side == Order.BUY and current_price <= order.limit_price:
                can_execute = True
            elif order.side == Order.SELL and current_price >= order.limit_price:
                can_execute = True
            
            if can_execute:
                # Execute the order
                result = TradingService.execute_limit_order(order, current_price)
                
                # If execution failed, log the error
                if not result['success']:
                    print(f"Failed to execute limit order {order.id}: {result['message']}")
    
    @staticmethod
    @transaction.atomic
    def execute_limit_order(order, current_price):
        """Execute a limit order that has met its price condition."""
        try:
            portfolio = order.portfolio
            
            # Create transaction record
            transaction = Transaction(
                portfolio=portfolio,
                ticker=order.ticker,
                transaction_type=order.side,
                quantity=order.quantity,
                price=current_price,
                total_amount=current_price * order.quantity,
                status=Transaction.PENDING
            )
            
            # Handle buy order
            if order.side == Order.BUY:
                # Calculate price difference (refund if current price is lower than limit price)
                price_diff = order.limit_price - current_price
                refund_amount = price_diff * Decimal(order.quantity)
                
                if refund_amount > 0:
                    portfolio.cash_balance += refund_amount
                    portfolio.save()
                
                # Update or create position
                position, created = Position.objects.get_or_create(
                    portfolio=portfolio,
                    ticker=order.ticker,
                    defaults={
                        'quantity': 0,
                        'average_buy_price': 0,
                        'current_price': current_price
                    }
                )
                
                # Update position
                if position.quantity > 0:
                    # Calculate new average buy price
                    total_value = (position.quantity * position.average_buy_price) + (current_price * order.quantity)
                    position.quantity += order.quantity
                    position.average_buy_price = total_value / position.quantity
                else:
                    position.quantity = order.quantity
                    position.average_buy_price = current_price
                
                position.current_price = current_price
                position.save()
                
            # Handle sell order
            elif order.side == Order.SELL:
                # Update portfolio cash balance
                portfolio.cash_balance += current_price * order.quantity
                portfolio.save()
                
                # Update position
                position = Position.objects.get(portfolio=portfolio, ticker=order.ticker)
                position.quantity -= order.quantity
                position.current_price = current_price
                
                # If all shares are sold, delete the position
                if position.quantity == 0:
                    position.delete()
                else:
                    position.save()
            
            # Mark transaction as executed
            transaction.status = Transaction.EXECUTED
            transaction.executed_at = timezone.now()
            transaction.save()
            
            # Link transaction to order
            order.transaction = transaction
            order.status = Order.FILLED
            order.save()
            
            return {
                'success': True,
                'message': f"Successfully executed limit order for {order.quantity} shares of {order.ticker} at ${current_price}",
                'transaction': transaction
            }
            
        except Exception as e:
            print(f"Error executing limit order {order.id}: {e}")
            return {
                'success': False,
                'message': f"Error executing limit order: {str(e)}"
            }
            
    @staticmethod
    def expire_old_orders():
        """Mark expired orders as expired."""
        expired_count = Order.objects.filter(
            status=Order.OPEN,
            expiration_date__lte=timezone.now()
        ).update(status=Order.EXPIRED)
        
        # Return funds for expired buy orders
        expired_buy_orders = Order.objects.filter(
            status=Order.EXPIRED,
            side=Order.BUY
        ).select_related('portfolio')
        
        for order in expired_buy_orders:
            total_amount = order.limit_price * order.quantity
            order.portfolio.cash_balance += total_amount
            order.portfolio.save()
        
        return expired_count