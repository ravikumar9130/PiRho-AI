"""
Dynamic LSTM Price Predictor for Crypto Trading
Supports per-symbol model training, loading, and prediction
"""

import logging
import os
import json
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    HAS_TORCH = False

logger = logging.getLogger(__name__)


# ============================================================
# LSTM MODEL ARCHITECTURE
# ============================================================

if HAS_TORCH:
    class EnhancedLSTM(nn.Module):
        """
        Enhanced LSTM model with attention mechanism for price prediction.
        Predicts: Direction probability (0=down, 1=up) and price change magnitude
        """
        
        def __init__(
            self, 
            input_size: int = 12,  # OHLCV + indicators
            hidden_size: int = 128,
            num_layers: int = 3,
            dropout: float = 0.2
        ):
            super(EnhancedLSTM, self).__init__()
            
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            # Batch normalization for input
            self.input_bn = nn.BatchNorm1d(input_size)
            
            # LSTM layers
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
                bidirectional=True
            )
            
            # Attention mechanism
            self.attention = nn.Sequential(
                nn.Linear(hidden_size * 2, hidden_size),
                nn.Tanh(),
                nn.Linear(hidden_size, 1)
            )
            
            # Output layers
            self.fc_direction = nn.Sequential(
                nn.Linear(hidden_size * 2, 64),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(64, 1),
                nn.Sigmoid()  # Probability of price going up
            )
            
            self.fc_magnitude = nn.Sequential(
                nn.Linear(hidden_size * 2, 64),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(64, 1)  # Predicted % change
            )
        
        def forward(self, x):
            batch_size, seq_len, features = x.size()
            
            # Batch normalization (reshape for BN)
            x = x.permute(0, 2, 1)  # [batch, features, seq]
            x = self.input_bn(x)
            x = x.permute(0, 2, 1)  # [batch, seq, features]
            
            # LSTM
            lstm_out, _ = self.lstm(x)  # [batch, seq, hidden*2]
            
            # Attention weights
            attention_weights = self.attention(lstm_out)  # [batch, seq, 1]
            attention_weights = torch.softmax(attention_weights, dim=1)
            
            # Weighted sum
            context = torch.sum(lstm_out * attention_weights, dim=1)  # [batch, hidden*2]
            
            # Predictions
            direction = self.fc_direction(context)  # Probability up
            magnitude = self.fc_magnitude(context)  # % change
            
            return direction, magnitude
    
    
    class PriceDataset(Dataset):
        """Dataset for price prediction with labels."""
        
        def __init__(self, features: np.ndarray, labels: np.ndarray, sequence_length: int = 30):
            self.features = features
            self.labels = labels
            self.sequence_length = sequence_length
        
        def __len__(self):
            return len(self.features) - self.sequence_length - 1
        
        def __getitem__(self, idx):
            # Input sequence
            x = self.features[idx:idx + self.sequence_length]
            
            # Target: direction and magnitude from current close to next close
            current_close = self.features[idx + self.sequence_length - 1, 3]  # close is index 3
            next_close = self.features[idx + self.sequence_length, 3]
            
            direction = 1.0 if next_close > current_close else 0.0
            magnitude = (next_close - current_close) / current_close * 100  # % change
            
            return (
                torch.FloatTensor(x),
                torch.FloatTensor([direction]),
                torch.FloatTensor([magnitude])
            )
else:
    EnhancedLSTM = None
    PriceDataset = None


# ============================================================
# FEATURE ENGINEERING
# ============================================================

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators as features for LSTM.
    
    Args:
        df: DataFrame with OHLCV columns
        
    Returns:
        DataFrame with additional feature columns
    """
    df = df.copy()
    
    # Price features (normalized by close)
    df['open_norm'] = df['open'] / df['close']
    df['high_norm'] = df['high'] / df['close']
    df['low_norm'] = df['low'] / df['close']
    df['close_norm'] = 1.0  # Reference
    
    # Volume feature (normalized)
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['volume_norm'] = df['volume'] / (df['volume_ma'] + 1e-8)
    
    # Price changes
    df['returns'] = df['close'].pct_change()
    df['returns_5'] = df['close'].pct_change(5)
    df['returns_10'] = df['close'].pct_change(10)
    
    # Volatility
    df['volatility'] = df['returns'].rolling(20).std()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-8)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi_norm'] = df['rsi'] / 100  # Normalize to 0-1
    
    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_norm'] = df['macd_hist'] / (df['close'] + 1e-8) * 100
    
    # EMAs
    df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema_cross'] = (df['ema9'] - df['ema21']) / df['close'] * 100
    
    # Bollinger Bands
    df['bb_mid'] = df['close'].rolling(20).mean()
    df['bb_std'] = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + 2 * df['bb_std']
    df['bb_lower'] = df['bb_mid'] - 2 * df['bb_std']
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-8)
    
    # ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr'] = tr.rolling(14).mean()
    df['atr_norm'] = df['atr'] / df['close'] * 100
    
    return df


def get_feature_columns() -> List[str]:
    """Get list of feature columns for LSTM input."""
    return [
        'open_norm', 'high_norm', 'low_norm', 'close_norm',
        'volume_norm', 'returns', 'volatility',
        'rsi_norm', 'macd_norm', 'ema_cross',
        'bb_position', 'atr_norm'
    ]


def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, float, np.ndarray, np.ndarray]:
    """
    Prepare normalized features for LSTM.
    
    Returns:
        Tuple of (feature_array, last_close_price, mean, std)
    """
    df = calculate_features(df)
    
    # Drop NaN rows
    feature_cols = get_feature_columns()
    df = df.dropna(subset=feature_cols)
    
    # Extract features
    features = df[feature_cols].values
    
    # Normalize features (z-score per column)
    mean = features.mean(axis=0)
    std = features.std(axis=0) + 1e-8
    normalized = (features - mean) / std
    
    last_close = df['close'].iloc[-1]
    
    return normalized, last_close, mean, std


# ============================================================
# MODEL MANAGER
# ============================================================

class LSTMModelManager:
    """
    Manages LSTM models for multiple symbols.
    Handles training, loading, saving, and prediction.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the LSTM model manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Configuration
        ai_config = config.get('ai', {})
        self.sequence_length = ai_config.get('lstm_sequence_length', 30)
        self.confidence_threshold = ai_config.get('lstm_confidence_threshold', 0.65)
        self.auto_train = ai_config.get('lstm_auto_train', True)
        self.train_epochs = ai_config.get('lstm_train_epochs', 100)
        
        # Loaded models cache
        self._models: Dict[str, Any] = {}
        self._norm_params: Dict[str, Dict] = {}
        
        # Device
        self.device = torch.device('cuda' if HAS_TORCH and torch.cuda.is_available() else 'cpu')
    
    def get_model_path(self, symbol: str) -> str:
        """Get model file path for a symbol."""
        return os.path.join(self.models_dir, f"lstm_{symbol}.pt")
    
    def get_norm_path(self, symbol: str) -> str:
        """Get normalization params file path for a symbol."""
        return os.path.join(self.models_dir, f"lstm_{symbol}_norm.json")
    
    def model_exists(self, symbol: str) -> bool:
        """Check if a trained model exists for the symbol."""
        return os.path.exists(self.get_model_path(symbol))
    
    def load_model(self, symbol: str) -> Optional[Any]:
        """
        Load a trained model for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Loaded model or None if not found
        """
        if not HAS_TORCH:
            logger.warning("PyTorch not available")
            return None
        
        # Check cache
        if symbol in self._models:
            return self._models[symbol]
        
        model_path = self.get_model_path(symbol)
        norm_path = self.get_norm_path(symbol)
        
        if not os.path.exists(model_path):
            logger.info(f"No LSTM model found for {symbol}")
            return None
        
        try:
            # Create model instance
            model = EnhancedLSTM(
                input_size=len(get_feature_columns()),
                hidden_size=128,
                num_layers=3
            )
            
            # Load weights
            state_dict = torch.load(model_path, map_location=self.device)
            model.load_state_dict(state_dict)
            model.to(self.device)
            model.eval()
            
            # Load normalization params
            if os.path.exists(norm_path):
                with open(norm_path, 'r') as f:
                    self._norm_params[symbol] = json.load(f)
            
            self._models[symbol] = model
            logger.info(f"✅ LSTM model loaded for {symbol}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load model for {symbol}: {e}")
            return None
    
    async def train_model(
        self,
        symbol: str,
        df: pd.DataFrame,
        epochs: int = None,
        batch_size: int = 64
    ) -> bool:
        """
        Train a new LSTM model for a symbol.
        
        Args:
            symbol: Trading symbol
            df: Historical OHLCV data
            epochs: Training epochs (uses config default if None)
            batch_size: Batch size for training
            
        Returns:
            True if training succeeded
        """
        if not HAS_TORCH:
            logger.error("PyTorch not available for training")
            return False
        
        epochs = epochs or self.train_epochs
        
        logger.info(f"🚀 Training LSTM model for {symbol}...")
        
        try:
            # Prepare features
            df = calculate_features(df)
            feature_cols = get_feature_columns()
            df = df.dropna(subset=feature_cols)
            
            if len(df) < self.sequence_length + 100:
                logger.error(f"Not enough data for training. Need {self.sequence_length + 100}, got {len(df)}")
                return False
            
            # Extract and normalize features
            features = df[feature_cols].values
            mean = features.mean(axis=0)
            std = features.std(axis=0) + 1e-8
            normalized = (features - mean) / std
            
            # Create labels (direction: 1=up, 0=down)
            labels = (df['close'].shift(-1) > df['close']).astype(float).values
            
            # Create dataset
            dataset = PriceDataset(normalized, labels, self.sequence_length)
            
            # Split train/val
            train_size = int(len(dataset) * 0.8)
            val_size = len(dataset) - train_size
            train_dataset, val_dataset = torch.utils.data.random_split(
                dataset, [train_size, val_size]
            )
            
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
            logger.info(f"📊 Dataset: {len(dataset)} samples (train: {train_size}, val: {val_size})")
            
            # Create model
            model = EnhancedLSTM(
                input_size=len(feature_cols),
                hidden_size=128,
                num_layers=3
            ).to(self.device)
            
            # Loss and optimizer
            criterion_dir = nn.BCELoss()
            criterion_mag = nn.MSELoss()
            optimizer = optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.01)
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
            
            best_val_loss = float('inf')
            patience_counter = 0
            max_patience = 20
            
            for epoch in range(epochs):
                # Training
                model.train()
                train_loss = 0
                
                for batch_x, batch_dir, batch_mag in train_loader:
                    batch_x = batch_x.to(self.device)
                    batch_dir = batch_dir.to(self.device)
                    batch_mag = batch_mag.to(self.device)
                    
                    optimizer.zero_grad()
                    
                    pred_dir, pred_mag = model(batch_x)
                    
                    loss_dir = criterion_dir(pred_dir, batch_dir)
                    loss_mag = criterion_mag(pred_mag, batch_mag)
                    loss = loss_dir + 0.5 * loss_mag
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                # Validation
                model.eval()
                val_loss = 0
                correct = 0
                total = 0
                
                with torch.no_grad():
                    for batch_x, batch_dir, batch_mag in val_loader:
                        batch_x = batch_x.to(self.device)
                        batch_dir = batch_dir.to(self.device)
                        batch_mag = batch_mag.to(self.device)
                        
                        pred_dir, pred_mag = model(batch_x)
                        
                        loss_dir = criterion_dir(pred_dir, batch_dir)
                        loss_mag = criterion_mag(pred_mag, batch_mag)
                        val_loss += (loss_dir + 0.5 * loss_mag).item()
                        
                        # Accuracy
                        predicted = (pred_dir > 0.5).float()
                        correct += (predicted == batch_dir).sum().item()
                        total += batch_dir.size(0)
                
                avg_train = train_loss / len(train_loader)
                avg_val = val_loss / len(val_loader)
                accuracy = correct / total * 100
                
                scheduler.step(avg_val)
                
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch + 1}/{epochs} | "
                        f"Train: {avg_train:.4f} | Val: {avg_val:.4f} | "
                        f"Acc: {accuracy:.1f}%"
                    )
                
                # Early stopping
                if avg_val < best_val_loss:
                    best_val_loss = avg_val
                    patience_counter = 0
                    # Save best model
                    torch.save(model.state_dict(), self.get_model_path(symbol))
                else:
                    patience_counter += 1
                    if patience_counter >= max_patience:
                        logger.info(f"Early stopping at epoch {epoch + 1}")
                        break
            
            # Save normalization params
            norm_params = {
                'mean': mean.tolist(),
                'std': std.tolist(),
                'feature_columns': feature_cols
            }
            with open(self.get_norm_path(symbol), 'w') as f:
                json.dump(norm_params, f)
            
            # Cache the model
            self._models[symbol] = model
            self._norm_params[symbol] = norm_params
            
            logger.info(f"✅ Model trained and saved for {symbol} (accuracy: {accuracy:.1f}%)")
            return True
            
        except Exception as e:
            logger.error(f"Training failed for {symbol}: {e}", exc_info=True)
            return False
    
    def predict(
        self,
        symbol: str,
        df: pd.DataFrame
    ) -> Tuple[float, float, str]:
        """
        Make a prediction for the given symbol.
        
        Args:
            symbol: Trading symbol
            df: Recent OHLCV data (at least sequence_length candles)
            
        Returns:
            Tuple of (direction_probability, predicted_magnitude, signal)
            direction_probability: 0-1 (0=down, 1=up)
            predicted_magnitude: Expected % change
            signal: "BUY", "SELL", or "HOLD"
        """
        if not HAS_TORCH:
            return 0.5, 0.0, "HOLD"
        
        model = self._models.get(symbol) or self.load_model(symbol)
        
        if model is None:
            return 0.5, 0.0, "HOLD"
        
        try:
            # Prepare features
            df = calculate_features(df)
            feature_cols = get_feature_columns()
            df = df.dropna(subset=feature_cols)
            
            if len(df) < self.sequence_length:
                logger.warning(f"Not enough data for prediction. Need {self.sequence_length}, got {len(df)}")
                return 0.5, 0.0, "HOLD"
            
            # Get last sequence
            features = df[feature_cols].values[-self.sequence_length:]
            
            # Normalize using saved params or compute
            if symbol in self._norm_params:
                mean = np.array(self._norm_params[symbol]['mean'])
                std = np.array(self._norm_params[symbol]['std'])
            else:
                # Use rolling normalization
                all_features = df[feature_cols].values
                mean = all_features.mean(axis=0)
                std = all_features.std(axis=0) + 1e-8
            
            normalized = (features - mean) / std
            
            # Predict
            model.eval()
            with torch.no_grad():
                x = torch.FloatTensor(normalized).unsqueeze(0).to(self.device)
                direction_prob, magnitude = model(x)
                
                direction_prob = direction_prob.item()
                magnitude = magnitude.item()
            
            # Generate signal
            if direction_prob > self.confidence_threshold:
                signal = "BUY"
            elif direction_prob < (1 - self.confidence_threshold):
                signal = "SELL"
            else:
                signal = "HOLD"
            
            logger.debug(
                f"[LSTM {symbol}] Direction: {direction_prob:.2%}, "
                f"Magnitude: {magnitude:+.2f}%, Signal: {signal}"
            )
            
            return direction_prob, magnitude, signal
            
        except Exception as e:
            logger.error(f"Prediction failed for {symbol}: {e}")
            return 0.5, 0.0, "HOLD"
    
    def get_model_info(self, symbol: str) -> Dict[str, Any]:
        """Get information about a model."""
        model_path = self.get_model_path(symbol)
        
        if not os.path.exists(model_path):
            return {'exists': False, 'symbol': symbol}
        
        stat = os.stat(model_path)
        
        return {
            'exists': True,
            'symbol': symbol,
            'path': model_path,
            'size_kb': stat.st_size / 1024,
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'loaded': symbol in self._models
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================

_model_manager: Optional[LSTMModelManager] = None


def get_model_manager(config: dict) -> LSTMModelManager:
    """Get or create the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = LSTMModelManager(config)
    return _model_manager

