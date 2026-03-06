"""
Indicator Configuration System
Centralized configuration for all technical indicators with validation and defaults
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class RSIConfig:
    """RSI indicator configuration."""
    period: int = 14
    overbought: float = 70.0
    oversold: float = 30.0
    
    def validate(self) -> bool:
        """Validate RSI configuration."""
        if not 2 <= self.period <= 100:
            raise ValueError(f"RSI period must be between 2 and 100, got {self.period}")
        if not 50 <= self.overbought <= 100:
            raise ValueError(f"RSI overbought must be between 50 and 100, got {self.overbought}")
        if not 0 <= self.oversold <= 50:
            raise ValueError(f"RSI oversold must be between 0 and 50, got {self.oversold}")
        return True


@dataclass
class MACDConfig:
    """MACD indicator configuration."""
    fast_period: int = 12
    slow_period: int = 26
    signal_period: int = 9
    
    def validate(self) -> bool:
        """Validate MACD configuration."""
        if not 2 <= self.fast_period <= 50:
            raise ValueError(f"MACD fast period must be between 2 and 50, got {self.fast_period}")
        if not 5 <= self.slow_period <= 100:
            raise ValueError(f"MACD slow period must be between 5 and 100, got {self.slow_period}")
        if not self.fast_period < self.slow_period:
            raise ValueError("MACD fast period must be less than slow period")
        if not 2 <= self.signal_period <= 50:
            raise ValueError(f"MACD signal period must be between 2 and 50, got {self.signal_period}")
        return True


@dataclass
class EMAConfig:
    """EMA indicator configuration with multiple periods."""
    short_period: int = 9
    medium_period: int = 21
    long_period: int = 50
    trend_period: int = 200
    
    def validate(self) -> bool:
        """Validate EMA configuration."""
        periods = [self.short_period, self.medium_period, self.long_period, self.trend_period]
        for i, p in enumerate(periods):
            if not 2 <= p <= 500:
                raise ValueError(f"EMA period must be between 2 and 500, got {p}")
        if not (self.short_period < self.medium_period < self.long_period < self.trend_period):
            logger.warning("EMA periods should ideally be in ascending order")
        return True


@dataclass
class BollingerBandsConfig:
    """Bollinger Bands indicator configuration."""
    period: int = 20
    std_dev: float = 2.0
    
    def validate(self) -> bool:
        """Validate Bollinger Bands configuration."""
        if not 5 <= self.period <= 100:
            raise ValueError(f"BB period must be between 5 and 100, got {self.period}")
        if not 0.5 <= self.std_dev <= 4.0:
            raise ValueError(f"BB std_dev must be between 0.5 and 4.0, got {self.std_dev}")
        return True


@dataclass
class ATRConfig:
    """ATR indicator configuration."""
    period: int = 14
    
    def validate(self) -> bool:
        """Validate ATR configuration."""
        if not 2 <= self.period <= 50:
            raise ValueError(f"ATR period must be between 2 and 50, got {self.period}")
        return True


@dataclass
class SupertrendConfig:
    """Supertrend indicator configuration."""
    period: int = 10
    multiplier: float = 3.0
    
    def validate(self) -> bool:
        """Validate Supertrend configuration."""
        if not 5 <= self.period <= 50:
            raise ValueError(f"Supertrend period must be between 5 and 50, got {self.period}")
        if not 1.0 <= self.multiplier <= 10.0:
            raise ValueError(f"Supertrend multiplier must be between 1.0 and 10.0, got {self.multiplier}")
        return True


@dataclass
class VWAPConfig:
    """VWAP indicator configuration."""
    enabled: bool = True
    anchor: str = "session"  # session, day, week
    
    def validate(self) -> bool:
        """Validate VWAP configuration."""
        if self.anchor not in ["session", "day", "week"]:
            raise ValueError(f"VWAP anchor must be session, day, or week, got {self.anchor}")
        return True


@dataclass
class IndicatorConfigSet:
    """Complete set of indicator configurations."""
    rsi: RSIConfig = field(default_factory=RSIConfig)
    macd: MACDConfig = field(default_factory=MACDConfig)
    ema: EMAConfig = field(default_factory=EMAConfig)
    bollinger: BollingerBandsConfig = field(default_factory=BollingerBandsConfig)
    atr: ATRConfig = field(default_factory=ATRConfig)
    supertrend: SupertrendConfig = field(default_factory=SupertrendConfig)
    vwap: VWAPConfig = field(default_factory=VWAPConfig)
    
    def validate_all(self) -> bool:
        """Validate all indicator configurations."""
        self.rsi.validate()
        self.macd.validate()
        self.ema.validate()
        self.bollinger.validate()
        self.atr.validate()
        self.supertrend.validate()
        self.vwap.validate()
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndicatorConfigSet':
        """Create configuration from dictionary."""
        config = cls()
        
        if 'rsi' in data:
            rsi_data = data['rsi']
            config.rsi = RSIConfig(
                period=rsi_data.get('period', 14),
                overbought=rsi_data.get('overbought', 70.0),
                oversold=rsi_data.get('oversold', 30.0),
            )
        
        if 'macd' in data:
            macd_data = data['macd']
            config.macd = MACDConfig(
                fast_period=macd_data.get('fast_period', 12),
                slow_period=macd_data.get('slow_period', 26),
                signal_period=macd_data.get('signal_period', 9),
            )
        
        if 'ema' in data:
            ema_data = data['ema']
            config.ema = EMAConfig(
                short_period=ema_data.get('short_period', 9),
                medium_period=ema_data.get('medium_period', 21),
                long_period=ema_data.get('long_period', 50),
                trend_period=ema_data.get('trend_period', 200),
            )
        
        if 'bollinger' in data:
            bb_data = data['bollinger']
            config.bollinger = BollingerBandsConfig(
                period=bb_data.get('period', 20),
                std_dev=bb_data.get('std_dev', 2.0),
            )
        
        if 'atr' in data:
            atr_data = data['atr']
            config.atr = ATRConfig(
                period=atr_data.get('period', 14),
            )
        
        if 'supertrend' in data:
            st_data = data['supertrend']
            config.supertrend = SupertrendConfig(
                period=st_data.get('period', 10),
                multiplier=st_data.get('multiplier', 3.0),
            )
        
        if 'vwap' in data:
            vwap_data = data['vwap']
            config.vwap = VWAPConfig(
                enabled=vwap_data.get('enabled', True),
                anchor=vwap_data.get('anchor', 'session'),
            )
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'rsi': {
                'period': self.rsi.period,
                'overbought': self.rsi.overbought,
                'oversold': self.rsi.oversold,
            },
            'macd': {
                'fast_period': self.macd.fast_period,
                'slow_period': self.macd.slow_period,
                'signal_period': self.macd.signal_period,
            },
            'ema': {
                'short_period': self.ema.short_period,
                'medium_period': self.ema.medium_period,
                'long_period': self.ema.long_period,
                'trend_period': self.ema.trend_period,
            },
            'bollinger': {
                'period': self.bollinger.period,
                'std_dev': self.bollinger.std_dev,
            },
            'atr': {
                'period': self.atr.period,
            },
            'supertrend': {
                'period': self.supertrend.period,
                'multiplier': self.supertrend.multiplier,
            },
            'vwap': {
                'enabled': self.vwap.enabled,
                'anchor': self.vwap.anchor,
            },
        }


# Preset configurations for different trading styles
PRESETS: Dict[str, IndicatorConfigSet] = {
    'default': IndicatorConfigSet(),
    
    'aggressive': IndicatorConfigSet(
        rsi=RSIConfig(period=7, overbought=65, oversold=35),
        macd=MACDConfig(fast_period=8, slow_period=17, signal_period=9),
        ema=EMAConfig(short_period=5, medium_period=13, long_period=34, trend_period=89),
        bollinger=BollingerBandsConfig(period=15, std_dev=1.5),
        atr=ATRConfig(period=10),
        supertrend=SupertrendConfig(period=7, multiplier=2.0),
    ),
    
    'conservative': IndicatorConfigSet(
        rsi=RSIConfig(period=21, overbought=75, oversold=25),
        macd=MACDConfig(fast_period=12, slow_period=26, signal_period=9),
        ema=EMAConfig(short_period=13, medium_period=34, long_period=89, trend_period=200),
        bollinger=BollingerBandsConfig(period=25, std_dev=2.5),
        atr=ATRConfig(period=20),
        supertrend=SupertrendConfig(period=14, multiplier=4.0),
    ),
    
    'scalping': IndicatorConfigSet(
        rsi=RSIConfig(period=5, overbought=60, oversold=40),
        macd=MACDConfig(fast_period=5, slow_period=13, signal_period=5),
        ema=EMAConfig(short_period=3, medium_period=8, long_period=21, trend_period=50),
        bollinger=BollingerBandsConfig(period=10, std_dev=1.5),
        atr=ATRConfig(period=7),
        supertrend=SupertrendConfig(period=5, multiplier=1.5),
    ),
    
    'swing': IndicatorConfigSet(
        rsi=RSIConfig(period=14, overbought=70, oversold=30),
        macd=MACDConfig(fast_period=12, slow_period=26, signal_period=9),
        ema=EMAConfig(short_period=21, medium_period=50, long_period=100, trend_period=200),
        bollinger=BollingerBandsConfig(period=20, std_dev=2.0),
        atr=ATRConfig(period=14),
        supertrend=SupertrendConfig(period=10, multiplier=3.0),
    ),
}


def get_preset(name: str) -> IndicatorConfigSet:
    """Get a preset indicator configuration by name."""
    if name not in PRESETS:
        logger.warning(f"Unknown preset '{name}', using default")
        return PRESETS['default']
    return PRESETS[name]


def get_available_presets() -> List[str]:
    """Get list of available preset names."""
    return list(PRESETS.keys())

