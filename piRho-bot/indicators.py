"""
Technical Indicators for Crypto Trading
Compatible with Bybit perpetual futures trading
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple, List

HAS_TALIB = False
HAS_PANDAS_TA = False

try:
    import talib
    HAS_TALIB = True
except ImportError:
    pass

try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except ImportError:
    pass


def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: Price series
        period: EMA period
        
    Returns:
        EMA series
    """
    if HAS_TALIB:
        return pd.Series(talib.EMA(prices, timeperiod=period), index=prices.index)
    elif HAS_PANDAS_TA:
        return ta.ema(prices, length=period)
    else:
        # Pure pandas implementation
        return prices.ewm(span=period, adjust=False).mean()


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        prices: Price series
        period: SMA period
        
    Returns:
        SMA series
    """
    if HAS_TALIB:
        return pd.Series(talib.SMA(prices, timeperiod=period), index=prices.index)
    else:
        return prices.rolling(window=period).mean()


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index.
    
    Args:
        prices: Price series
        period: RSI period (default 14)
        
    Returns:
        RSI series (0-100)
    """
    if HAS_TALIB:
        return pd.Series(talib.RSI(prices, timeperiod=period), index=prices.index)
    elif HAS_PANDAS_TA:
        return ta.rsi(prices, length=period)
    else:
        # Pure pandas implementation
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))


def calculate_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD indicator.
    
    Args:
        prices: Price series
        fast: Fast period
        slow: Slow period
        signal: Signal period
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    if HAS_TALIB:
        macd, macd_signal, macd_hist = talib.MACD(
            prices, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        return (
            pd.Series(macd, index=prices.index),
            pd.Series(macd_signal, index=prices.index),
            pd.Series(macd_hist, index=prices.index)
        )
    elif HAS_PANDAS_TA:
        macd_df = ta.macd(prices, fast=fast, slow=slow, signal=signal)
        if macd_df is not None:
            return (
                macd_df[f'MACD_{fast}_{slow}_{signal}'],
                macd_df[f'MACDs_{fast}_{slow}_{signal}'],
                macd_df[f'MACDh_{fast}_{slow}_{signal}']
            )
        return pd.Series(), pd.Series(), pd.Series()
    else:
        # Pure pandas implementation
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram


def calculate_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: Price series
        period: Moving average period
        std_dev: Standard deviation multiplier
        
    Returns:
        Tuple of (Upper band, Middle band, Lower band)
    """
    if HAS_TALIB:
        upper, middle, lower = talib.BBANDS(
            prices, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev
        )
        return (
            pd.Series(upper, index=prices.index),
            pd.Series(middle, index=prices.index),
            pd.Series(lower, index=prices.index)
        )
    elif HAS_PANDAS_TA:
        bb_df = ta.bbands(prices, length=period, std=std_dev)
        if bb_df is not None:
            return (
                bb_df[f'BBU_{period}_{std_dev}'],
                bb_df[f'BBM_{period}_{std_dev}'],
                bb_df[f'BBL_{period}_{std_dev}']
            )
        return pd.Series(), pd.Series(), pd.Series()
    else:
        # Pure pandas implementation
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower


def calculate_atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14
) -> pd.Series:
    """
    Calculate Average True Range.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period
        
    Returns:
        ATR series
    """
    if HAS_TALIB:
        return pd.Series(talib.ATR(high, low, close, timeperiod=period), index=close.index)
    elif HAS_PANDAS_TA:
        return ta.atr(high, low, close, length=period)
    else:
        # Pure pandas implementation
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()


def calculate_vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series
) -> pd.Series:
    """
    Calculate Volume Weighted Average Price.
    
    Args:
        high: High prices
        low: Low prices
        close: Close prices
        volume: Volume
        
    Returns:
        VWAP series
    """
    if HAS_PANDAS_TA:
        return ta.vwap(high, low, close, volume)
    else:
        # Pure pandas implementation
        typical_price = (high + low + close) / 3
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        return vwap


def check_rsi_divergence(
    price_df: pd.DataFrame,
    rsi_series: pd.Series,
    lookback: int = 30
) -> str:
    """
    Check for bullish/bearish RSI divergence.
    
    Args:
        price_df: DataFrame with OHLC data
        rsi_series: RSI values
        lookback: Lookback period
        
    Returns:
        "Bullish", "Bearish", or "None"
    """
    period = -lookback
    
    if len(price_df) < abs(period) or len(rsi_series) < abs(period):
        return "None"
    
    low_prices = price_df['low'][period:]
    high_prices = price_df['high'][period:]
    rsi_values = rsi_series[period:]
    
    if rsi_values.empty or len(rsi_values) < 2:
        return "None"
    
    # Bullish divergence: Lower low in price, higher low in RSI
    if (low_prices.iloc[-1] < low_prices.iloc[:-1].min() and 
        rsi_values.iloc[-1] > rsi_values.iloc[:-1].min()):
        return "Bullish"
    
    # Bearish divergence: Higher high in price, lower high in RSI
    if (high_prices.iloc[-1] > high_prices.iloc[:-1].max() and 
        rsi_values.iloc[-1] < rsi_values.iloc[:-1].max()):
        return "Bearish"
    
    return "None"


def _find_extrema(series: pd.Series, window: int = 5) -> List[Tuple[int, str]]:
    """
    Find local peaks and troughs in a series.
    
    Args:
        series: Price or indicator series
        window: Window size for extrema detection
        
    Returns:
        List of (index, type) tuples where type is 'peak' or 'trough'
    """
    extrema = []
    
    if len(series) < (2 * window + 1):
        return extrema
    
    for i in range(window, len(series) - window):
        window_data = series.iloc[i-window:i+window+1]
        is_peak = window_data.max() == series.iloc[i]
        is_trough = window_data.min() == series.iloc[i]
        
        if is_peak:
            extrema.append((i, 'peak'))
        if is_trough:
            extrema.append((i, 'trough'))
    
    return extrema


def check_momentum_divergence(
    price_series: pd.Series,
    oscillator_series: pd.Series,
    lookback: int = 45
) -> str:
    """
    Check for Class A Regular Divergence.
    
    Args:
        price_series: Close prices
        oscillator_series: RSI or other oscillator values
        lookback: Lookback period
        
    Returns:
        "Bullish", "Bearish", or "None"
    """
    if len(price_series) < lookback or len(oscillator_series) < lookback:
        return "None"
    
    price_slice = price_series.tail(lookback)
    osc_slice = oscillator_series.tail(lookback)
    
    price_extrema = _find_extrema(price_slice)
    osc_extrema = _find_extrema(osc_slice)
    
    price_peaks = [p for p in price_extrema if p[1] == 'peak']
    price_troughs = [p for p in price_extrema if p[1] == 'trough']
    osc_peaks = [p for p in osc_extrema if p[1] == 'peak']
    osc_troughs = [p for p in osc_extrema if p[1] == 'trough']
    
    # Bearish Divergence: Higher high in price, lower high in oscillator
    if len(price_peaks) >= 2 and len(osc_peaks) >= 2:
        last_price_peak = price_slice.iloc[price_peaks[-1][0]]
        prev_price_peak = price_slice.iloc[price_peaks[-2][0]]
        last_osc_peak = osc_slice.iloc[osc_peaks[-1][0]]
        prev_osc_peak = osc_slice.iloc[osc_peaks[-2][0]]
        
        if last_price_peak > prev_price_peak and last_osc_peak < prev_osc_peak:
            return "Bearish"
    
    # Bullish Divergence: Lower low in price, higher low in oscillator
    if len(price_troughs) >= 2 and len(osc_troughs) >= 2:
        last_price_trough = price_slice.iloc[price_troughs[-1][0]]
        prev_price_trough = price_slice.iloc[price_troughs[-2][0]]
        last_osc_trough = osc_slice.iloc[osc_troughs[-1][0]]
        prev_osc_trough = osc_slice.iloc[osc_troughs[-2][0]]
        
        if last_price_trough < prev_price_trough and last_osc_trough > prev_osc_trough:
            return "Bullish"
    
    return "None"


def is_trend_overextended(
    df: pd.DataFrame,
    lookback: int = 20,
    percent_move: float = 0.01,
    rsi_high: int = 70,
    rsi_low: int = 30
) -> str:
    """
    Detect if price is in an overextended trend.
    
    Args:
        df: DataFrame with OHLC and RSI data
        lookback: Lookback period
        percent_move: Minimum percent move for overextension
        rsi_high: RSI threshold for overbought
        rsi_low: RSI threshold for oversold
        
    Returns:
        "Uptrend", "Downtrend", or "None"
    """
    if len(df) < lookback or 'rsi' not in df.columns:
        return "None"
    
    price_slice = df['close'][-lookback:]
    max_price = price_slice.max()
    min_price = price_slice.min()
    current_price = price_slice.iloc[-1]
    rsi = df['rsi'].iloc[-1]
    
    if pd.isna(rsi):
        return "None"
    
    # Overextended uptrend
    if (current_price / min_price - 1) > percent_move and rsi > rsi_high:
        return "Uptrend"
    
    # Overextended downtrend
    if (max_price / current_price - 1) > percent_move and rsi < rsi_low:
        return "Downtrend"
    
    return "None"


def calculate_all_indicators(df: pd.DataFrame, config: dict = None) -> pd.DataFrame:
    """
    Calculate all common indicators and add them to the DataFrame.
    
    Args:
        df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        config: Optional configuration dictionary
        
    Returns:
        DataFrame with indicator columns added
    """
    if df.empty:
        return df
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # EMAs
    df['ema_9'] = calculate_ema(df['close'], 9)
    df['ema_15'] = calculate_ema(df['close'], 15)
    df['ema_21'] = calculate_ema(df['close'], 21)
    df['ema_50'] = calculate_ema(df['close'], 50)
    df['ema_200'] = calculate_ema(df['close'], 200)
    
    # RSI
    df['rsi'] = calculate_rsi(df['close'], 14)
    
    # MACD
    macd, macd_signal, macd_hist = calculate_macd(df['close'])
    df['macd'] = macd
    df['macd_signal'] = macd_signal
    df['macd_hist'] = macd_hist
    
    # Bollinger Bands
    bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(df['close'])
    df['bb_upper'] = bb_upper
    df['bb_mid'] = bb_mid
    df['bb_lower'] = bb_lower
    df['bb_bandwidth'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
    df['bb_bandwidth_ma'] = df['bb_bandwidth'].rolling(window=20).mean()
    
    # ATR
    df['atr'] = calculate_atr(df['high'], df['low'], df['close'], 14)
    df['atr_ma'] = df['atr'].rolling(window=20).mean()
    
    # VWAP
    if 'volume' in df.columns:
        df['vwap'] = calculate_vwap(df['high'], df['low'], df['close'], df['volume'])
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
    
    # Supertrend (using pandas_ta if available)
    if HAS_PANDAS_TA:
        try:
            supertrend = ta.supertrend(df['high'], df['low'], df['close'])
            if supertrend is not None and not supertrend.empty:
                df['supertrend'] = supertrend['SUPERT_7_3.0']
                df['supertrend_direction'] = supertrend['SUPERTd_7_3.0']
        except Exception:
            pass
    else:
        # Simple trend direction based on EMA
        df['supertrend_direction'] = np.where(df['close'] > df['ema_21'], 1, -1)
    
    # Price spread (for VSA)
    df['spread'] = df['high'] - df['low']
    
    return df


# CPR functions removed - not applicable to 24/7 crypto markets
# For crypto, we use different support/resistance methodologies


def check_ema_crossover(
    df: pd.DataFrame,
    current_candle: pd.Series,
    last_candle: pd.Series,
    period: int
) -> str:
    """
    Check for EMA crossover.
    
    Args:
        df: Full DataFrame (unused but kept for compatibility)
        current_candle: Current candle data
        last_candle: Previous candle data
        period: EMA period to check
        
    Returns:
        "Bullish", "Bearish", or "None"
    """
    ema_col = f'ema_{period}'
    
    if ema_col not in current_candle.index or ema_col not in last_candle.index:
        return "None"
    
    price = current_candle['close']
    last_price = last_candle['close']
    ema_val = current_candle[ema_col]
    last_ema_val = last_candle[ema_col]
    
    # Bullish crossover
    if last_price <= last_ema_val and price > ema_val:
        return "Bullish"
    
    # Bearish crossover
    if last_price >= last_ema_val and price < ema_val:
        return "Bearish"
    
    return "None"
