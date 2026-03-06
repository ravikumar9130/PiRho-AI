"""
Trading Strategies for Bybit USDT Perpetual Futures
Adapted from NIFTY strategies + LSTM integration for crypto markets
"""

import logging
import pandas as pd
try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    ta = None
    HAS_PANDAS_TA = False
import numpy as np

try:
    import torch
    HAS_TORCH = True
except ImportError:
    torch = None
    HAS_TORCH = False

from typing import Optional, Dict, Any
from datetime import datetime

from indicators import (
    calculate_rsi, check_rsi_divergence, 
    calculate_ema, check_momentum_divergence, 
    is_trend_overextended
)

logger = logging.getLogger(__name__)


class BaseStrategy:
    """Base class for all trading strategies."""
    
    def __init__(self, config: dict):
        """
        Initialize base strategy.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.name = "Base"
        self.is_reversal_trade = False
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Generate trading signal.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            sentiment: Market sentiment (Bullish, Bearish, Neutral, etc.)
            index: Candle index to analyze (defaults to latest)
            
        Returns:
            Tuple of (signal, reason, context):
            - signal: "BUY", "SELL", or "HOLD"
            - reason: Human-readable reason for the signal
            - context: Dictionary with strategy-specific context data
        """
        raise NotImplementedError
    
    def get_status_message(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        **kwargs
    ) -> str:
        """
        Get human-readable status message.
        
        Args:
            df: DataFrame with OHLCV data
            sentiment: Market sentiment
            
        Returns:
            Status message string
        """
        return f"Awaiting signal: {self.name} strategy monitoring market."


class LSTM_Momentum_Strategy(BaseStrategy):
    """
    Enhanced LSTM-based momentum strategy using LSTMModelManager.
    Supports per-symbol models with dynamic loading and auto-training.
    Uses advanced features: direction probability + magnitude prediction with attention mechanism.
    """
    
    def __init__(self, config: dict, lstm_manager=None):
        super().__init__(config)
        self.name = "LSTM_Momentum"
        self.lstm_manager = lstm_manager
        self.current_symbol = None
        ai_config = config.get('ai', {})
        self.sequence_length = ai_config.get('lstm_sequence_length', 30)
        self.confidence_threshold = ai_config.get('lstm_confidence_threshold', 0.65)
        
    def set_lstm_manager(self, lstm_manager, symbol: str):
        """
        Set the LSTM model manager and current symbol.
        
        Args:
            lstm_manager: LSTMModelManager instance
            symbol: Current trading symbol
        """
        self.lstm_manager = lstm_manager
        self.current_symbol = symbol
        if self.lstm_manager:
            logger.info(f"[{self.name}] LSTM manager set for symbol: {symbol}")
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        """
        Generate trading signals using LSTM predictions.
        
        Args:
            df: DataFrame with OHLCV data and indicators
            sentiment: Market sentiment
            index: Candle index (unused, uses latest)
            **kwargs: Additional args (symbol can be passed here)
            
        Returns:
            Tuple of (signal, reason, context)
        """
        # Get symbol from kwargs or use current
        symbol = kwargs.get('symbol', self.current_symbol)
        if not symbol:
            logger.warning(f"[{self.name}] No symbol specified, returning HOLD")
            return ('HOLD', 'No symbol specified', {})
        
        if not HAS_TORCH or self.lstm_manager is None:
            logger.warning(f"[{self.name}] LSTM manager not available, returning HOLD")
            return ('HOLD', 'LSTM manager not available', {})
        
        if len(df) < self.sequence_length:
            logger.debug(f"[{self.name}] Not enough data: {len(df)} < {self.sequence_length}")
            return ('HOLD', f'Insufficient data: {len(df)} < {self.sequence_length}', {})
        
        try:
            # Use LSTMModelManager to get prediction
            direction_prob, magnitude, signal = self.lstm_manager.predict(symbol, df)
            
            # Technical confirmation with RSI
            current = df.iloc[-1]
            rsi = current.get('rsi', 50)
            
            context = {
                'direction_probability': float(direction_prob),
                'magnitude': float(magnitude),
                'rsi': float(rsi),
                'sentiment': sentiment,
            }
            
            # Enhanced signal logic with magnitude consideration
            # Strong BUY: High up probability + reasonable RSI + positive magnitude
            if (direction_prob > self.confidence_threshold and 
                rsi > 40 and rsi < 75 and 
                magnitude > -0.5):  # Not predicting large drop
                if sentiment in ['Bullish', 'Very Bullish', 'Neutral']:
                    reason = (
                        f"LSTM predicts {direction_prob:.1%} up probability, "
                        f"magnitude {magnitude:+.2f}%, RSI {rsi:.1f}, "
                        f"sentiment {sentiment}"
                    )
                    logger.info(
                        f"[{self.name}] BUY signal: "
                        f"Direction={direction_prob:.2%}, Magnitude={magnitude:+.2f}%, "
                        f"RSI={rsi:.1f}, Sentiment={sentiment}"
                    )
                    return ('BUY', reason, context)
            
            # Strong SELL: Low up probability + reasonable RSI + negative magnitude
            if (direction_prob < (1 - self.confidence_threshold) and 
                rsi < 60 and rsi > 25 and 
                magnitude < 0.5):  # Not predicting large rise
                if sentiment in ['Bearish', 'Very Bearish', 'Neutral']:
                    reason = (
                        f"LSTM predicts {direction_prob:.1%} up probability, "
                        f"magnitude {magnitude:+.2f}%, RSI {rsi:.1f}, "
                        f"sentiment {sentiment}"
                    )
                    logger.info(
                        f"[{self.name}] SELL signal: "
                        f"Direction={direction_prob:.2%}, Magnitude={magnitude:+.2f}%, "
                        f"RSI={rsi:.1f}, Sentiment={sentiment}"
                    )
                    return ('SELL', reason, context)
            
            # Log when we have prediction but conditions not met
            reason = (
                f"LSTM prediction: {direction_prob:.1%} up, {magnitude:+.2f}% magnitude, "
                f"RSI {rsi:.1f} - conditions not met for signal"
            )
            logger.debug(
                f"[{self.name}] HOLD: Direction={direction_prob:.2%}, "
                f"Magnitude={magnitude:+.2f}%, RSI={rsi:.1f}"
            )
            
            return ('HOLD', reason, context)
            
        except Exception as e:
            logger.error(f"[{self.name}] Prediction error for {symbol}: {e}", exc_info=True)
            return ('HOLD', f'Prediction error: {str(e)}', {})
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        """Get status message with current prediction info."""
        if not HAS_TORCH:
            return f"[{self.name}] PyTorch not available. Using fallback strategies."
        
        if self.lstm_manager is None:
            return f"[{self.name}] Waiting for LSTM manager to be initialized."
        
        symbol = kwargs.get('symbol', self.current_symbol)
        if not symbol:
            return f"[{self.name}] No symbol set. Waiting for symbol assignment."
        
        # Check if model exists
        if not self.lstm_manager.model_exists(symbol):
            return f"[{self.name}] Model for {symbol} not found. Auto-training may be in progress."
        
        # Try to get a prediction for status
        try:
            if len(df) >= self.sequence_length:
                direction_prob, magnitude, _ = self.lstm_manager.predict(symbol, df)
                return (
                    f"[{self.name}] {symbol}: Direction={direction_prob:.1%}, "
                    f"Magnitude={magnitude:+.2f}%, Confidence threshold: {self.confidence_threshold:.0%}"
                )
        except:
            pass
        
        return f"[{self.name}] Analyzing {symbol} with enhanced LSTM model. Confidence: {self.confidence_threshold:.0%}"


class Supertrend_MACD_Strategy(BaseStrategy):
    """Trend-following strategy using Supertrend and MACD."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Supertrend_MACD"
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 1:
            return ('HOLD', 'Insufficient data', {})
        
        # Calculate Supertrend if not present
        if 'supertrend_direction' not in df.columns:
            if HAS_PANDAS_TA and ta is not None:
                supertrend = ta.supertrend(df['high'], df['low'], df['close'])
                if supertrend is not None and not supertrend.empty:
                    df['supertrend_direction'] = supertrend.get('SUPERTd_7_3.0')
            else:
                # Fallback: use EMA trend
                ema_21 = calculate_ema(df['close'], 21)
                df['supertrend_direction'] = np.where(df['close'] > ema_21, 1, -1)
        
        # Calculate MACD if not present
        if 'macd' not in df.columns:
            from indicators import calculate_macd
            macd_line, signal_line, _ = calculate_macd(df['close'])
            df['macd'] = macd_line
            df['macd_signal'] = signal_line
        
        current = df.iloc[index]
        
        supertrend_dir = current.get('supertrend_direction', 0)
        macd = current.get('macd', 0)
        macd_signal = current.get('macd_signal', 0)
        
        context = {
            'supertrend_direction': int(supertrend_dir),
            'macd': float(macd),
            'macd_signal': float(macd_signal),
            'sentiment': sentiment,
        }
        
        is_bullish = (supertrend_dir == 1 and macd > macd_signal)
        is_bearish = (supertrend_dir == -1 and macd < macd_signal)
        
        if is_bullish:
            reason = "Supertrend bullish + MACD crossover"
            logger.info(f"[{self.name}] BUY signal: {reason}")
            return ('BUY', reason, context)
        if is_bearish:
            reason = "Supertrend bearish + MACD crossover"
            logger.info(f"[{self.name}] SELL signal: {reason}")
            return ('SELL', reason, context)
        
        return ('HOLD', 'Awaiting Supertrend direction + MACD crossover confirmation', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        return f"[{self.name}] Awaiting Supertrend direction + MACD crossover confirmation."


class VolatilityClusterStrategy(BaseStrategy):
    """Reversal strategy based on volatility clustering and large candle moves."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Volatility_Cluster_Reversal"
        self.is_reversal_trade = True
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 20:
            return ('HOLD', 'Insufficient data (need 20 candles)', {})
        
        # Calculate ATR if not present
        if 'atr' not in df.columns:
            from indicators import calculate_atr
            df['atr'] = calculate_atr(df['high'], df['low'], df['close'], 14)
        if 'atr_ma' not in df.columns:
            df['atr_ma'] = df['atr'].rolling(window=20).mean()
        
        last_candle = df.iloc[index - 1]
        
        if pd.isna(last_candle['atr']) or pd.isna(last_candle['atr_ma']):
            return ('HOLD', 'ATR data not available', {})
        
        atr = float(last_candle['atr'])
        atr_ma = float(last_candle['atr_ma'])
        is_high_volatility = atr > atr_ma
        avg_candle_size = df['atr'].iloc[index - 1]
        last_candle_size = abs(last_candle['open'] - last_candle['close'])
        is_large_move = last_candle_size > (avg_candle_size * 1.5)
        
        context = {
            'atr': atr,
            'atr_ma': atr_ma,
            'candle_size': float(last_candle_size),
            'sentiment': sentiment,
        }
        
        # Look for reversal after large move
        if sentiment in ['Bullish', 'Very Bullish']:
            is_reversal_candle = last_candle['close'] < last_candle['open']  # Red candle
            if is_high_volatility and is_large_move and is_reversal_candle:
                reason = "High volatility reversal: Large down move with high ATR"
                logger.info(f"[{self.name}] Reversal BUY: {reason}")
                return ('BUY', reason, context)
                
        elif sentiment in ['Bearish', 'Very Bearish']:
            is_reversal_candle = last_candle['close'] > last_candle['open']  # Green candle
            if is_high_volatility and is_large_move and is_reversal_candle:
                reason = "High volatility reversal: Large up move with high ATR"
                logger.info(f"[{self.name}] Reversal SELL: {reason}")
                return ('SELL', reason, context)
        
        return ('HOLD', 'Monitoring for high volatility reversal opportunities', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        return f"[{self.name}] Monitoring for high volatility reversal opportunities."


class VSA_Strategy(BaseStrategy):
    """Volume Spread Analysis strategy for detecting smart money activity."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Volume_Spread_Analysis"
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 20:
            return ('HOLD', 'Insufficient data (need 20 candles)', {})
        
        # Calculate volume MA if not present
        if 'volume_ma' not in df.columns:
            df['volume_ma'] = df['volume'].rolling(window=20).mean()
        if 'spread' not in df.columns:
            df['spread'] = df['high'] - df['low']
        
        last_candle = df.iloc[index - 1]
        
        volume = float(last_candle.get('volume', 0))
        volume_ma = float(last_candle.get('volume_ma', 0))
        is_high_volume = volume > (volume_ma * 1.3)
        spread_ma = df['spread'].rolling(window=20).mean().iloc[index - 1]
        spread = float(last_candle.get('spread', 0))
        is_wide_spread = spread > spread_ma
        
        context = {
            'volume': volume,
            'volume_ma': volume_ma,
            'spread': spread,
            'spread_ma': float(spread_ma),
            'sentiment': sentiment,
        }
        
        if sentiment in ['Bullish', 'Very Bullish']:
            is_down_bar = last_candle['close'] < last_candle['open']
            is_high_close = last_candle['close'] > (last_candle['low'] + last_candle['spread'] * 0.5)
            if is_down_bar and is_high_volume and is_wide_spread and is_high_close:
                reason = "Sign of Strength: High volume down bar with wide spread, closing high"
                logger.info(f"[{self.name}] {reason} - BUY signal")
                return ('BUY', reason, context)
        
        if sentiment in ['Bearish', 'Very Bearish']:
            is_up_bar = last_candle['close'] > last_candle['open']
            is_low_close = last_candle['close'] < (last_candle['low'] + last_candle['spread'] * 0.5)
            if is_up_bar and is_high_volume and is_wide_spread and is_low_close:
                reason = "Sign of Weakness: High volume up bar with wide spread, closing low"
                logger.info(f"[{self.name}] {reason} - SELL signal")
                return ('SELL', reason, context)
        
        return ('HOLD', 'Monitoring for smart money activity (VSA patterns)', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        return f"[{self.name}] Analyzing volume and spread for smart money signals."


class Momentum_VWAP_RSI_Strategy(BaseStrategy):
    """Momentum strategy using VWAP and RSI."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Momentum_VWAP_RSI"
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 1:
            return ('HOLD', 'Insufficient data', {})
        
        # Calculate VWAP if not present
        if 'vwap' not in df.columns:
            from indicators import calculate_vwap
            df['vwap'] = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
        
        current = df.iloc[index]
        price = float(current['close'])
        vwap = float(current.get('vwap', price))
        rsi = float(current.get('rsi', 50))
        
        context = {
            'price': price,
            'vwap': vwap,
            'rsi': rsi,
            'sentiment': sentiment,
        }
        
        if sentiment in ['Bullish', 'Very Bullish']:
            if price > vwap and rsi > 55:
                reason = f"Price above VWAP ({vwap:.2f}) with RSI {rsi:.1f} > 55"
                logger.info(f"[{self.name}] BUY: {reason}")
                return ('BUY', reason, context)
                
        if sentiment in ['Bearish', 'Very Bearish']:
            if price < vwap and rsi < 45:
                reason = f"Price below VWAP ({vwap:.2f}) with RSI {rsi:.1f} < 45"
                logger.info(f"[{self.name}] SELL: {reason}")
                return ('SELL', reason, context)
        
        return ('HOLD', f'Awaiting VWAP ({vwap:.2f}) + RSI confirmation', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        vwap = df.iloc[-1].get('vwap', 0)
        return f"[{self.name}] Awaiting VWAP ({vwap:.2f}) + RSI confirmation."


class Bollinger_Band_Squeeze_Strategy(BaseStrategy):
    """Volatility breakout strategy using Bollinger Band squeeze."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "BB_Squeeze_Breakout"
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 1:
            return ('HOLD', 'Insufficient data', {})
        
        # Calculate Bollinger Bands if not present
        if 'bb_upper' not in df.columns:
            from indicators import calculate_bollinger_bands
            bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(df['close'], 20, 2.0)
            df['bb_upper'] = bb_upper
            df['bb_lower'] = bb_lower
            df['bb_mid'] = bb_mid
            df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
            df['bb_bandwidth_ma'] = df['bb_bandwidth'].rolling(window=20).mean()
        
        current, last = df.iloc[index], df.iloc[index - 1]
        
        bb_upper = float(current.get('bb_upper', 0))
        bb_lower = float(current.get('bb_lower', float('inf')))
        bb_bandwidth = float(current.get('bb_bandwidth', 1))
        bb_bandwidth_ma = float(current.get('bb_bandwidth_ma', 0.5))
        price = float(current['close'])
        last_price = float(last['close'])
        
        context = {
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'bb_bandwidth': bb_bandwidth,
            'bb_bandwidth_ma': bb_bandwidth_ma,
            'price': price,
            'sentiment': sentiment,
        }
        
        # Check if in squeeze
        if bb_bandwidth < bb_bandwidth_ma:
            if sentiment in ['Bullish', 'Very Bullish']:
                if last_price < bb_upper and price > bb_upper:
                    reason = "Bollinger Band squeeze breakout to upside"
                    logger.info(f"[{self.name}] BUY: {reason}")
                    return ('BUY', reason, context)
                    
            if sentiment in ['Bearish', 'Very Bearish']:
                if last_price > bb_lower and price < bb_lower:
                    reason = "Bollinger Band squeeze breakout to downside"
                    logger.info(f"[{self.name}] SELL: {reason}")
                    return ('SELL', reason, context)
        
        return ('HOLD', 'Waiting for Bollinger Bands squeeze and breakout', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        current = df.iloc[-1]
        if current.get('bb_bandwidth', 1) > current.get('bb_bandwidth_ma', 0.5):
            return f"[{self.name}] Waiting for Bollinger Bands to tighten into a squeeze."
        return f"[{self.name}] In squeeze. Awaiting breakout."


class MA_Crossover_Strategy(BaseStrategy):
    """
    Moving average crossover strategy with trend-following logic.
    
    Generates signals based on EMA 9/21 crossovers AND current trend direction.
    Works in both Neutral and aligned sentiment conditions.
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "MA_Crossover"
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < 1:
            return ('HOLD', 'Insufficient data', {})
        
        # Calculate EMAs if not present
        if 'ema_9' not in df.columns:
            df['ema_9'] = calculate_ema(df['close'], 9)
        if 'ema_21' not in df.columns:
            df['ema_21'] = calculate_ema(df['close'], 21)
        
        current, last = df.iloc[index], df.iloc[index - 1]
        ema9 = float(current['ema_9'])
        ema21 = float(current['ema_21'])
        last_ema9 = float(last['ema_9'])
        last_ema21 = float(last['ema_21'])
        rsi = float(current.get('rsi', 50))
        price = float(current['close'])
        
        # Check for crossover events
        golden_cross = last_ema9 <= last_ema21 and ema9 > ema21
        death_cross = last_ema9 >= last_ema21 and ema9 < ema21
        
        # Also check current trend (not just crossover)
        is_bullish_trend = ema9 > ema21
        is_bearish_trend = ema9 < ema21
        
        # Check for momentum confirmation
        price_above_ema9 = price > ema9
        price_below_ema9 = price < ema9
        
        context = {
            'ema_9': ema9,
            'ema_21': ema21,
            'rsi': rsi,
            'price': price,
            'sentiment': sentiment,
            'golden_cross': golden_cross,
            'death_cross': death_cross,
        }
        
        # BUY conditions: Allow in Neutral, Bullish, or Very Bullish sentiment
        # Also allow in Bearish if there's a clear reversal signal
        if sentiment in ['Bullish', 'Very Bullish', 'Neutral']:
            # Strong signal: Golden cross just occurred
            if golden_cross:
                reason = f"Golden cross: EMA9 ({ema9:.2f}) crossed above EMA21 ({ema21:.2f}), RSI {rsi:.1f}"
                logger.info(f"[{self.name}] BUY: {reason}, Sentiment={sentiment}")
                return ('BUY', reason, context)
            
            # Trend continuation: Already in bullish trend + price pullback to EMA9
            if is_bullish_trend and price_above_ema9 and 40 < rsi < 70:
                # Only signal on momentum pickup after pullback
                if last['close'] < last['ema_9'] and price > ema9:
                    reason = f"Pullback bounce: Price reclaimed EMA9 in uptrend, RSI {rsi:.1f}"
                    logger.info(f"[{self.name}] BUY: {reason}")
                    return ('BUY', reason, context)
        
        # Even in Bearish sentiment, allow BUY on strong reversal (golden cross + oversold)
        elif sentiment in ['Bearish', 'Very Bearish']:
            if golden_cross and rsi < 40:
                reason = f"Reversal golden cross in bearish sentiment, RSI {rsi:.1f} (oversold)"
                logger.info(f"[{self.name}] BUY: {reason}")
                return ('BUY', reason, context)
        
        # SELL conditions: Allow in Neutral, Bearish, or Very Bearish sentiment
        if sentiment in ['Bearish', 'Very Bearish', 'Neutral']:
            # Strong signal: Death cross just occurred
            if death_cross:
                reason = f"Death cross: EMA9 ({ema9:.2f}) crossed below EMA21 ({ema21:.2f}), RSI {rsi:.1f}"
                logger.info(f"[{self.name}] SELL: {reason}, Sentiment={sentiment}")
                return ('SELL', reason, context)
            
            # Trend continuation: Already in bearish trend + price rally to EMA9
            if is_bearish_trend and price_below_ema9 and 30 < rsi < 60:
                # Only signal on momentum breakdown after rally
                if last['close'] > last['ema_9'] and price < ema9:
                    reason = f"Rally rejection: Price lost EMA9 in downtrend, RSI {rsi:.1f}"
                    logger.info(f"[{self.name}] SELL: {reason}")
                    return ('SELL', reason, context)
        
        # Even in Bullish sentiment, allow SELL on strong reversal (death cross + overbought)
        elif sentiment in ['Bullish', 'Very Bullish']:
            if death_cross and rsi > 60:
                reason = f"Reversal death cross in bullish sentiment, RSI {rsi:.1f} (overbought)"
                logger.info(f"[{self.name}] SELL: {reason}")
                return ('SELL', reason, context)
        
        # Log why we're holding (only every few iterations to avoid spam)
        reason = f"EMA9={ema9:.2f}, EMA21={ema21:.2f}, RSI={rsi:.1f}, Trend={'bullish' if is_bullish_trend else 'bearish'}"
        logger.debug(
            f"[{self.name}] HOLD: {reason}, Sentiment={sentiment}, "
            f"Cross={'golden' if golden_cross else 'death' if death_cross else 'none'}"
        )
        
        return ('HOLD', f'Awaiting EMA crossover or trend continuation, {reason}', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        current = df.iloc[-1]
        ema9 = current.get('ema_9', 0)
        ema21 = current.get('ema_21', 0)
        trend = "bullish" if ema9 > ema21 else "bearish"
        return f"[{self.name}] Trend: {trend}, EMA9={ema9:.2f}, EMA21={ema21:.2f}. Awaiting signal."


class RSI_Divergence_Strategy(BaseStrategy):
    """Pure reversal strategy based on RSI divergence."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "RSI_Divergence"
        self.is_reversal_trade = True
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        
        # Calculate RSI if not present
        if 'rsi' not in df.columns:
            df['rsi'] = calculate_rsi(df['close'], 14)
        
        current = df.iloc[index]
        rsi = float(current.get('rsi', 50))
        price = float(current['close'])
        
        divergence = check_rsi_divergence(df.iloc[:index + 1], df['rsi'].iloc[:index + 1])
        
        context = {
            'rsi': rsi,
            'price': price,
            'divergence': divergence,
            'sentiment': sentiment,
        }
        
        if sentiment in ['Bullish', 'Very Bullish'] and divergence == 'Bullish':
            reason = "Bullish RSI divergence: Price making lower low, RSI making higher low"
            logger.info(f"[{self.name}] BUY: {reason}")
            return ('BUY', reason, context)
            
        if sentiment in ['Bearish', 'Very Bearish'] and divergence == 'Bearish':
            reason = "Bearish RSI divergence: Price making higher high, RSI making lower high"
            logger.info(f"[{self.name}] SELL: {reason}")
            return ('SELL', reason, context)
        
        return ('HOLD', f'Monitoring for RSI divergence, current RSI {rsi:.1f}', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        if sentiment in ['Bullish', 'Very Bullish']:
            return f"[{self.name}] Looking for bullish divergence (price lower low, RSI higher low)."
        return f"[{self.name}] Looking for bearish divergence (price higher high, RSI lower high)."


class EMA_Cross_RSI_Strategy(BaseStrategy):
    """EMA crossover with RSI confirmation."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "EMA_Cross_RSI"
        self.lookback = config.get('trading_flags', {}).get('ema_cross_lookback', 5)
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if index is None:
            index = len(df) - 1
        if index < self.lookback + 1:
            return ('HOLD', f'Insufficient data (need {self.lookback + 1} candles)', {})
        
        # Calculate indicators if not present
        if 'ema_9' not in df.columns:
            df['ema_9'] = calculate_ema(df['close'], 9)
        if 'ema_15' not in df.columns:
            df['ema_15'] = calculate_ema(df['close'], 15)
        if 'rsi' not in df.columns:
            df['rsi'] = calculate_rsi(df['close'], 14)
        
        current = df.iloc[index]
        ema9 = float(current['ema_9'])
        ema15 = float(current['ema_15'])
        rsi = float(current.get('rsi', 50))
        price = float(current['close'])
        
        context = {
            'ema_9': ema9,
            'ema_15': ema15,
            'rsi': rsi,
            'price': price,
            'sentiment': sentiment,
        }
        
        # Bullish setup
        is_trending_up = ema9 > ema15
        is_confirmed_up = rsi > 50 and price > ema9
        
        if is_trending_up and is_confirmed_up:
            # Check for recent golden cross
            for i in range(index - self.lookback, index + 1):
                prev = df.iloc[i - 1]
                curr = df.iloc[i]
                if prev['ema_9'] < prev['ema_15'] and curr['ema_9'] > curr['ema_15']:
                    reason = f"EMA9/15 golden cross with RSI {rsi:.1f} > 50 and price above EMA9"
                    logger.info(f"[{self.name}] BUY: {reason}")
                    return ('BUY', reason, context)
        
        # Bearish setup
        is_trending_down = ema9 < ema15
        is_confirmed_down = rsi < 50 and price < ema9
        
        if is_trending_down and is_confirmed_down:
            # Check for recent death cross
            for i in range(index - self.lookback, index + 1):
                prev = df.iloc[i - 1]
                curr = df.iloc[i]
                if prev['ema_9'] > prev['ema_15'] and curr['ema_9'] < curr['ema_15']:
                    reason = f"EMA9/15 death cross with RSI {rsi:.1f} < 50 and price below EMA9"
                    logger.info(f"[{self.name}] SELL: {reason}")
                    return ('SELL', reason, context)
        
        return ('HOLD', f'Awaiting EMA9/15 crossover with RSI confirmation, RSI {rsi:.1f}', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        return f"[{self.name}] Awaiting 9/15 EMA crossover with RSI confirmation."


class Reversal_Detector_Strategy(BaseStrategy):
    """
    Reversal strategy detecting overextended trends with momentum divergence.
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Reversal_Detector"
        self.is_reversal_trade = True
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        # Calculate RSI if not present
        if 'rsi' not in df.columns:
            df['rsi'] = calculate_rsi(df['close'], 14)
        if 'ema_9' not in df.columns:
            df['ema_9'] = calculate_ema(df['close'], 9)
        
        trend_status = is_trend_overextended(df)
        if trend_status == "None":
            return ('HOLD', 'No overextended trend detected', {})
        
        rsi_divergence = check_momentum_divergence(df['close'], df['rsi'])
        current = df.iloc[-1]
        rsi = float(current.get('rsi', 50))
        price = float(current['close'])
        ema9 = float(current.get('ema_9', price))
        
        context = {
            'trend_status': trend_status,
            'rsi_divergence': rsi_divergence,
            'rsi': rsi,
            'price': price,
            'ema_9': ema9,
            'sentiment': sentiment,
        }
        
        # Bearish reversal
        if trend_status == "Uptrend" and rsi_divergence == "Bearish":
            if price < ema9:
                reason = f"Overextended uptrend with bearish momentum divergence, price below EMA9"
                logger.info(f"[{self.name}] SELL: {reason}")
                return ('SELL', reason, context)
        
        # Bullish reversal
        if trend_status == "Downtrend" and rsi_divergence == "Bullish":
            if price > ema9:
                reason = f"Overextended downtrend with bullish momentum divergence, price above EMA9"
                logger.info(f"[{self.name}] BUY: {reason}")
                return ('BUY', reason, context)
        
        return ('HOLD', f'Monitoring {trend_status.lower()} for reversal signals', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        trend = is_trend_overextended(df) if not df.empty else "None"
        if trend == "Uptrend":
            return f"[{self.name}] Overextended uptrend detected. Looking for bearish divergence."
        if trend == "Downtrend":
            return f"[{self.name}] Overextended downtrend detected. Looking for bullish divergence."
        return f"[{self.name}] Waiting for overextended trend to form."


class Funding_Rate_Strategy(BaseStrategy):
    """
    Crypto-specific strategy based on funding rate and market imbalance.
    
    High positive funding = too many longs = potential for short
    High negative funding = too many shorts = potential for long
    
    Uses multiple tiers of confirmation:
    - Tier 1 (Strong): Extreme funding + extreme RSI
    - Tier 2 (Normal): Moderate funding + moderate RSI
    - Tier 3 (Trend): Moderate funding + trend alignment
    """
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.name = "Funding_Rate"
        self.is_reversal_trade = True
        # Funding rate thresholds (8h funding rate)
        self.extreme_funding_threshold = 0.0005  # 0.05% - very extreme
        self.high_funding_threshold = 0.0003     # 0.03% - elevated
        self.moderate_funding_threshold = 0.0001 # 0.01% - notable
        
    def generate_signals(
        self, 
        df: pd.DataFrame, 
        sentiment: str = "Neutral",
        index: Optional[int] = None,
        funding_rate: Optional[float] = None,
        **kwargs
    ) -> tuple[str, str, Dict[str, Any]]:
        if funding_rate is None:
            logger.debug(f"[{self.name}] HOLD: No funding rate data available")
            return ('HOLD', 'No funding rate data available', {})
        
        # Calculate RSI for confirmation
        if 'rsi' not in df.columns:
            df['rsi'] = calculate_rsi(df['close'], 14)
        if 'ema_9' not in df.columns:
            df['ema_9'] = calculate_ema(df['close'], 9)
        if 'ema_21' not in df.columns:
            df['ema_21'] = calculate_ema(df['close'], 21)
        
        current = df.iloc[-1]
        rsi = float(current.get('rsi', 50))
        ema9 = float(current.get('ema_9', 0))
        ema21 = float(current.get('ema_21', 0))
        price = float(current['close'])
        
        # Trend direction
        is_downtrend = ema9 < ema21
        is_uptrend = ema9 > ema21
        
        # Price action
        price_falling = price < ema9
        price_rising = price > ema9
        
        context = {
            'funding_rate': float(funding_rate),
            'rsi': rsi,
            'ema_9': ema9,
            'ema_21': ema21,
            'price': price,
            'sentiment': sentiment,
            'trend': 'downtrend' if is_downtrend else 'uptrend' if is_uptrend else 'neutral',
        }
        
        # ========== SELL SIGNALS (Short) ==========
        # Tier 1: Extreme positive funding + overbought
        if funding_rate > self.extreme_funding_threshold and rsi > 65:
            reason = f"Extreme funding rate {funding_rate:.4%} (too many longs) + overbought RSI {rsi:.1f}"
            logger.info(f"[{self.name}] SELL (Tier 1): {reason}")
            return ('SELL', reason, context)
        
        # Tier 2: High positive funding + moderately overbought
        if funding_rate > self.high_funding_threshold and rsi > 55:
            reason = f"High funding rate {funding_rate:.4%} (many longs) + elevated RSI {rsi:.1f}"
            logger.info(f"[{self.name}] SELL (Tier 2): {reason}")
            return ('SELL', reason, context)
        
        # Tier 3: Moderate positive funding + downtrend confirmation
        if funding_rate > self.moderate_funding_threshold and is_downtrend and price_falling:
            reason = f"Positive funding {funding_rate:.4%} + downtrend confirmed, RSI {rsi:.1f}"
            logger.info(f"[{self.name}] SELL (Tier 3): {reason}")
            return ('SELL', reason, context)
        
        # ========== BUY SIGNALS (Long) ==========
        # Tier 1: Extreme negative funding + oversold
        if funding_rate < -self.extreme_funding_threshold and rsi < 35:
            reason = f"Extreme negative funding {funding_rate:.4%} (too many shorts) + oversold RSI {rsi:.1f}"
            logger.info(f"[{self.name}] BUY (Tier 1): {reason}")
            return ('BUY', reason, context)
        
        # Tier 2: High negative funding + moderately oversold
        if funding_rate < -self.high_funding_threshold and rsi < 45:
            reason = f"High negative funding {funding_rate:.4%} (many shorts) + low RSI {rsi:.1f}"
            logger.info(f"[{self.name}] BUY (Tier 2): {reason}")
            return ('BUY', reason, context)
        
        # Tier 3: Moderate negative funding + uptrend confirmation
        if funding_rate < -self.moderate_funding_threshold and is_uptrend and price_rising:
            reason = f"Negative funding {funding_rate:.4%} + uptrend confirmed, RSI {rsi:.1f}"
            logger.info(f"[{self.name}] BUY (Tier 3): {reason}")
            return ('BUY', reason, context)
        
        # Log current state for debugging
        reason = f"Funding={funding_rate:.4%}, RSI={rsi:.1f}, Trend={'up' if is_uptrend else 'down' if is_downtrend else 'neutral'}"
        logger.debug(f"[{self.name}] HOLD: {reason}")
        
        return ('HOLD', f'Monitoring funding rate for imbalance, {reason}', context)
    
    def get_status_message(self, df: pd.DataFrame, sentiment: str = "Neutral", **kwargs) -> str:
        funding_rate = kwargs.get('funding_rate')
        if funding_rate:
            return f"[{self.name}] Funding rate: {funding_rate:.4%}. Monitoring for imbalance."
        return f"[{self.name}] Monitoring funding rate extremes for reversal opportunities."


# Strategy factory function
def get_strategy(name: str, config: dict, lstm_manager=None) -> BaseStrategy:
    """
    Factory function to get a strategy instance by name.
    
    Args:
        name: Strategy name
        config: Configuration dictionary
        lstm_manager: Optional LSTMModelManager for LSTM_Momentum strategy
        
    Returns:
        Strategy instance
    """
    strategies = {
        "LSTM_Momentum": lambda: LSTM_Momentum_Strategy(config, lstm_manager),
        "Supertrend_MACD": lambda: Supertrend_MACD_Strategy(config),
        "Volatility_Cluster_Reversal": lambda: VolatilityClusterStrategy(config),
        "Volume_Spread_Analysis": lambda: VSA_Strategy(config),
        "EMA_Cross_RSI": lambda: EMA_Cross_RSI_Strategy(config),
        "Momentum_VWAP_RSI": lambda: Momentum_VWAP_RSI_Strategy(config),
        "BB_Squeeze_Breakout": lambda: Bollinger_Band_Squeeze_Strategy(config),
        "MA_Crossover": lambda: MA_Crossover_Strategy(config),
        "RSI_Divergence": lambda: RSI_Divergence_Strategy(config),
        "Reversal_Detector": lambda: Reversal_Detector_Strategy(config),
        "Funding_Rate": lambda: Funding_Rate_Strategy(config),
    }
    
    if name not in strategies:
        logger.warning(f"Strategy '{name}' not found, defaulting to LSTM_Momentum")
        name = "LSTM_Momentum"
    
    return strategies[name]()


def get_available_strategies() -> list:
    """Get list of available strategy names."""
    return [
        "LSTM_Momentum",
        "Supertrend_MACD",
        "Volatility_Cluster_Reversal",
        "Volume_Spread_Analysis",
        "EMA_Cross_RSI",
        "Momentum_VWAP_RSI",
        "BB_Squeeze_Breakout",
        "MA_Crossover",
        "RSI_Divergence",
        "Reversal_Detector",
        "Funding_Rate",
    ]
