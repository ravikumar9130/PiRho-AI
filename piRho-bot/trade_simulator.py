"""
Trade Simulator
Realistic trade simulation with slippage, fees, and position management
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class OrderType(str, Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class PositionSide(str, Enum):
    """Position side."""
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeConfig:
    """Configuration for trade simulation."""
    initial_capital: float = 10000.0
    leverage: int = 1
    risk_per_trade: float = 2.0  # Percentage of capital to risk per trade
    stop_loss_percent: float = 2.0
    take_profit_percent: float = 4.0
    use_trailing_stop: bool = False
    trailing_stop_percent: float = 1.5
    slippage_percent: float = 0.1
    commission_percent: float = 0.06  # Bybit taker fee
    max_position_size_percent: float = 100.0  # Max % of capital per position
    partial_fill_probability: float = 0.0  # 0 = always full fills
    
    def validate(self) -> bool:
        """Validate configuration."""
        assert self.initial_capital > 0, "Initial capital must be positive"
        assert 1 <= self.leverage <= 100, "Leverage must be between 1 and 100"
        assert 0 < self.risk_per_trade <= 100, "Risk per trade must be between 0 and 100"
        assert 0 < self.stop_loss_percent <= 50, "Stop loss must be between 0 and 50%"
        assert 0 < self.take_profit_percent <= 100, "Take profit must be between 0 and 100%"
        assert 0 <= self.slippage_percent <= 5, "Slippage must be between 0 and 5%"
        assert 0 <= self.commission_percent <= 1, "Commission must be between 0 and 1%"
        return True


@dataclass
class Position:
    """Represents an open position."""
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: int
    entry_time: datetime
    stop_loss: float
    take_profit: float
    trailing_stop_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    entry_fees: float = 0.0
    entry_slippage: float = 0.0
    signal_reason: str = ""
    
    @property
    def notional_value(self) -> float:
        """Get position notional value."""
        return self.entry_price * self.quantity
    
    @property
    def margin_required(self) -> float:
        """Get margin required for position."""
        return self.notional_value / self.leverage
    
    def update_pnl(self, current_price: float) -> float:
        """Update unrealized P&L."""
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity * self.leverage
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity * self.leverage
        return self.unrealized_pnl
    
    def update_trailing_stop(self, current_price: float, trail_percent: float):
        """Update trailing stop price."""
        if self.trailing_stop_price is None:
            # Initialize trailing stop
            if self.side == PositionSide.LONG:
                self.trailing_stop_price = current_price * (1 - trail_percent / 100)
            else:
                self.trailing_stop_price = current_price * (1 + trail_percent / 100)
        else:
            # Update if price moved favorably
            if self.side == PositionSide.LONG:
                new_stop = current_price * (1 - trail_percent / 100)
                self.trailing_stop_price = max(self.trailing_stop_price, new_stop)
            else:
                new_stop = current_price * (1 + trail_percent / 100)
                self.trailing_stop_price = min(self.trailing_stop_price, new_stop)


@dataclass
class SimulatedTrade:
    """Result of a completed trade simulation."""
    trade_id: int
    entry_time: datetime
    exit_time: datetime
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    leverage: int
    pnl: float
    pnl_percent: float
    fees: float
    slippage: float
    exit_reason: str
    signal_reason: str = ""
    
    @property
    def duration_minutes(self) -> int:
        """Get trade duration in minutes."""
        return int((self.exit_time - self.entry_time).total_seconds() / 60)


class TradeSimulator:
    """
    Simulates trades with realistic execution.
    
    Features:
    - Slippage modeling
    - Commission calculation
    - Position sizing based on risk
    - Stop loss and take profit execution
    - Trailing stop support
    - Margin and leverage handling
    """
    
    def __init__(self, config: TradeConfig):
        """
        Initialize trade simulator.
        
        Args:
            config: Trade configuration
        """
        config.validate()
        self.config = config
        self.capital = config.initial_capital
        self.position: Optional[Position] = None
        self.trades: List[SimulatedTrade] = []
        self.equity_curve: List[float] = [config.initial_capital]
        self.trade_counter = 0
    
    def reset(self):
        """Reset simulator to initial state."""
        self.capital = self.config.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = [self.config.initial_capital]
        self.trade_counter = 0
    
    def calculate_position_size(
        self,
        entry_price: float,
        stop_loss_price: float,
    ) -> float:
        """
        Calculate position size based on risk per trade.
        
        Args:
            entry_price: Expected entry price
            stop_loss_price: Stop loss price
            
        Returns:
            Position size (quantity)
        """
        risk_amount = self.capital * (self.config.risk_per_trade / 100)
        stop_distance = abs(entry_price - stop_loss_price)
        
        if stop_distance == 0:
            return 0
        
        # Position size = Risk Amount / Stop Distance
        position_size = risk_amount / stop_distance
        
        # Apply leverage
        max_position_value = self.capital * self.config.leverage * (self.config.max_position_size_percent / 100)
        max_quantity = max_position_value / entry_price
        
        return min(position_size, max_quantity)
    
    def apply_slippage(
        self,
        price: float,
        is_buy: bool,
        is_entry: bool = True,
    ) -> Tuple[float, float]:
        """
        Apply slippage to price.
        
        Args:
            price: Original price
            is_buy: True for buy orders
            is_entry: True for entry orders
            
        Returns:
            Tuple of (adjusted price, slippage amount)
        """
        slippage_pct = self.config.slippage_percent / 100
        
        # Slippage direction
        if is_buy:
            adjusted = price * (1 + slippage_pct)
        else:
            adjusted = price * (1 - slippage_pct)
        
        slippage_amount = abs(adjusted - price)
        return adjusted, slippage_amount
    
    def calculate_commission(self, notional_value: float) -> float:
        """Calculate commission for a trade."""
        return notional_value * (self.config.commission_percent / 100)
    
    def open_position(
        self,
        side: str,
        price: float,
        timestamp: datetime,
        signal_reason: str = "",
    ) -> Optional[Position]:
        """
        Open a new position.
        
        Args:
            side: 'BUY' or 'SELL'
            price: Current market price
            timestamp: Current timestamp
            signal_reason: Reason for the signal
            
        Returns:
            Position if opened, None if failed
        """
        if self.position is not None:
            logger.warning("Cannot open position: already have an open position")
            return None
        
        position_side = PositionSide.LONG if side == 'BUY' else PositionSide.SHORT
        
        # Calculate stop loss and take profit prices
        if position_side == PositionSide.LONG:
            stop_loss = price * (1 - self.config.stop_loss_percent / 100)
            take_profit = price * (1 + self.config.take_profit_percent / 100)
        else:
            stop_loss = price * (1 + self.config.stop_loss_percent / 100)
            take_profit = price * (1 - self.config.take_profit_percent / 100)
        
        # Apply slippage to entry
        is_buy = position_side == PositionSide.LONG
        entry_price, slippage = self.apply_slippage(price, is_buy, is_entry=True)
        
        # Calculate position size
        quantity = self.calculate_position_size(entry_price, stop_loss)
        
        if quantity <= 0:
            logger.warning("Cannot open position: calculated quantity is 0")
            return None
        
        # Calculate commission
        notional = entry_price * quantity
        commission = self.calculate_commission(notional)
        
        # Check if we have enough margin
        margin_required = notional / self.config.leverage
        if margin_required + commission > self.capital:
            logger.warning(f"Insufficient margin: need {margin_required + commission:.2f}, have {self.capital:.2f}")
            return None
        
        # Deduct commission from capital
        self.capital -= commission
        
        self.position = Position(
            side=position_side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=self.config.leverage,
            entry_time=timestamp,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_fees=commission,
            entry_slippage=slippage,
            signal_reason=signal_reason,
        )
        
        logger.debug(
            f"Opened {position_side.value} position: "
            f"qty={quantity:.6f} @ {entry_price:.2f}, "
            f"SL={stop_loss:.2f}, TP={take_profit:.2f}"
        )
        
        return self.position
    
    def close_position(
        self,
        price: float,
        timestamp: datetime,
        exit_reason: str = "signal",
    ) -> Optional[SimulatedTrade]:
        """
        Close the current position.
        
        Args:
            price: Current market price
            timestamp: Current timestamp
            exit_reason: Reason for closing
            
        Returns:
            SimulatedTrade if closed, None if no position
        """
        if self.position is None:
            return None
        
        pos = self.position
        
        # Apply slippage to exit
        is_buy = pos.side == PositionSide.SHORT  # Closing short = buying
        exit_price, exit_slippage = self.apply_slippage(price, is_buy, is_entry=False)
        
        # Calculate P&L
        if pos.side == PositionSide.LONG:
            pnl = (exit_price - pos.entry_price) * pos.quantity * pos.leverage
            pnl_percent = ((exit_price / pos.entry_price) - 1) * 100 * pos.leverage
        else:
            pnl = (pos.entry_price - exit_price) * pos.quantity * pos.leverage
            pnl_percent = ((pos.entry_price / exit_price) - 1) * 100 * pos.leverage
        
        # Calculate exit commission
        notional = exit_price * pos.quantity
        exit_commission = self.calculate_commission(notional)
        
        # Net P&L after fees
        total_fees = pos.entry_fees + exit_commission
        total_slippage = pos.entry_slippage + exit_slippage
        pnl -= exit_commission
        
        # Update capital
        self.capital += pnl
        
        # Record trade
        self.trade_counter += 1
        trade = SimulatedTrade(
            trade_id=self.trade_counter,
            entry_time=pos.entry_time,
            exit_time=timestamp,
            side='BUY' if pos.side == PositionSide.LONG else 'SELL',
            entry_price=pos.entry_price,
            exit_price=exit_price,
            quantity=pos.quantity,
            leverage=pos.leverage,
            pnl=pnl,
            pnl_percent=pnl_percent,
            fees=total_fees,
            slippage=total_slippage,
            exit_reason=exit_reason,
            signal_reason=pos.signal_reason,
        )
        
        self.trades.append(trade)
        self.position = None
        
        logger.debug(
            f"Closed position: PnL={pnl:.2f} ({pnl_percent:.2f}%), "
            f"reason={exit_reason}"
        )
        
        return trade
    
    def check_exit_conditions(
        self,
        high: float,
        low: float,
        close: float,
        timestamp: datetime,
    ) -> Optional[SimulatedTrade]:
        """
        Check if position should be closed based on SL/TP/trailing stop.
        
        Args:
            high: Candle high price
            low: Candle low price
            close: Candle close price
            timestamp: Current timestamp
            
        Returns:
            SimulatedTrade if position was closed, None otherwise
        """
        if self.position is None:
            return None
        
        pos = self.position
        
        # Update trailing stop if enabled
        if self.config.use_trailing_stop:
            pos.update_trailing_stop(close, self.config.trailing_stop_percent)
        
        # Determine effective stop loss (trailing or fixed)
        if pos.trailing_stop_price is not None:
            if pos.side == PositionSide.LONG:
                effective_stop = max(pos.stop_loss, pos.trailing_stop_price)
            else:
                effective_stop = min(pos.stop_loss, pos.trailing_stop_price)
        else:
            effective_stop = pos.stop_loss
        
        # Check stop loss
        if pos.side == PositionSide.LONG:
            if low <= effective_stop:
                return self.close_position(effective_stop, timestamp, "Stop Loss")
            if high >= pos.take_profit:
                return self.close_position(pos.take_profit, timestamp, "Take Profit")
        else:
            if high >= effective_stop:
                return self.close_position(effective_stop, timestamp, "Stop Loss")
            if low <= pos.take_profit:
                return self.close_position(pos.take_profit, timestamp, "Take Profit")
        
        return None
    
    def process_signal(
        self,
        signal: str,
        price: float,
        high: float,
        low: float,
        timestamp: datetime,
        signal_reason: str = "",
    ) -> Optional[SimulatedTrade]:
        """
        Process a trading signal.
        
        Args:
            signal: 'BUY', 'SELL', or 'HOLD'
            price: Current close price
            high: Current high price
            low: Current low price
            timestamp: Current timestamp
            signal_reason: Reason for the signal
            
        Returns:
            SimulatedTrade if a trade was completed, None otherwise
        """
        # First check if we need to exit current position
        trade = self.check_exit_conditions(high, low, price, timestamp)
        
        if self.position is None and signal in ['BUY', 'SELL']:
            # Open new position
            self.open_position(signal, price, timestamp, signal_reason)
        elif self.position is not None and signal != 'HOLD':
            # Check for reversal signal
            is_long = self.position.side == PositionSide.LONG
            if (is_long and signal == 'SELL') or (not is_long and signal == 'BUY'):
                trade = self.close_position(price, timestamp, "Signal Reversal")
                # Open opposite position
                self.open_position(signal, price, timestamp, signal_reason)
        
        # Update equity curve
        current_equity = self.capital
        if self.position is not None:
            self.position.update_pnl(price)
            current_equity += self.position.unrealized_pnl
        self.equity_curve.append(current_equity)
        
        return trade
    
    def get_summary(self) -> Dict[str, Any]:
        """Get simulation summary."""
        final_equity = self.capital
        if self.position:
            final_equity += self.position.unrealized_pnl
        
        return {
            'initial_capital': self.config.initial_capital,
            'final_capital': final_equity,
            'total_trades': len(self.trades),
            'open_position': self.position is not None,
            'total_pnl': final_equity - self.config.initial_capital,
            'total_return_percent': ((final_equity / self.config.initial_capital) - 1) * 100,
        }


def simulate_backtest(
    signals: List[Tuple[datetime, str, float, float, float, str]],
    config: Optional[TradeConfig] = None,
) -> Tuple[List[SimulatedTrade], List[float]]:
    """
    Convenience function to run a backtest simulation.
    
    Args:
        signals: List of (timestamp, signal, close, high, low, reason) tuples
        config: Trade configuration (uses defaults if None)
        
    Returns:
        Tuple of (trades list, equity curve)
    """
    if config is None:
        config = TradeConfig()
    
    simulator = TradeSimulator(config)
    
    for timestamp, signal, close, high, low, reason in signals:
        simulator.process_signal(signal, close, high, low, timestamp, reason)
    
    # Close any remaining position at last price
    if simulator.position and signals:
        last_timestamp, _, last_close, _, _, _ = signals[-1]
        simulator.close_position(last_close, last_timestamp, "End of Backtest")
    
    return simulator.trades, simulator.equity_curve

