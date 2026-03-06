"""
Trading Agents for Bybit USDT Perpetual Futures
Handles order execution and position management
"""

import logging
import pandas as pd
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    ta = None
    HAS_PANDAS_TA = False
import datetime
import asyncio
from typing import Optional, Dict, Any, Tuple

from bybit_client import BybitClient

logger = logging.getLogger(__name__)


class OrderExecutionAgent:
    """
    Handles order sizing, placement, and retrieval for Bybit perpetual futures.
    """
    
    def __init__(self, bybit_client: BybitClient, config: dict):
        """
        Initialize the order execution agent.
        
        Args:
            bybit_client: Initialized BybitClient instance
            config: Configuration dictionary
        """
        self.client = bybit_client
        self.config = config
        self.trading_config = config.get('trading', {})
        self.flags = config.get('trading_flags', {})
        
        # Default settings
        self.default_leverage = self.trading_config.get('default_leverage', 5)
        self.max_leverage = self.trading_config.get('max_leverage', 20)
        self.risk_per_trade = self.trading_config.get('risk_per_trade_percent', 2.0)
        
    async def place_trade(
        self, 
        direction: str, 
        symbol: Optional[str] = None,
        leverage: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Place a perpetual futures trade.
        
        Args:
            direction: "BUY" (long) or "SELL" (short)
            symbol: Trading pair symbol (defaults to config default)
            leverage: Leverage to use (defaults to config default)
            
        Returns:
            Trade details dictionary or None if failed
        """
        symbol = symbol or self.trading_config.get('default_symbol', 'BTCUSDT')
        leverage = leverage or self.default_leverage
        leverage = min(leverage, self.max_leverage)
        
        try:
            # Calculate position size based on risk
            qty, entry_price = await self._calculate_position_size(symbol, direction)
            
            if qty <= 0:
                logger.error(f"Invalid position size calculated for {symbol}")
                return None
            
            # Calculate stop loss and take profit
            sl_percent = self.trading_config.get('stop_loss_percent', 2.0)
            tp_percent = self.trading_config.get('take_profit_percent', 4.0)
            
            if direction == "BUY":
                stop_loss = entry_price * (1 - sl_percent / 100)
                take_profit = entry_price * (1 + tp_percent / 100)
            else:
                stop_loss = entry_price * (1 + sl_percent / 100)
                take_profit = entry_price * (1 - tp_percent / 100)
            
            # Map direction to Bybit side
            side = "Buy" if direction == "BUY" else "Sell"
            
            logger.info(f"Placing {direction} order: {qty} {symbol} @ ~{entry_price:.2f}")
            logger.info(f"  Leverage: {leverage}x | SL: {stop_loss:.2f} | TP: {take_profit:.2f}")
            
            # Place the order
            result = await self.client.place_perpetual_order(
                symbol=symbol,
                side=side,
                qty=qty,
                leverage=leverage,
                order_type="Market",
                stop_loss=stop_loss,
                take_profit=take_profit,
            )
            
            if result.get('ok'):
                trade_details = {
                    'order_id': result.get('orderId'),
                    'symbol': symbol,
                    'type': direction,
                    'side': side,
                    'quantity': qty,
                    'entry_price': entry_price,
                    'leverage': leverage,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'timestamp': datetime.datetime.now().isoformat(),
                }
                
                logger.info(f"✅ Trade executed: {trade_details}")
                return trade_details
            else:
                logger.error(f"❌ Trade failed: {result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Error placing trade: {e}", exc_info=True)
            return None
    
    async def get_paper_trade_details(
        self, 
        direction: str,
        symbol: Optional[str] = None,
        leverage: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get simulated trade details for paper trading.
        
        Args:
            direction: "BUY" (long) or "SELL" (short)
            symbol: Trading pair symbol
            leverage: Leverage to use
            
        Returns:
            Simulated trade details dictionary
        """
        symbol = symbol or self.trading_config.get('default_symbol', 'BTCUSDT')
        leverage = leverage or self.default_leverage
        
        try:
            # Get current price
            current_price = await self.client.get_current_price(symbol)
            if current_price <= 0:
                logger.error(f"Could not get price for {symbol}")
                return None
            
            # Calculate position size
            qty, _ = await self._calculate_position_size(symbol, direction)
            if qty <= 0:
                return None
            
            # Calculate SL/TP
            sl_percent = self.trading_config.get('stop_loss_percent', 2.0)
            tp_percent = self.trading_config.get('take_profit_percent', 4.0)
            
            if direction == "BUY":
                stop_loss = current_price * (1 - sl_percent / 100)
                take_profit = current_price * (1 + tp_percent / 100)
            else:
                stop_loss = current_price * (1 + sl_percent / 100)
                take_profit = current_price * (1 - tp_percent / 100)
            
            trade_details = {
                'order_id': f"PAPER_{int(datetime.datetime.now().timestamp())}",
                'symbol': symbol,
                'type': direction,
                'side': "Buy" if direction == "BUY" else "Sell",
                'quantity': qty,
                'entry_price': current_price,
                'leverage': leverage,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'timestamp': datetime.datetime.now().isoformat(),
                'paper_trade': True,
            }
            
            logger.info(f"[Paper Trade] {direction} {qty} {symbol} @ {current_price:.2f}")
            return trade_details
            
        except Exception as e:
            logger.error(f"Error getting paper trade details: {e}")
            return None
    
    async def _calculate_position_size(
        self, 
        symbol: str, 
        direction: str
    ) -> Tuple[float, float]:
        """
        Calculate position size based on risk management rules.
        
        Args:
            symbol: Trading pair symbol
            direction: Trade direction
            
        Returns:
            Tuple of (quantity, current_price)
        """
        try:
            # Get wallet balance
            balance = await self.client.get_wallet_balance("USDT")
            available_balance = balance.get('available', 0)
            wallet_balance = balance.get('walletBalance', 0)
            margin_balance = balance.get('marginBalance', 0)
            total_equity = balance.get('totalEquity', 0)
            
            logger.info(f"Wallet balance check: available={available_balance}, wallet={wallet_balance}, margin={margin_balance}, equity={total_equity}")
            
            # For Unified Trading Account, use marginBalance or totalEquity when coin-specific balance is 0
            if available_balance <= 0:
                # Priority: marginBalance > totalEquity > walletBalance
                if margin_balance > 0:
                    logger.info(f"Using margin balance ({margin_balance}) for position sizing")
                    available_balance = margin_balance
                elif total_equity > 0:
                    logger.info(f"Using total equity ({total_equity}) for position sizing")
                    available_balance = total_equity
                elif wallet_balance > 0:
                    logger.info(f"Using wallet balance ({wallet_balance}) for position sizing")
                    available_balance = wallet_balance
                else:
                    logger.warning(f"No available balance for trading. Balance response: {balance}")
                    return 0, 0
            
            # Get current price
            current_price = await self.client.get_current_price(symbol)
            if current_price <= 0:
                return 0, 0
            
            # Get instrument info for min qty
            inst_info = await self.client.get_instrument_info(symbol)
            min_qty = inst_info.get('minOrderQty', 0.001)
            qty_step = inst_info.get('qtyStep', 0.001)
            
            # Calculate risk amount
            risk_amount = available_balance * (self.risk_per_trade / 100)
            
            # Calculate stop loss distance
            sl_percent = self.trading_config.get('stop_loss_percent', 2.0)
            sl_distance = current_price * (sl_percent / 100)
            
            # Position size = risk amount / stop loss distance
            # This gives us the quantity where if SL is hit, we lose risk_amount
            qty = risk_amount / sl_distance
            
            # Apply max position limit
            max_position_percent = self.trading_config.get('max_position_percent', 10.0)
            max_position_value = available_balance * (max_position_percent / 100)
            max_qty = max_position_value / current_price
            
            qty = min(qty, max_qty)
            
            # Round to valid step
            qty = round(qty / qty_step) * qty_step
            qty = max(qty, min_qty)
            
            logger.info(f"Position size: {qty} {symbol} (risk: ${risk_amount:.2f})")
            return qty, current_price
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0, 0


class PositionManagementAgent:
    """
    Monitors active trades and manages exits for Bybit perpetual futures.
    """
    
    def __init__(self, bybit_client: BybitClient, config: dict):
        """
        Initialize the position management agent.
        
        Args:
            bybit_client: Initialized BybitClient instance
            config: Configuration dictionary
        """
        self.client = bybit_client
        self.config = config
        self.active_trade: Optional[Dict[str, Any]] = None
        self.tsl_config = config.get('trailing_stop_loss', {})
        
    def start_trade(self, trade_details: Dict[str, Any]):
        """
        Start managing a new trade.
        
        Args:
            trade_details: Dictionary with trade information
        """
        if not trade_details:
            return
        
        self.active_trade = trade_details.copy()
        self.active_trade['high_water_mark'] = trade_details.get('entry_price', 0)
        self.active_trade['low_water_mark'] = trade_details.get('entry_price', 0)
        self.active_trade['initial_stop_loss'] = trade_details.get('stop_loss', 0)
        self.active_trade['trailing_stop_loss'] = trade_details.get('stop_loss', 0)
        
        logger.info(f"Managing trade: {self.active_trade['symbol']} "
                   f"Entry: {self.active_trade['entry_price']:.2f} "
                   f"SL: {self.active_trade['initial_stop_loss']:.2f}")
    
    async def manage(
        self, 
        is_paper_trade: bool = False,
        underlying_hist_df: Optional[pd.DataFrame] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Monitor and manage the active position.
        
        Args:
            is_paper_trade: Whether this is a paper trade
            underlying_hist_df: Historical price data for indicator-based exits
            
        Returns:
            "ACTIVE" if position is still open, trade result dict if closed
        """
        if not self.active_trade:
            return None
        
        symbol = self.active_trade['symbol']
        
        try:
            # Get current price
            current_price = await self.client.get_current_price(symbol)
            if current_price <= 0:
                logger.warning(f"Could not fetch price for {symbol}")
                return "ACTIVE"
            
            entry_price = self.active_trade['entry_price']
            trade_type = self.active_trade['type']
            
            # Calculate unrealized P&L
            if trade_type == "BUY":
                pnl_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_percent = ((entry_price - current_price) / entry_price) * 100
            
            # Check hard stop loss
            hard_sl = self.active_trade['initial_stop_loss']
            if trade_type == "BUY" and current_price <= hard_sl:
                logger.info(f"HARD stop-loss hit at {current_price:.2f} (SL: {hard_sl:.2f})")
                return await self.exit_trade(is_paper_trade, "STOP_LOSS")
            elif trade_type == "SELL" and current_price >= hard_sl:
                logger.info(f"HARD stop-loss hit at {current_price:.2f} (SL: {hard_sl:.2f})")
                return await self.exit_trade(is_paper_trade, "STOP_LOSS")
            
            # Check take profit
            take_profit = self.active_trade.get('take_profit')
            if take_profit:
                if trade_type == "BUY" and current_price >= take_profit:
                    logger.info(f"Take profit hit at {current_price:.2f} (TP: {take_profit:.2f})")
                    return await self.exit_trade(is_paper_trade, "TAKE_PROFIT")
                elif trade_type == "SELL" and current_price <= take_profit:
                    logger.info(f"Take profit hit at {current_price:.2f} (TP: {take_profit:.2f})")
                    return await self.exit_trade(is_paper_trade, "TAKE_PROFIT")
            
            # Update trailing stop
            self._update_trailing_stop(current_price)
            
            # Check trailing stop
            trailing_sl = self.active_trade.get('trailing_stop_loss')
            if trailing_sl:
                if trade_type == "BUY" and current_price <= trailing_sl:
                    logger.info(f"Trailing SL hit at {current_price:.2f} (TSL: {trailing_sl:.2f})")
                    return await self.exit_trade(is_paper_trade, "TRAILING_STOP")
                elif trade_type == "SELL" and current_price >= trailing_sl:
                    logger.info(f"Trailing SL hit at {current_price:.2f} (TSL: {trailing_sl:.2f})")
                    return await self.exit_trade(is_paper_trade, "TRAILING_STOP")
            
            # Check indicator-based exit
            if self.tsl_config.get('use_indicator_exit') and underlying_hist_df is not None:
                if self._check_indicator_exit(underlying_hist_df, current_price):
                    logger.info(f"Indicator exit signal at {current_price:.2f}")
                    return await self.exit_trade(is_paper_trade, "INDICATOR_EXIT")
            
            # Log position status
            logger.debug(f"Position {symbol}: Price={current_price:.2f} P&L={pnl_percent:+.2f}%")
            
            return "ACTIVE"
            
        except Exception as e:
            logger.error(f"Error managing position: {e}")
            return "ACTIVE"
    
    def _update_trailing_stop(self, current_price: float):
        """Update trailing stop loss based on price movement."""
        if not self.active_trade:
            return
        
        trade_type = self.active_trade['type']
        trail_type = self.tsl_config.get('type', 'NONE')
        
        if trail_type == 'NONE':
            return
        
        if trade_type == "BUY":
            # Update high water mark
            self.active_trade['high_water_mark'] = max(
                self.active_trade.get('high_water_mark', 0), 
                current_price
            )
            
            if trail_type == 'PERCENTAGE':
                percentage = self.tsl_config.get('percentage', 15.0)
                new_sl = self.active_trade['high_water_mark'] * (1 - percentage / 100)
                
                # Only move SL up, never down
                current_tsl = self.active_trade.get('trailing_stop_loss', 0)
                if new_sl > current_tsl:
                    self.active_trade['trailing_stop_loss'] = new_sl
                    logger.debug(f"Trailing SL updated to {new_sl:.2f}")
                    
        else:  # SELL
            # Update low water mark
            self.active_trade['low_water_mark'] = min(
                self.active_trade.get('low_water_mark', float('inf')), 
                current_price
            )
            
            if trail_type == 'PERCENTAGE':
                percentage = self.tsl_config.get('percentage', 15.0)
                new_sl = self.active_trade['low_water_mark'] * (1 + percentage / 100)
                
                # Only move SL down, never up
                current_tsl = self.active_trade.get('trailing_stop_loss', float('inf'))
                if new_sl < current_tsl:
                    self.active_trade['trailing_stop_loss'] = new_sl
                    logger.debug(f"Trailing SL updated to {new_sl:.2f}")
    
    def _check_indicator_exit(
        self, 
        df: pd.DataFrame, 
        current_price: float
    ) -> bool:
        """Check for indicator-based exit signals."""
        if df.empty or not self.active_trade:
            return False
        
        indicator_type = self.tsl_config.get('indicator_exit_type', 'NONE')
        
        if indicator_type == 'MA':
            period = self.tsl_config.get('ma_period', 9)
            ma_col = f'ema_{period}'
            
            if ma_col not in df.columns:
                from indicators import calculate_ema
                df[ma_col] = calculate_ema(df['close'], period)
            
            if df[ma_col].isna().all():
                return False
                
            ma_value = df[ma_col].iloc[-1]
            
            if self.active_trade['type'] == 'BUY' and current_price < ma_value:
                return True
            if self.active_trade['type'] == 'SELL' and current_price > ma_value:
                return True
        
        return False
    
    async def exit_trade(
        self, 
        is_paper_trade: bool = False,
        exit_reason: str = "MANUAL"
    ) -> Optional[Dict[str, Any]]:
        """
        Exit the current active trade.
        
        Args:
            is_paper_trade: Whether this is a paper trade
            exit_reason: Reason for exit (STOP_LOSS, TAKE_PROFIT, etc.)
            
        Returns:
            Completed trade details dictionary
        """
        if not self.active_trade:
            return None
        
        trade = self.active_trade
        symbol = trade['symbol']
        
        try:
            # Get exit price
            exit_price = await self.client.get_current_price(symbol)
            if exit_price <= 0:
                exit_price = trade['entry_price']  # Fallback
            
            # Close position on exchange if not paper trading
            if not is_paper_trade and not trade.get('paper_trade'):
                result = await self.client.close_position(symbol)
                if not result.get('ok'):
                    logger.error(f"Failed to close position: {result.get('error')}")
            else:
                logger.info(f"[Paper Trade] Closing {symbol} at {exit_price:.2f}")
            
            # Calculate P&L
            qty = trade['quantity']
            entry_price = trade['entry_price']
            leverage = trade.get('leverage', 1)
            
            if trade['type'] == 'BUY':
                pnl = (exit_price - entry_price) * qty
                pnl_percent = ((exit_price - entry_price) / entry_price) * 100 * leverage
            else:
                pnl = (entry_price - exit_price) * qty
                pnl_percent = ((entry_price - exit_price) / entry_price) * 100 * leverage
            
            # Build completed trade record
            completed_trade = {
                'Timestamp': datetime.datetime.now().isoformat(),
                'OrderID': trade.get('order_id'),
                'Symbol': symbol,
                'TradeType': trade['type'],
                'EntryPrice': entry_price,
                'ExitPrice': exit_price,
                'Quantity': qty,
                'Leverage': leverage,
                'ProfitLoss': pnl,
                'ProfitLossPercent': pnl_percent,
                'ExitReason': exit_reason,
                'Status': 'CLOSED',
                'Strategy': trade.get('Strategy', 'N/A'),
                'PaperTrade': trade.get('paper_trade', is_paper_trade),
            }
            
            emoji = "💰" if pnl >= 0 else "📉"
            logger.info(f"{emoji} Trade closed: {symbol} P&L: ${pnl:.2f} ({pnl_percent:+.2f}%)")
            
            self.active_trade = None
            return completed_trade
            
        except Exception as e:
            logger.error(f"Error exiting trade: {e}")
            self.active_trade = None
            return None
    
    async def get_position_status(self) -> Optional[Dict[str, Any]]:
        """
        Get current position status with real-time data.
        
        Returns:
            Dictionary with position status or None if no position
        """
        if not self.active_trade:
            return None
        
        try:
            symbol = self.active_trade['symbol']
            current_price = await self.client.get_current_price(symbol)
            
            entry_price = self.active_trade['entry_price']
            qty = self.active_trade['quantity']
            trade_type = self.active_trade['type']
            leverage = self.active_trade.get('leverage', 1)
            
            if trade_type == 'BUY':
                pnl = (current_price - entry_price) * qty
                pnl_percent = ((current_price - entry_price) / entry_price) * 100 * leverage
            else:
                pnl = (entry_price - current_price) * qty
                pnl_percent = ((entry_price - current_price) / entry_price) * 100 * leverage
            
            return {
                'symbol': symbol,
                'type': trade_type,
                'entry_price': entry_price,
                'current_price': current_price,
                'quantity': qty,
                'leverage': leverage,
                'unrealized_pnl': pnl,
                'unrealized_pnl_percent': pnl_percent,
                'stop_loss': self.active_trade.get('stop_loss'),
                'take_profit': self.active_trade.get('take_profit'),
                'trailing_stop': self.active_trade.get('trailing_stop_loss'),
            }
            
        except Exception as e:
            logger.error(f"Error getting position status: {e}")
            return None
    
    async def check_liquidation_risk(self) -> Optional[Dict[str, Any]]:
        """
        Check if position is at risk of liquidation.
        
        Returns:
            Dictionary with liquidation risk info or None
        """
        if not self.active_trade:
            return None
        
        try:
            symbol = self.active_trade['symbol']
            positions = await self.client.get_positions(symbol)
            
            if not positions:
                return None
            
            pos = positions[0]
            liq_price = pos.get('liqPrice')
            current_price = pos.get('markPrice', 0)
            
            if not liq_price or liq_price == 0:
                return None
            
            # Calculate distance to liquidation
            if self.active_trade['type'] == 'BUY':
                distance_percent = ((current_price - liq_price) / current_price) * 100
            else:
                distance_percent = ((liq_price - current_price) / current_price) * 100
            
            risk_level = "LOW"
            if distance_percent < 5:
                risk_level = "CRITICAL"
            elif distance_percent < 10:
                risk_level = "HIGH"
            elif distance_percent < 20:
                risk_level = "MEDIUM"
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'liquidation_price': liq_price,
                'distance_percent': distance_percent,
                'risk_level': risk_level,
            }
            
        except Exception as e:
            logger.error(f"Error checking liquidation risk: {e}")
            return None
