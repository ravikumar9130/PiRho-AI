"""
Backtest Metrics Calculator
Comprehensive metrics calculation for backtesting results
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single completed trade."""
    trade_id: int
    entry_time: datetime
    exit_time: datetime
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    exit_price: float
    quantity: float
    leverage: int = 1
    pnl: float = 0.0
    pnl_percent: float = 0.0
    fees: float = 0.0
    slippage: float = 0.0
    exit_reason: str = ""
    signal_reason: str = ""
    
    @property
    def duration(self) -> timedelta:
        """Get trade duration."""
        return self.exit_time - self.entry_time
    
    @property
    def duration_minutes(self) -> int:
        """Get trade duration in minutes."""
        return int(self.duration.total_seconds() / 60)
    
    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.pnl > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert trade to dictionary."""
        return {
            'trade_id': self.trade_id,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'side': self.side,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'quantity': self.quantity,
            'leverage': self.leverage,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'fees': self.fees,
            'slippage': self.slippage,
            'exit_reason': self.exit_reason,
            'signal_reason': self.signal_reason,
            'duration_minutes': self.duration_minutes,
        }


@dataclass
class BacktestMetrics:
    """Comprehensive backtesting metrics."""
    # Basic statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    breakeven_trades: int = 0
    win_rate: float = 0.0
    
    # P&L metrics
    total_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    total_return: float = 0.0
    
    # APY calculations
    simple_apy: float = 0.0
    compound_apy: float = 0.0
    
    # Risk-adjusted returns
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Drawdown metrics
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    max_drawdown_duration_days: int = 0
    average_drawdown: float = 0.0
    
    # Trade quality metrics
    profit_factor: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    average_win_percent: float = 0.0
    average_loss_percent: float = 0.0
    
    # Trade timing
    average_trade_duration_minutes: float = 0.0
    average_winning_trade_duration: float = 0.0
    average_losing_trade_duration: float = 0.0
    
    # Streak analysis
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    current_streak: int = 0
    current_streak_type: str = ""
    
    # Cost analysis
    total_fees: float = 0.0
    total_slippage: float = 0.0
    fees_as_percent_of_profit: float = 0.0
    
    # Daily/Monthly analysis
    best_day: float = 0.0
    worst_day: float = 0.0
    best_month: float = 0.0
    worst_month: float = 0.0
    profitable_days: int = 0
    losing_days: int = 0
    profitable_months: int = 0
    losing_months: int = 0
    
    # Expectancy and edge
    expectancy: float = 0.0
    expectancy_ratio: float = 0.0  # Expectancy / average loss
    risk_reward_ratio: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'breakeven_trades': self.breakeven_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'gross_profit': round(self.gross_profit, 2),
            'gross_loss': round(self.gross_loss, 2),
            'total_return': round(self.total_return, 2),
            'simple_apy': round(self.simple_apy, 2),
            'compound_apy': round(self.compound_apy, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'calmar_ratio': round(self.calmar_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'max_drawdown_percent': round(self.max_drawdown_percent, 2),
            'max_drawdown_duration_days': self.max_drawdown_duration_days,
            'average_drawdown': round(self.average_drawdown, 2),
            'profit_factor': round(self.profit_factor, 2),
            'average_win': round(self.average_win, 2),
            'average_loss': round(self.average_loss, 2),
            'largest_win': round(self.largest_win, 2),
            'largest_loss': round(self.largest_loss, 2),
            'average_win_percent': round(self.average_win_percent, 2),
            'average_loss_percent': round(self.average_loss_percent, 2),
            'average_trade_duration_minutes': round(self.average_trade_duration_minutes, 2),
            'max_consecutive_wins': self.max_consecutive_wins,
            'max_consecutive_losses': self.max_consecutive_losses,
            'total_fees': round(self.total_fees, 2),
            'total_slippage': round(self.total_slippage, 2),
            'best_day': round(self.best_day, 2),
            'worst_day': round(self.worst_day, 2),
            'expectancy': round(self.expectancy, 2),
            'risk_reward_ratio': round(self.risk_reward_ratio, 2),
        }


class MetricsCalculator:
    """Calculator for backtest performance metrics."""
    
    def __init__(self, initial_capital: float = 10000.0, risk_free_rate: float = 0.04):
        """
        Initialize metrics calculator.
        
        Args:
            initial_capital: Starting capital for the backtest
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default 4%)
        """
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
    
    def calculate_all(
        self,
        trades: List[Trade],
        equity_curve: List[float],
        backtest_days: int,
    ) -> BacktestMetrics:
        """
        Calculate all metrics from trades and equity curve.
        
        Args:
            trades: List of completed trades
            equity_curve: List of equity values over time
            backtest_days: Number of days in the backtest period
            
        Returns:
            Comprehensive BacktestMetrics
        """
        metrics = BacktestMetrics()
        
        if not trades:
            return metrics
        
        # Basic statistics
        metrics.total_trades = len(trades)
        metrics.winning_trades = sum(1 for t in trades if t.pnl > 0)
        metrics.losing_trades = sum(1 for t in trades if t.pnl < 0)
        metrics.breakeven_trades = sum(1 for t in trades if t.pnl == 0)
        metrics.win_rate = (metrics.winning_trades / metrics.total_trades) * 100
        
        # P&L metrics
        metrics.total_pnl = sum(t.pnl for t in trades)
        metrics.gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
        metrics.gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
        
        final_capital = equity_curve[-1] if equity_curve else self.initial_capital
        metrics.total_return = ((final_capital / self.initial_capital) - 1) * 100
        
        # APY calculations
        metrics.simple_apy = self._calculate_simple_apy(metrics.total_return, backtest_days)
        metrics.compound_apy = self._calculate_compound_apy(equity_curve, backtest_days)
        
        # Risk-adjusted returns
        daily_returns = self._calculate_daily_returns(equity_curve)
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
        metrics.sortino_ratio = self._calculate_sortino_ratio(daily_returns)
        
        # Drawdown metrics
        dd_metrics = self._calculate_drawdown_metrics(equity_curve)
        metrics.max_drawdown = dd_metrics['max_drawdown']
        metrics.max_drawdown_percent = dd_metrics['max_drawdown_percent']
        metrics.max_drawdown_duration_days = dd_metrics['max_duration_days']
        metrics.average_drawdown = dd_metrics['average_drawdown']
        
        # Calmar ratio (return / max drawdown)
        if metrics.max_drawdown_percent > 0:
            annualized_return = metrics.simple_apy
            metrics.calmar_ratio = annualized_return / metrics.max_drawdown_percent
        
        # Trade quality metrics
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [abs(t.pnl) for t in trades if t.pnl < 0]
        
        metrics.average_win = np.mean(wins) if wins else 0
        metrics.average_loss = np.mean(losses) if losses else 0
        metrics.largest_win = max(wins) if wins else 0
        metrics.largest_loss = max(losses) if losses else 0
        
        win_pcts = [t.pnl_percent for t in trades if t.pnl > 0]
        loss_pcts = [abs(t.pnl_percent) for t in trades if t.pnl < 0]
        metrics.average_win_percent = np.mean(win_pcts) if win_pcts else 0
        metrics.average_loss_percent = np.mean(loss_pcts) if loss_pcts else 0
        
        # Profit factor
        if metrics.gross_loss > 0:
            metrics.profit_factor = metrics.gross_profit / metrics.gross_loss
        elif metrics.gross_profit > 0:
            metrics.profit_factor = float('inf')
        
        # Risk reward ratio
        if metrics.average_loss > 0:
            metrics.risk_reward_ratio = metrics.average_win / metrics.average_loss
        
        # Trade timing
        durations = [t.duration_minutes for t in trades]
        metrics.average_trade_duration_minutes = np.mean(durations) if durations else 0
        
        win_durations = [t.duration_minutes for t in trades if t.pnl > 0]
        loss_durations = [t.duration_minutes for t in trades if t.pnl < 0]
        metrics.average_winning_trade_duration = np.mean(win_durations) if win_durations else 0
        metrics.average_losing_trade_duration = np.mean(loss_durations) if loss_durations else 0
        
        # Streak analysis
        streak_metrics = self._calculate_streaks(trades)
        metrics.max_consecutive_wins = streak_metrics['max_wins']
        metrics.max_consecutive_losses = streak_metrics['max_losses']
        metrics.current_streak = streak_metrics['current_streak']
        metrics.current_streak_type = streak_metrics['current_type']
        
        # Cost analysis
        metrics.total_fees = sum(t.fees for t in trades)
        metrics.total_slippage = sum(t.slippage for t in trades)
        if metrics.gross_profit > 0:
            metrics.fees_as_percent_of_profit = (metrics.total_fees / metrics.gross_profit) * 100
        
        # Daily analysis
        daily_pnl = self._aggregate_daily_pnl(trades)
        if daily_pnl:
            metrics.best_day = max(daily_pnl.values())
            metrics.worst_day = min(daily_pnl.values())
            metrics.profitable_days = sum(1 for v in daily_pnl.values() if v > 0)
            metrics.losing_days = sum(1 for v in daily_pnl.values() if v < 0)
        
        # Monthly analysis
        monthly_pnl = self._aggregate_monthly_pnl(trades)
        if monthly_pnl:
            metrics.best_month = max(monthly_pnl.values())
            metrics.worst_month = min(monthly_pnl.values())
            metrics.profitable_months = sum(1 for v in monthly_pnl.values() if v > 0)
            metrics.losing_months = sum(1 for v in monthly_pnl.values() if v < 0)
        
        # Expectancy
        loss_rate = 1 - (metrics.win_rate / 100)
        metrics.expectancy = (metrics.win_rate / 100 * metrics.average_win) - (loss_rate * metrics.average_loss)
        if metrics.average_loss > 0:
            metrics.expectancy_ratio = metrics.expectancy / metrics.average_loss
        
        return metrics
    
    def _calculate_simple_apy(self, total_return: float, days: int) -> float:
        """Calculate simple annualized percentage yield."""
        if days <= 0:
            return 0.0
        return ((1 + total_return / 100) ** (365 / days) - 1) * 100
    
    def _calculate_compound_apy(self, equity_curve: List[float], days: int) -> float:
        """Calculate compound APY from equity curve."""
        if len(equity_curve) < 2 or days <= 0:
            return 0.0
        
        daily_returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1] > 0:
                daily_returns.append(equity_curve[i] / equity_curve[i-1] - 1)
        
        if not daily_returns:
            return 0.0
        
        # Geometric mean of daily returns
        avg_daily_return = np.mean(daily_returns)
        compound_apy = ((1 + avg_daily_return) ** 365 - 1) * 100
        
        return compound_apy
    
    def _calculate_daily_returns(self, equity_curve: List[float]) -> List[float]:
        """Calculate daily returns from equity curve."""
        if len(equity_curve) < 2:
            return []
        
        returns = []
        for i in range(1, len(equity_curve)):
            if equity_curve[i-1] > 0:
                returns.append(equity_curve[i] / equity_curve[i-1] - 1)
        
        return returns
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """Calculate annualized Sharpe ratio."""
        if len(daily_returns) < 2:
            return 0.0
        
        avg_return = np.mean(daily_returns)
        std_return = np.std(daily_returns, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualize: multiply by sqrt(252 trading days)
        daily_rf = self.risk_free_rate / 252
        sharpe = ((avg_return - daily_rf) / std_return) * np.sqrt(252)
        
        return sharpe
    
    def _calculate_sortino_ratio(self, daily_returns: List[float]) -> float:
        """Calculate annualized Sortino ratio (only downside volatility)."""
        if len(daily_returns) < 2:
            return 0.0
        
        avg_return = np.mean(daily_returns)
        negative_returns = [r for r in daily_returns if r < 0]
        
        if not negative_returns:
            return float('inf') if avg_return > 0 else 0.0
        
        downside_std = np.std(negative_returns, ddof=1)
        
        if downside_std == 0:
            return 0.0
        
        daily_rf = self.risk_free_rate / 252
        sortino = ((avg_return - daily_rf) / downside_std) * np.sqrt(252)
        
        return sortino
    
    def _calculate_drawdown_metrics(self, equity_curve: List[float]) -> Dict[str, float]:
        """Calculate drawdown metrics from equity curve."""
        if not equity_curve:
            return {
                'max_drawdown': 0,
                'max_drawdown_percent': 0,
                'max_duration_days': 0,
                'average_drawdown': 0,
            }
        
        peak = equity_curve[0]
        max_dd = 0
        max_dd_pct = 0
        drawdowns = []
        
        dd_start = None
        max_duration = 0
        current_duration = 0
        
        for i, eq in enumerate(equity_curve):
            if eq > peak:
                peak = eq
                if dd_start is not None:
                    max_duration = max(max_duration, current_duration)
                    current_duration = 0
                    dd_start = None
            else:
                dd = peak - eq
                dd_pct = (dd / peak) * 100 if peak > 0 else 0
                
                if dd > max_dd:
                    max_dd = dd
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                
                if dd > 0:
                    drawdowns.append(dd)
                    if dd_start is None:
                        dd_start = i
                    current_duration += 1
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_percent': max_dd_pct,
            'max_duration_days': max_duration,
            'average_drawdown': np.mean(drawdowns) if drawdowns else 0,
        }
    
    def _calculate_streaks(self, trades: List[Trade]) -> Dict[str, Any]:
        """Calculate winning and losing streaks."""
        if not trades:
            return {
                'max_wins': 0,
                'max_losses': 0,
                'current_streak': 0,
                'current_type': '',
            }
        
        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0
        
        for trade in trades:
            if trade.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            elif trade.pnl < 0:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
            else:
                current_wins = 0
                current_losses = 0
        
        current_streak = current_wins if current_wins > 0 else current_losses
        current_type = 'wins' if current_wins > 0 else ('losses' if current_losses > 0 else '')
        
        return {
            'max_wins': max_wins,
            'max_losses': max_losses,
            'current_streak': current_streak,
            'current_type': current_type,
        }
    
    def _aggregate_daily_pnl(self, trades: List[Trade]) -> Dict[str, float]:
        """Aggregate P&L by day."""
        daily_pnl = defaultdict(float)
        for trade in trades:
            day = trade.exit_time.strftime('%Y-%m-%d')
            daily_pnl[day] += trade.pnl
        return dict(daily_pnl)
    
    def _aggregate_monthly_pnl(self, trades: List[Trade]) -> Dict[str, float]:
        """Aggregate P&L by month."""
        monthly_pnl = defaultdict(float)
        for trade in trades:
            month = trade.exit_time.strftime('%Y-%m')
            monthly_pnl[month] += trade.pnl
        return dict(monthly_pnl)


def calculate_metrics(
    trades: List[Trade],
    equity_curve: List[float],
    initial_capital: float = 10000.0,
    backtest_days: int = 30,
) -> BacktestMetrics:
    """
    Convenience function to calculate all metrics.
    
    Args:
        trades: List of completed trades
        equity_curve: List of equity values
        initial_capital: Starting capital
        backtest_days: Number of days in backtest
        
    Returns:
        Complete BacktestMetrics
    """
    calculator = MetricsCalculator(initial_capital=initial_capital)
    return calculator.calculate_all(trades, equity_curve, backtest_days)

