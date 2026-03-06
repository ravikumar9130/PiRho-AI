"""
Bybit API Client for USDT Perpetual Futures Trading
Uses the official pybit SDK with Unified Trading Account (v5 API)
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError, FailedRequestError

logger = logging.getLogger(__name__)


class BybitClient:
    """
    Bybit API wrapper for USDT Perpetual Futures trading.
    Supports both mainnet and testnet environments.
    """
    
    # Interval mapping for kline data
    INTERVAL_MAP = {
        "1": "1",
        "3": "3",
        "5": "5",
        "15": "15",
        "30": "30",
        "60": "60",
        "120": "120",
        "240": "240",
        "360": "360",
        "720": "720",
        "D": "D",
        "W": "W",
        "M": "M",
    }
    
    def __init__(self, config: dict):
        """
        Initialize Bybit client with configuration.
        
        Args:
            config: Dictionary containing bybit API credentials and settings
        """
        self.config = config
        bybit_config = config.get('bybit', {})
        
        self.api_key = bybit_config.get('api_key', '')
        self.api_secret = bybit_config.get('api_secret', '')
        self.testnet = bybit_config.get('testnet', True)
        
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests (10 req/sec)
        
        # Initialize HTTP client
        self.client = None
        self.authenticated = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Bybit HTTP client."""
        try:
            self.client = HTTP(
                testnet=self.testnet,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=20000,  # 20 second receive window
            )
            
            # Test authentication by fetching wallet balance
            if self.api_key and self.api_secret:
                try:
                    balance = self.client.get_wallet_balance(accountType="UNIFIED")
                    if balance.get('retCode') == 0:
                        self.authenticated = True
                        mode = "TESTNET" if self.testnet else "MAINNET"
                        logger.info(f"✅ Bybit client authenticated successfully ({mode})")
                    else:
                        logger.warning(f"⚠ Bybit authentication check returned: {balance.get('retMsg')}")
                except Exception as e:
                    logger.warning(f"⚠ Bybit authentication check failed: {e}")
            else:
                logger.warning("⚠ Bybit API credentials not provided - running in read-only mode")
                
        except Exception as e:
            logger.error(f"Failed to initialize Bybit client: {e}")
            self.client = None
    
    def _reinitialize_client(self):
        """Reinitialize the client after connection errors."""
        logger.info("Reinitializing Bybit client due to connection errors...")
        self._initialize_client()
    
    async def _rate_limit(self):
        """Apply rate limiting between API requests."""
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()
    
    # ==========================================
    # MARKET DATA METHODS
    # ==========================================
    
    async def get_ticker(self, symbol: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Get current ticker data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            max_retries: Number of retry attempts
            
        Returns:
            Dictionary with price data including lastPrice, bid, ask, etc.
        """
        for attempt in range(max_retries):
            await self._rate_limit()
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.get_tickers,
                        category="linear",
                        symbol=symbol
                    ),
                    timeout=15.0
                )
                
                if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                    ticker = result['result']['list'][0]
                    return {
                        'symbol': ticker.get('symbol'),
                        'lastPrice': self._safe_float(ticker.get('lastPrice')),
                        'bid': self._safe_float(ticker.get('bid1Price')),
                        'ask': self._safe_float(ticker.get('ask1Price')),
                        'volume24h': self._safe_float(ticker.get('volume24h')),
                        'turnover24h': self._safe_float(ticker.get('turnover24h')),
                        'highPrice24h': self._safe_float(ticker.get('highPrice24h')),
                        'lowPrice24h': self._safe_float(ticker.get('lowPrice24h')),
                        'prevPrice24h': self._safe_float(ticker.get('prevPrice24h')),
                        'price24hPcnt': self._safe_float(ticker.get('price24hPcnt')),
                        'fundingRate': self._safe_float(ticker.get('fundingRate')),
                        'nextFundingTime': ticker.get('nextFundingTime'),
                    }
                else:
                    logger.error(f"Failed to get ticker for {symbol}: {result.get('retMsg')}")
                    return {}
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching ticker for {symbol} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"Error fetching ticker for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        logger.error(f"Failed to get ticker for {symbol} after {max_retries} attempts")
        return {}
    
    async def get_current_price(self, symbol: str) -> float:
        """
        Get the current price for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Current price as float
        """
        ticker = await self.get_ticker(symbol)
        return ticker.get('lastPrice', 0.0)
    
    async def get_market_data(
        self, 
        symbol: str, 
        interval: str = "15", 
        limit: int = 200,
        max_retries: int = 3
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data (klines/candlesticks).
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            interval: Timeframe (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
            limit: Number of candles to fetch (max 1000)
            max_retries: Number of retry attempts on failure
            
        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        # Validate interval
        if interval not in self.INTERVAL_MAP:
            logger.warning(f"Invalid interval {interval}, using 15m")
            interval = "15"
        
        last_error = None
        for attempt in range(max_retries):
            await self._rate_limit()
            
            try:
                result = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.get_kline,
                        category="linear",
                        symbol=symbol,
                        interval=interval,
                        limit=min(limit, 1000)
                    ),
                    timeout=30.0  # 30 second timeout
                )
                
                if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                    klines = result['result']['list']
                    
                    # Bybit returns newest first, so reverse
                    klines = list(reversed(klines))
                    
                    df = pd.DataFrame(klines, columns=[
                        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'
                    ])
                    
                    # Convert types
                    df['timestamp'] = pd.to_datetime(df['timestamp'].astype(int), unit='ms')
                    for col in ['open', 'high', 'low', 'close', 'volume', 'turnover']:
                        df[col] = df[col].astype(float)
                    
                    df.set_index('timestamp', inplace=True)
                    
                    return df
                else:
                    logger.error(f"Failed to get klines for {symbol}: {result.get('retMsg')}")
                    return pd.DataFrame()
                    
            except asyncio.TimeoutError:
                last_error = "Request timed out"
                logger.warning(f"Timeout fetching market data for {symbol} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    # Reinitialize client on timeout
                    if attempt == max_retries - 2:
                        self._reinitialize_client()
                        
            except (ConnectionError, ConnectionResetError) as e:
                last_error = str(e)
                logger.warning(f"Connection error for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    self._reinitialize_client()
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error fetching market data for {symbol} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        logger.error(f"Failed to get market data for {symbol} after {max_retries} attempts: {last_error}")
        return pd.DataFrame()
    
    async def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Get current and historical funding rate information.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            
        Returns:
            Dictionary with funding rate data
        """
        await self._rate_limit()
        
        try:
            result = await asyncio.to_thread(
                self.client.get_funding_rate_history,
                category="linear",
                symbol=symbol,
                limit=1
            )
            
            if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                funding = result['result']['list'][0]
                return {
                    'symbol': funding.get('symbol'),
                    'fundingRate': self._safe_float(funding.get('fundingRate')),
                    'fundingRateTimestamp': funding.get('fundingRateTimestamp'),
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching funding rate for {symbol}: {e}")
            return {}
    
    async def get_instrument_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get instrument specifications (tick size, lot size, etc.)
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with instrument specifications
        """
        await self._rate_limit()
        
        try:
            result = await asyncio.to_thread(
                self.client.get_instruments_info,
                category="linear",
                symbol=symbol
            )
            
            if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                info = result['result']['list'][0]
                lot_filter = info.get('lotSizeFilter', {})
                price_filter = info.get('priceFilter', {})
                leverage_filter = info.get('leverageFilter', {})
                
                return {
                    'symbol': info.get('symbol'),
                    'baseCoin': info.get('baseCoin'),
                    'quoteCoin': info.get('quoteCoin'),
                    'minOrderQty': self._safe_float(lot_filter.get('minOrderQty'), 0.001),
                    'maxOrderQty': self._safe_float(lot_filter.get('maxOrderQty'), 1000000),
                    'qtyStep': self._safe_float(lot_filter.get('qtyStep'), 0.001),
                    'minPrice': self._safe_float(price_filter.get('minPrice')),
                    'maxPrice': self._safe_float(price_filter.get('maxPrice'), 1000000),
                    'tickSize': self._safe_float(price_filter.get('tickSize'), 0.01),
                    'maxLeverage': self._safe_float(leverage_filter.get('maxLeverage'), 100),
                    'minLeverage': self._safe_float(leverage_filter.get('minLeverage'), 1),
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching instrument info for {symbol}: {e}")
            return {}
    
    # ==========================================
    # ACCOUNT & WALLET METHODS
    # ==========================================
    
    async def get_wallet_balance(self, coin: str = "USDT") -> Dict[str, Any]:
        """
        Get wallet balance for unified trading account.
        
        Args:
            coin: Coin to check balance for (default: USDT)
            
        Returns:
            Dictionary with balance information
        """
        if not self.authenticated:
            logger.warning("Cannot get wallet balance - not authenticated")
            return {'available': 0, 'total': 0, 'unrealizedPnl': 0}
        
        await self._rate_limit()
        
        try:
            result = await asyncio.to_thread(
                self.client.get_wallet_balance,
                accountType="UNIFIED",
                coin=coin
            )
            
            logger.debug(f"Wallet balance API response: {result}")
            
            if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                account = result['result']['list'][0]
                coins = account.get('coin', [])
                
                # Log what coins are available
                logger.debug(f"Account coins found: {[c.get('coin') for c in coins]}")
                
                for c in coins:
                    if c.get('coin') == coin:
                        # Get all relevant balance fields
                        available_to_withdraw = self._safe_float(c.get('availableToWithdraw'))
                        wallet_balance = self._safe_float(c.get('walletBalance'))
                        equity = self._safe_float(c.get('equity'))
                        available_to_borrow = self._safe_float(c.get('availableToBorrow'))
                        
                        # Use the best available balance
                        # Priority: availableToWithdraw > equity > walletBalance
                        best_available = available_to_withdraw
                        if best_available <= 0 and equity > 0:
                            best_available = equity
                            logger.info(f"Using equity ({equity}) as available balance")
                        elif best_available <= 0 and wallet_balance > 0:
                            best_available = wallet_balance
                            logger.info(f"Using walletBalance ({wallet_balance}) as available balance")
                        
                        balance_info = {
                            'coin': coin,
                            'available': best_available,
                            'walletBalance': wallet_balance,
                            'equity': equity,
                            'totalEquity': self._safe_float(account.get('totalEquity')),
                            'unrealizedPnl': self._safe_float(c.get('unrealisedPnl')),
                            'marginBalance': self._safe_float(account.get('totalMarginBalance')),
                        }
                        
                        logger.info(f"Wallet balance for {coin}: available={best_available}, wallet={wallet_balance}, equity={equity}")
                        return balance_info
                
                # Coin not found in account
                logger.warning(f"{coin} not found in wallet. Available coins: {[c.get('coin') for c in coins]}")
                        
            else:
                logger.warning(f"Wallet balance API error: retCode={result.get('retCode')}, msg={result.get('retMsg')}")
                
            return {'available': 0, 'total': 0, 'unrealizedPnl': 0}
            
        except Exception as e:
            logger.error(f"Error fetching wallet balance: {e}", exc_info=True)
            return {'available': 0, 'total': 0, 'unrealizedPnl': 0}
    
    def _safe_float(self, value, default: float = 0.0) -> float:
        """
        Safely convert a value to float, handling empty strings and None.
        
        Args:
            value: Value to convert
            default: Default value if conversion fails
            
        Returns:
            Float value or default
        """
        if value is None or value == '' or value == 'None':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open positions or position for a specific symbol.
        
        Args:
            symbol: Optional symbol to filter positions
            
        Returns:
            List of position dictionaries
        """
        if not self.authenticated:
            logger.warning("Cannot get positions - not authenticated")
            return []
        
        await self._rate_limit()
        
        try:
            params = {"category": "linear", "settleCoin": "USDT"}
            if symbol:
                params["symbol"] = symbol
            
            result = await asyncio.to_thread(
                self.client.get_positions,
                **params
            )
            
            if result.get('retCode') == 0 and result.get('result', {}).get('list'):
                positions = []
                for pos in result['result']['list']:
                    size = self._safe_float(pos.get('size'))
                    if size > 0:  # Only include open positions
                        liq_price = self._safe_float(pos.get('liqPrice'))
                        positions.append({
                            'symbol': pos.get('symbol'),
                            'side': pos.get('side'),
                            'size': size,
                            'entryPrice': self._safe_float(pos.get('avgPrice')),
                            'markPrice': self._safe_float(pos.get('markPrice')),
                            'unrealizedPnl': self._safe_float(pos.get('unrealisedPnl')),
                            'leverage': self._safe_float(pos.get('leverage'), 1.0),
                            'liqPrice': liq_price if liq_price > 0 else None,
                            'takeProfit': pos.get('takeProfit'),
                            'stopLoss': pos.get('stopLoss'),
                            'positionValue': self._safe_float(pos.get('positionValue')),
                            'positionIdx': int(pos.get('positionIdx', 0)),
                        })
                return positions
            return []
            
        except Exception as e:
            logger.error(f"Error fetching positions: {e}")
            return []
    
    # ==========================================
    # ORDER EXECUTION METHODS
    # ==========================================
    
    async def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        Set leverage for a symbol.
        
        Args:
            symbol: Trading pair symbol
            leverage: Leverage value (1-100 depending on symbol)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.authenticated:
            logger.warning("Cannot set leverage - not authenticated")
            return False
        
        await self._rate_limit()
        
        try:
            result = await asyncio.to_thread(
                self.client.set_leverage,
                category="linear",
                symbol=symbol,
                buyLeverage=str(leverage),
                sellLeverage=str(leverage)
            )
            
            if result.get('retCode') == 0:
                logger.info(f"Leverage set to {leverage}x for {symbol}")
                return True
            elif result.get('retCode') == 110043:
                # Leverage not modified (already set)
                return True
            else:
                logger.error(f"Failed to set leverage: {result.get('retMsg')}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting leverage for {symbol}: {e}")
            return False
    
    async def place_perpetual_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        leverage: int = 1,
        order_type: str = "Market",
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        reduce_only: bool = False,
    ) -> Dict[str, Any]:
        """
        Place a perpetual futures order.
        
        Args:
            symbol: Trading pair symbol (e.g., "BTCUSDT")
            side: "Buy" or "Sell"
            qty: Order quantity in base currency
            leverage: Leverage to use (will be set before order)
            order_type: "Market" or "Limit"
            price: Limit price (required for Limit orders)
            stop_loss: Stop loss price
            take_profit: Take profit price
            reduce_only: If True, only reduces position
            
        Returns:
            Dictionary with order result
        """
        if not self.authenticated:
            logger.warning("Cannot place order - not authenticated")
            return {"ok": False, "error": "Not authenticated"}
        
        await self._rate_limit()
        
        try:
            # Set leverage first
            if not reduce_only:
                await self.set_leverage(symbol, leverage)
            
            # Get instrument info for qty precision
            inst_info = await self.get_instrument_info(symbol)
            qty_step = inst_info.get('qtyStep', 0.001)
            
            # Round quantity to valid step
            qty = round(qty / qty_step) * qty_step
            qty = max(qty, inst_info.get('minOrderQty', qty_step))
            
            # Build order parameters
            order_params = {
                "category": "linear",
                "symbol": symbol,
                "side": side,
                "orderType": order_type,
                "qty": str(qty),
                "timeInForce": "GTC" if order_type == "Limit" else "IOC",
                "reduceOnly": reduce_only,
            }
            
            if order_type == "Limit" and price:
                tick_size = inst_info.get('tickSize', 0.1)
                price = round(price / tick_size) * tick_size
                order_params["price"] = str(price)
            
            if stop_loss:
                order_params["stopLoss"] = str(stop_loss)
            
            if take_profit:
                order_params["takeProfit"] = str(take_profit)
            
            logger.info(f"Placing {side} order: {qty} {symbol} @ {order_type}")
            
            result = await asyncio.to_thread(
                self.client.place_order,
                **order_params
            )
            
            if result.get('retCode') == 0:
                order_id = result['result'].get('orderId')
                logger.info(f"✅ Order placed successfully: {order_id}")
                return {
                    "ok": True,
                    "orderId": order_id,
                    "symbol": symbol,
                    "side": side,
                    "qty": qty,
                    "leverage": leverage,
                    "orderType": order_type,
                }
            else:
                error_msg = result.get('retMsg', 'Unknown error')
                logger.error(f"❌ Order failed: {error_msg}")
                return {"ok": False, "error": error_msg}
                
        except InvalidRequestError as e:
            logger.error(f"Invalid order request: {e}")
            return {"ok": False, "error": str(e)}
        except FailedRequestError as e:
            logger.error(f"Order request failed: {e}")
            return {"ok": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"ok": False, "error": str(e)}
    
    async def close_position(
        self, 
        symbol: str, 
        side: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Close an open position for a symbol.
        
        Args:
            symbol: Trading pair symbol
            side: Position side to close (if not provided, closes entire position)
            
        Returns:
            Dictionary with close result
        """
        if not self.authenticated:
            logger.warning("Cannot close position - not authenticated")
            return {"ok": False, "error": "Not authenticated"}
        
        try:
            # Get current position
            positions = await self.get_positions(symbol)
            
            if not positions:
                logger.info(f"No open position for {symbol}")
                return {"ok": True, "message": "No position to close"}
            
            results = []
            for pos in positions:
                if side and pos['side'] != side:
                    continue
                
                # To close: Buy if short, Sell if long
                close_side = "Sell" if pos['side'] == "Buy" else "Buy"
                
                result = await self.place_perpetual_order(
                    symbol=symbol,
                    side=close_side,
                    qty=pos['size'],
                    reduce_only=True
                )
                results.append(result)
            
            if all(r.get('ok') for r in results):
                logger.info(f"✅ Position closed for {symbol}")
                return {"ok": True, "results": results}
            else:
                return {"ok": False, "results": results}
                
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return {"ok": False, "error": str(e)}
    
    async def set_trading_stop(
        self,
        symbol: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        trailing_stop: Optional[float] = None,
        position_idx: int = 0
    ) -> Dict[str, Any]:
        """
        Set stop loss, take profit, or trailing stop for an open position.
        
        Args:
            symbol: Trading pair symbol
            stop_loss: Stop loss price
            take_profit: Take profit price
            trailing_stop: Trailing stop distance in price
            position_idx: Position index (0 for one-way mode)
            
        Returns:
            Dictionary with result
        """
        if not self.authenticated:
            return {"ok": False, "error": "Not authenticated"}
        
        await self._rate_limit()
        
        try:
            params = {
                "category": "linear",
                "symbol": symbol,
                "positionIdx": position_idx,
            }
            
            if stop_loss is not None:
                params["stopLoss"] = str(stop_loss)
            if take_profit is not None:
                params["takeProfit"] = str(take_profit)
            if trailing_stop is not None:
                params["trailingStop"] = str(trailing_stop)
            
            result = await asyncio.to_thread(
                self.client.set_trading_stop,
                **params
            )
            
            if result.get('retCode') == 0:
                logger.info(f"Trading stop updated for {symbol}")
                return {"ok": True}
            else:
                return {"ok": False, "error": result.get('retMsg')}
                
        except Exception as e:
            logger.error(f"Error setting trading stop: {e}")
            return {"ok": False, "error": str(e)}
    
    async def get_order_history(
        self, 
        symbol: Optional[str] = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get order history.
        
        Args:
            symbol: Optional symbol filter
            limit: Number of orders to retrieve
            
        Returns:
            List of order dictionaries
        """
        if not self.authenticated:
            return []
        
        await self._rate_limit()
        
        try:
            params = {
                "category": "linear",
                "limit": limit,
            }
            if symbol:
                params["symbol"] = symbol
            
            result = await asyncio.to_thread(
                self.client.get_order_history,
                **params
            )
            
            if result.get('retCode') == 0:
                return result['result'].get('list', [])
            return []
            
        except Exception as e:
            logger.error(f"Error fetching order history: {e}")
            return []
    
    # ==========================================
    # UTILITY METHODS
    # ==========================================
    
    async def get_server_time(self) -> int:
        """Get Bybit server time in milliseconds."""
        try:
            result = await asyncio.to_thread(self.client.get_server_time)
            if result.get('retCode') == 0:
                return int(result['result'].get('timeSecond', 0)) * 1000
            return 0
        except Exception as e:
            logger.error(f"Error fetching server time: {e}")
            return 0
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self.authenticated
    
    def get_mode(self) -> str:
        """Get current trading mode (TESTNET/MAINNET)."""
        return "TESTNET" if self.testnet else "MAINNET"

