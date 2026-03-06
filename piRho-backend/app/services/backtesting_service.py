"""
Backtesting Service
Orchestrates backtest execution by calling the bot backtesting engine
"""

import logging
import asyncio
import httpx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from collections import defaultdict

from app.models.backtesting import (
    BacktestResult,
    BacktestMetrics,
    BacktestConfig,
    IndicatorConfig,
    TradeDetail,
    EquityCurvePoint,
    DailyReturn,
    MonthlyReturn,
)

logger = logging.getLogger(__name__)


class BacktestingService:
    """
    Service for running backtests against historical market data.
    This is a self-contained implementation that doesn't require the bot service to be running.
    """
    
    # Bybit API endpoint for klines
    BYBIT_API_URL = "https://api.bybit.com"
    
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx async client."""
        if self.client is None or self.client.is_closed:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def run_backtest(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategy: str,
        timeframe: str,
        indicators: IndicatorConfig,
        config: BacktestConfig,
    ) -> BacktestResult:
        """
        Run a complete backtest.
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            start_date: Backtest start date
            end_date: Backtest end date
            strategy: Strategy name to test
            timeframe: Candlestick timeframe
            indicators: Indicator configuration
            config: Backtest configuration
            
        Returns:
            Complete backtest results with metrics
        """
        logger.info(f"Starting backtest: {symbol} {strategy} from {start_date} to {end_date}")
        
        # Fetch historical data
        df = await self._fetch_historical_data(symbol, start_date, end_date, timeframe)
        
        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient data: only {len(df)} candles fetched")
        
        logger.info(f"Fetched {len(df)} candles for {symbol}")
        
        # Calculate indicators
        df = self._calculate_indicators(df, indicators)
        
        # Run strategy simulation
        trades, equity_curve = self._run_strategy_simulation(
            df, strategy, config, indicators
        )
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            trades, equity_curve, config.initial_capital,
            (end_date - start_date).days
        )
        
        # Calculate daily and monthly returns
        daily_returns = self._calculate_daily_returns(trades, df)
        monthly_returns = self._calculate_monthly_returns(daily_returns)
        
        # Build equity curve points
        equity_points = self._build_equity_curve_points(equity_curve, df)
        
        return BacktestResult(
            symbol=symbol,
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            initial_capital=config.initial_capital,
            final_capital=equity_curve[-1] if equity_curve else config.initial_capital,
            config=config,
            indicators=indicators,
            metrics=metrics,
            equity_curve=equity_points,
            trades=trades,
            daily_returns=daily_returns,
            monthly_returns=monthly_returns,
            execution_time_seconds=0,  # Will be set by endpoint
            data_points_analyzed=len(df),
        )
    
    async def _fetch_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str,
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data from Bybit."""
        client = await self._get_client()
        
        all_data = []
        
        # Ensure timezone-aware datetimes (convert to UTC if naive)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        
        # Convert to millisecond timestamps
        current_end = int(end_date.timestamp() * 1000)
        start_ts = int(start_date.timestamp() * 1000)
        
        logger.info(f"Fetching data for {symbol} from {start_date} to {end_date}")
        logger.info(f"Timestamps: start={start_ts}, end={current_end}, timeframe={timeframe}")
        
        # Bybit returns data in reverse chronological order
        fetch_attempts = 0
        max_attempts = 100  # Prevent infinite loops
        
        while current_end > start_ts and fetch_attempts < max_attempts:
            fetch_attempts += 1
            url = f"{self.BYBIT_API_URL}/v5/market/kline"
            params = {
                "category": "linear",
                "symbol": symbol,
                "interval": timeframe,
                "end": current_end,
                "limit": 1000,
            }
            
            try:
                logger.debug(f"Fetching batch {fetch_attempts}: end={current_end}")
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    logger.error(f"Bybit API HTTP error: {response.status_code}, response: {response.text}")
                    break
                
                try:
                    data = response.json()
                except Exception as json_err:
                    logger.error(f"Failed to parse JSON: {json_err}, response: {response.text[:500]}")
                    break
                
                if data.get("retCode") != 0:
                    logger.error(f"Bybit API error: code={data.get('retCode')}, msg={data.get('retMsg')}")
                    break
                
                klines = data.get("result", {}).get("list", [])
                
                if not klines:
                    logger.debug(f"No more klines returned at end={current_end}")
                    break
                
                logger.debug(f"Received {len(klines)} klines")
                all_data.extend(klines)
                
                # Get earliest timestamp for next batch
                # Bybit v5 returns klines in descending order (newest first)
                # So the last element has the earliest timestamp
                earliest_ts = int(klines[-1][0])
                
                if earliest_ts <= start_ts:
                    logger.debug(f"Reached start timestamp")
                    break
                
                if earliest_ts >= current_end:
                    logger.warning(f"Timestamp not progressing: earliest={earliest_ts}, current_end={current_end}")
                    break
                
                current_end = earliest_ts - 1
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except httpx.TimeoutException:
                logger.error(f"Timeout fetching data from Bybit")
                break
            except Exception as e:
                logger.error(f"Error fetching data: {e}", exc_info=True)
                break
        
        logger.info(f"Fetched total {len(all_data)} raw klines after {fetch_attempts} API calls")
        
        if not all_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms', utc=True)
        for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
            df[col] = df[col].astype(float)
        
        # Sort chronologically and remove duplicates
        df = df.sort_values('timestamp').drop_duplicates(subset=['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Filter to requested date range (make start_date and end_date timezone-aware for comparison)
        start_dt_aware = pd.Timestamp(start_date).tz_convert('UTC') if start_date.tzinfo else pd.Timestamp(start_date, tz='UTC')
        end_dt_aware = pd.Timestamp(end_date).tz_convert('UTC') if end_date.tzinfo else pd.Timestamp(end_date, tz='UTC')
        
        df = df[(df.index >= start_dt_aware) & (df.index <= end_dt_aware)]
        
        logger.info(f"After filtering: {len(df)} candles from {df.index.min() if len(df) > 0 else 'N/A'} to {df.index.max() if len(df) > 0 else 'N/A'}")
        
        return df
    
    def _calculate_indicators(
        self,
        df: pd.DataFrame,
        config: IndicatorConfig
    ) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=config.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=config.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # EMAs
        df['ema_short'] = df['close'].ewm(span=config.ema_short, adjust=False).mean()
        df['ema_medium'] = df['close'].ewm(span=config.ema_medium, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=config.ema_long, adjust=False).mean()
        df['ema_trend'] = df['close'].ewm(span=config.ema_trend, adjust=False).mean()
        
        # Legacy column names for strategy compatibility
        df['ema_9'] = df['ema_short']
        df['ema_21'] = df['ema_medium']
        df['ema_50'] = df['ema_long']
        df['ema_200'] = df['ema_trend']
        
        # MACD
        ema_fast = df['close'].ewm(span=config.macd_fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=config.macd_slow, adjust=False).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=config.macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        df['bb_mid'] = df['close'].rolling(window=config.bb_period).mean()
        bb_std = df['close'].rolling(window=config.bb_period).std()
        df['bb_upper'] = df['bb_mid'] + (bb_std * config.bb_std_dev)
        df['bb_lower'] = df['bb_mid'] - (bb_std * config.bb_std_dev)
        df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        df['bb_bandwidth_ma'] = df['bb_bandwidth'].rolling(window=20).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(window=config.atr_period).mean()
        df['atr_ma'] = df['atr'].rolling(window=20).mean()
        
        # Supertrend
        hl2 = (df['high'] + df['low']) / 2
        upper_band = hl2 + (config.supertrend_multiplier * df['atr'])
        lower_band = hl2 - (config.supertrend_multiplier * df['atr'])
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > upper_band.iloc[i-1]:
                direction.iloc[i] = 1
            elif df['close'].iloc[i] < lower_band.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1] if i > 0 else 1
        
        df['supertrend_direction'] = direction.fillna(1)
        
        # VWAP (cumulative for the session)
        if config.vwap_enabled:
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            df['vwap'] = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
        
        # Volume MA
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        
        # Spread (for VSA)
        df['spread'] = df['high'] - df['low']
        
        return df
    
    def _run_strategy_simulation(
        self,
        df: pd.DataFrame,
        strategy_name: str,
        config: BacktestConfig,
        indicators: IndicatorConfig,
    ) -> tuple[List[TradeDetail], List[float]]:
        """Run the strategy simulation and generate trades."""
        trades = []
        equity_curve = [config.initial_capital]
        current_capital = config.initial_capital
        position = None  # None, 'LONG', or 'SHORT'
        entry_price = 0.0
        entry_time = None
        entry_quantity = 0.0
        trade_id = 0
        signal_reason = ""
        
        # Skip first N candles for indicator warmup
        warmup = max(config.leverage, 50, indicators.ema_trend)
        
        for i in range(warmup, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i - 1]
            current_time = df.index[i]
            price = current['close']
            
            # Generate signal based on strategy
            signal, reason = self._generate_signal(
                df, i, strategy_name, indicators, position
            )
            
            if position is None:
                # Look for entry
                if signal in ['BUY', 'SELL']:
                    # Calculate position size based on risk
                    risk_amount = current_capital * (config.risk_per_trade / 100)
                    stop_distance = price * (config.stop_loss_percent / 100)
                    position_value = (risk_amount / stop_distance) * price
                    position_value = min(position_value, current_capital * config.leverage)
                    
                    # Apply slippage to entry
                    slippage = price * (config.slippage_percent / 100)
                    if signal == 'BUY':
                        actual_entry = price + slippage
                    else:
                        actual_entry = price - slippage
                    
                    # Commission
                    commission = position_value * (config.commission_percent / 100)
                    
                    position = 'LONG' if signal == 'BUY' else 'SHORT'
                    entry_price = actual_entry
                    entry_time = current_time
                    entry_quantity = position_value / actual_entry
                    signal_reason = reason
                    
                    # Deduct commission from capital
                    current_capital -= commission
            else:
                # Check for exit conditions
                exit_signal = False
                exit_reason = ""
                exit_price = price
                
                if position == 'LONG':
                    # Check stop loss
                    if current['low'] <= entry_price * (1 - config.stop_loss_percent / 100):
                        exit_signal = True
                        exit_reason = "Stop Loss"
                        exit_price = entry_price * (1 - config.stop_loss_percent / 100)
                    # Check take profit
                    elif current['high'] >= entry_price * (1 + config.take_profit_percent / 100):
                        exit_signal = True
                        exit_reason = "Take Profit"
                        exit_price = entry_price * (1 + config.take_profit_percent / 100)
                    # Check for opposite signal
                    elif signal == 'SELL':
                        exit_signal = True
                        exit_reason = "Signal Reversal"
                else:  # SHORT
                    # Check stop loss
                    if current['high'] >= entry_price * (1 + config.stop_loss_percent / 100):
                        exit_signal = True
                        exit_reason = "Stop Loss"
                        exit_price = entry_price * (1 + config.stop_loss_percent / 100)
                    # Check take profit
                    elif current['low'] <= entry_price * (1 - config.take_profit_percent / 100):
                        exit_signal = True
                        exit_reason = "Take Profit"
                        exit_price = entry_price * (1 - config.take_profit_percent / 100)
                    # Check for opposite signal
                    elif signal == 'BUY':
                        exit_signal = True
                        exit_reason = "Signal Reversal"
                
                if exit_signal:
                    # Apply slippage to exit
                    slippage = exit_price * (config.slippage_percent / 100)
                    if position == 'LONG':
                        actual_exit = exit_price - slippage
                        pnl = (actual_exit - entry_price) * entry_quantity
                    else:
                        actual_exit = exit_price + slippage
                        pnl = (entry_price - actual_exit) * entry_quantity
                    
                    # Apply leverage to PnL
                    pnl = pnl * config.leverage
                    
                    # Commission on exit
                    exit_value = entry_quantity * actual_exit
                    commission = exit_value * (config.commission_percent / 100)
                    pnl -= commission
                    
                    # Calculate percentages
                    if position == 'LONG':
                        pnl_percent = ((actual_exit / entry_price) - 1) * 100 * config.leverage
                    else:
                        pnl_percent = ((entry_price / actual_exit) - 1) * 100 * config.leverage
                    
                    # Update capital
                    current_capital += pnl
                    
                    # Calculate duration
                    duration_minutes = int((current_time - entry_time).total_seconds() / 60)
                    
                    # Record trade
                    trade_id += 1
                    trades.append(TradeDetail(
                        trade_id=trade_id,
                        entry_time=entry_time,
                        exit_time=current_time,
                        side='BUY' if position == 'LONG' else 'SELL',
                        entry_price=entry_price,
                        exit_price=actual_exit,
                        quantity=entry_quantity,
                        leverage=config.leverage,
                        pnl=pnl,
                        pnl_percent=pnl_percent,
                        fees=commission * 2,  # Entry + exit
                        exit_reason=exit_reason,
                        signal_reason=signal_reason,
                        duration_minutes=duration_minutes,
                    ))
                    
                    position = None
                    entry_price = 0.0
                    entry_time = None
            
            equity_curve.append(current_capital)
        
        return trades, equity_curve
    
    def _generate_signal(
        self,
        df: pd.DataFrame,
        index: int,
        strategy: str,
        indicators: IndicatorConfig,
        current_position: Optional[str],
    ) -> tuple[str, str]:
        """Generate trading signal based on strategy."""
        current = df.iloc[index]
        prev = df.iloc[index - 1] if index > 0 else current
        
        # Default: no signal
        signal = 'HOLD'
        reason = ''
        
        if strategy == 'MA_Crossover':
            # EMA crossover strategy
            ema_short = current['ema_short']
            ema_medium = current['ema_medium']
            prev_short = prev['ema_short']
            prev_medium = prev['ema_medium']
            
            if prev_short <= prev_medium and ema_short > ema_medium:
                signal = 'BUY'
                reason = f'Golden cross: EMA{indicators.ema_short} crossed above EMA{indicators.ema_medium}'
            elif prev_short >= prev_medium and ema_short < ema_medium:
                signal = 'SELL'
                reason = f'Death cross: EMA{indicators.ema_short} crossed below EMA{indicators.ema_medium}'
        
        elif strategy == 'RSI_Divergence':
            rsi = current['rsi']
            if rsi < indicators.rsi_oversold:
                signal = 'BUY'
                reason = f'RSI oversold at {rsi:.1f}'
            elif rsi > indicators.rsi_overbought:
                signal = 'SELL'
                reason = f'RSI overbought at {rsi:.1f}'
        
        elif strategy == 'Supertrend_MACD':
            st_dir = current['supertrend_direction']
            macd = current['macd']
            macd_signal = current['macd_signal']
            
            if st_dir == 1 and macd > macd_signal:
                signal = 'BUY'
                reason = 'Supertrend bullish + MACD crossover'
            elif st_dir == -1 and macd < macd_signal:
                signal = 'SELL'
                reason = 'Supertrend bearish + MACD crossover'
        
        elif strategy == 'BB_Squeeze_Breakout':
            price = current['close']
            bb_upper = current['bb_upper']
            bb_lower = current['bb_lower']
            bb_bandwidth = current['bb_bandwidth']
            bb_bandwidth_ma = current['bb_bandwidth_ma']
            prev_price = prev['close']
            
            if bb_bandwidth < bb_bandwidth_ma:  # In squeeze
                if prev_price < bb_upper and price > bb_upper:
                    signal = 'BUY'
                    reason = 'BB squeeze breakout to upside'
                elif prev_price > bb_lower and price < bb_lower:
                    signal = 'SELL'
                    reason = 'BB squeeze breakout to downside'
        
        elif strategy == 'Momentum_VWAP_RSI':
            price = current['close']
            vwap = current.get('vwap', price)
            rsi = current['rsi']
            
            if price > vwap and rsi > 55:
                signal = 'BUY'
                reason = f'Price above VWAP with RSI {rsi:.1f}'
            elif price < vwap and rsi < 45:
                signal = 'SELL'
                reason = f'Price below VWAP with RSI {rsi:.1f}'
        
        elif strategy == 'EMA_Cross_RSI':
            ema_short = current['ema_short']
            ema_medium = current['ema_medium']
            rsi = current['rsi']
            price = current['close']
            
            if ema_short > ema_medium and rsi > 50 and price > ema_short:
                signal = 'BUY'
                reason = f'EMA crossover confirmed with RSI {rsi:.1f}'
            elif ema_short < ema_medium and rsi < 50 and price < ema_short:
                signal = 'SELL'
                reason = f'EMA crossover confirmed with RSI {rsi:.1f}'
        
        elif strategy == 'Volume_Spread_Analysis':
            volume = current['volume']
            volume_ma = current['volume_ma']
            spread = current['spread']
            is_high_volume = volume > volume_ma * 1.3
            is_up_candle = current['close'] > current['open']
            
            if is_high_volume and is_up_candle and spread > df['spread'].iloc[index-20:index].mean():
                signal = 'BUY'
                reason = 'High volume up bar with wide spread'
            elif is_high_volume and not is_up_candle and spread > df['spread'].iloc[index-20:index].mean():
                signal = 'SELL'
                reason = 'High volume down bar with wide spread'
        
        elif strategy == 'Volatility_Cluster_Reversal':
            atr = current['atr']
            atr_ma = current['atr_ma']
            is_high_volatility = atr > atr_ma
            candle_size = abs(current['open'] - current['close'])
            is_large_move = candle_size > atr * 1.5
            
            if is_high_volatility and is_large_move:
                if current['close'] < current['open']:  # Red candle after big move
                    signal = 'BUY'
                    reason = 'Volatility reversal after large down move'
                else:  # Green candle after big move
                    signal = 'SELL'
                    reason = 'Volatility reversal after large up move'
        
        elif strategy == 'Reversal_Detector':
            rsi = current['rsi']
            ema_short = current['ema_short']
            price = current['close']
            
            # Check for overextension
            price_change = (price / df['close'].iloc[index-20]) - 1
            
            if price_change > 0.05 and rsi > 70 and price < ema_short:
                signal = 'SELL'
                reason = 'Overextended uptrend with bearish reversal'
            elif price_change < -0.05 and rsi < 30 and price > ema_short:
                signal = 'BUY'
                reason = 'Overextended downtrend with bullish reversal'
        
        elif strategy in ['LSTM_Momentum', 'Funding_Rate']:
            # These require external data/models - use MA crossover as fallback
            ema_short = current['ema_short']
            ema_medium = current['ema_medium']
            rsi = current['rsi']
            
            if ema_short > ema_medium and 40 < rsi < 70:
                signal = 'BUY'
                reason = 'Trend following (simulated)'
            elif ema_short < ema_medium and 30 < rsi < 60:
                signal = 'SELL'
                reason = 'Trend following (simulated)'
        
        return signal, reason
    
    def _calculate_metrics(
        self,
        trades: List[TradeDetail],
        equity_curve: List[float],
        initial_capital: float,
        days: int,
    ) -> BacktestMetrics:
        """Calculate comprehensive backtest metrics."""
        if not trades:
            return BacktestMetrics(
                total_trades=0,
                total_pnl=0,
                total_return=0,
            )
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl < 0)
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = sum(t.pnl for t in trades)
        total_return = ((equity_curve[-1] / initial_capital) - 1) * 100
        
        # APY calculations
        if days > 0:
            simple_apy = ((1 + total_return / 100) ** (365 / days) - 1) * 100
        else:
            simple_apy = 0
        
        # Compound APY (geometric mean of returns)
        if len(equity_curve) > 1:
            daily_returns = []
            for i in range(1, len(equity_curve)):
                if equity_curve[i-1] > 0:
                    daily_returns.append(equity_curve[i] / equity_curve[i-1] - 1)
            
            if daily_returns:
                avg_return = np.mean(daily_returns)
                compound_apy = ((1 + avg_return) ** 365 - 1) * 100
            else:
                compound_apy = 0
        else:
            compound_apy = 0
        
        # Risk metrics
        returns = [t.pnl for t in trades]
        if len(returns) > 1:
            returns_std = np.std(returns)
            avg_return = np.mean(returns)
            sharpe_ratio = (avg_return / returns_std) * np.sqrt(252) if returns_std > 0 else 0
            
            # Sortino (only negative returns for denominator)
            neg_returns = [r for r in returns if r < 0]
            if neg_returns:
                downside_std = np.std(neg_returns)
                sortino_ratio = (avg_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0
            else:
                sortino_ratio = sharpe_ratio
        else:
            sharpe_ratio = 0
            sortino_ratio = 0
        
        # Drawdown
        peak = initial_capital
        max_dd = 0
        max_dd_pct = 0
        for eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = peak - eq
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
        
        # Trade quality
        wins = [t.pnl for t in trades if t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl < 0]
        
        average_win = np.mean(wins) if wins else 0
        average_loss = abs(np.mean(losses)) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = abs(min(losses)) if losses else 0
        
        gross_profit = sum(wins) if wins else 0
        gross_loss = abs(sum(losses)) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        # Trade duration
        durations = [t.duration_minutes for t in trades]
        avg_duration = np.mean(durations) if durations else 0
        
        # Fees
        total_fees = sum(t.fees for t in trades)
        
        # Consecutive wins/losses
        max_consec_wins = 0
        max_consec_losses = 0
        current_wins = 0
        current_losses = 0
        
        for t in trades:
            if t.pnl > 0:
                current_wins += 1
                current_losses = 0
                max_consec_wins = max(max_consec_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_consec_losses = max(max_consec_losses, current_losses)
        
        # Expectancy
        loss_rate = 1 - (win_rate / 100)
        expectancy = (win_rate / 100 * average_win) - (loss_rate * average_loss)
        
        # Daily P&L for best/worst day
        daily_pnl = defaultdict(float)
        for t in trades:
            day = t.exit_time.strftime('%Y-%m-%d')
            daily_pnl[day] += t.pnl
        
        best_day = max(daily_pnl.values()) if daily_pnl else 0
        worst_day = min(daily_pnl.values()) if daily_pnl else 0
        
        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            total_pnl=round(total_pnl, 2),
            total_return=round(total_return, 2),
            simple_apy=round(simple_apy, 2),
            compound_apy=round(compound_apy, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            sortino_ratio=round(sortino_ratio, 2),
            max_drawdown=round(max_dd, 2),
            max_drawdown_percent=round(max_dd_pct, 2),
            profit_factor=round(profit_factor, 2) if profit_factor != float('inf') else 999.99,
            average_win=round(average_win, 2),
            average_loss=round(average_loss, 2),
            largest_win=round(largest_win, 2),
            largest_loss=round(largest_loss, 2),
            average_trade_duration_minutes=round(avg_duration, 2),
            total_fees=round(total_fees, 2),
            total_slippage=0,  # Already included in trade P&L
            best_day=round(best_day, 2),
            worst_day=round(worst_day, 2),
            max_consecutive_wins=max_consec_wins,
            max_consecutive_losses=max_consec_losses,
            expectancy=round(expectancy, 2),
        )
    
    def _calculate_daily_returns(
        self,
        trades: List[TradeDetail],
        df: pd.DataFrame,
    ) -> List[DailyReturn]:
        """Calculate daily returns from trades."""
        daily_pnl = defaultdict(lambda: {'pnl': 0, 'trades': 0})
        
        for t in trades:
            day = t.exit_time.strftime('%Y-%m-%d')
            daily_pnl[day]['pnl'] += t.pnl
            daily_pnl[day]['trades'] += 1
        
        # Fill in missing days
        if not df.empty:
            start = df.index[0].date()
            end = df.index[-1].date()
            current = start
            while current <= end:
                day_str = current.strftime('%Y-%m-%d')
                if day_str not in daily_pnl:
                    daily_pnl[day_str] = {'pnl': 0, 'trades': 0}
                current += timedelta(days=1)
        
        # Calculate running capital for return percentages
        result = []
        running_capital = 10000  # Will be adjusted based on actual initial capital
        
        for day in sorted(daily_pnl.keys()):
            data = daily_pnl[day]
            return_pct = (data['pnl'] / running_capital) * 100 if running_capital > 0 else 0
            running_capital += data['pnl']
            
            result.append(DailyReturn(
                date=day,
                pnl=round(data['pnl'], 2),
                return_percent=round(return_pct, 2),
                trades=data['trades'],
            ))
        
        return result
    
    def _calculate_monthly_returns(
        self,
        daily_returns: List[DailyReturn],
    ) -> List[MonthlyReturn]:
        """Aggregate daily returns into monthly returns."""
        monthly_pnl = defaultdict(lambda: {'pnl': 0, 'trades': 0})
        
        for day in daily_returns:
            month = day.date[:7]  # YYYY-MM
            monthly_pnl[month]['pnl'] += day.pnl
            monthly_pnl[month]['trades'] += day.trades
        
        result = []
        running_capital = 10000
        
        for month in sorted(monthly_pnl.keys()):
            data = monthly_pnl[month]
            return_pct = (data['pnl'] / running_capital) * 100 if running_capital > 0 else 0
            running_capital += data['pnl']
            
            result.append(MonthlyReturn(
                month=month,
                pnl=round(data['pnl'], 2),
                return_percent=round(return_pct, 2),
                trades=data['trades'],
            ))
        
        return result
    
    def _build_equity_curve_points(
        self,
        equity_curve: List[float],
        df: pd.DataFrame,
    ) -> List[EquityCurvePoint]:
        """Build equity curve points with timestamps and drawdown."""
        if df.empty or not equity_curve:
            return []
        
        # Sample equity curve to avoid too many points
        max_points = 500
        step = max(1, len(equity_curve) // max_points)
        
        result = []
        peak = equity_curve[0]
        
        # Match equity curve to dataframe timestamps
        timestamps = list(df.index)
        
        for i in range(0, min(len(equity_curve), len(timestamps)), step):
            eq = equity_curve[i]
            ts = timestamps[i]
            
            if eq > peak:
                peak = eq
            
            dd = peak - eq
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            
            result.append(EquityCurvePoint(
                timestamp=ts,
                equity=round(eq, 2),
                drawdown=round(dd, 2),
                drawdown_percent=round(dd_pct, 2),
            ))
        
        return result
    
    async def close(self):
        """Close the httpx client."""
        if self.client and not self.client.is_closed:
            await self.client.aclose()

