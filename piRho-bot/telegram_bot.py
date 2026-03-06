"""
Telegram Bot for Bybit Perpetual Futures Trading
Interactive trading interface with live position monitoring
"""

import logging
import asyncio
import io
import sys
from datetime import datetime
from typing import Optional, Dict, Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)
from telegram.request import HTTPXRequest

from bybit_client import BybitClient
from agents import OrderExecutionAgent, PositionManagementAgent
from sentiment_agent import CryptoSentimentAgent
from langgraph_agent import LangGraphAgent
from strategy_factory import get_strategy, get_available_strategies
from indicators import calculate_all_indicators
from reporting import get_trade_history, calculate_performance_metrics, generate_daily_summary

logger = logging.getLogger(__name__)


def fmt_money(x):
    """Format number as money string."""
    try:
        return f"{x:,.2f}"
    except Exception:
        return str(x)


class TelegramTradingBot:
    """
    Telegram bot for interactive trading with Bybit perpetual futures.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the Telegram trading bot.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        telegram_config = config.get('telegram', {})
        trading_config = config.get('trading', {})
        
        self.bot_token = telegram_config.get('bot_token', '')
        self.chat_id = telegram_config.get('chat_id', '')
        
        # Trading settings
        self.symbols = trading_config.get('symbols', ['BTCUSDT'])
        self.default_symbol = trading_config.get('default_symbol', 'BTCUSDT')
        self.default_leverage = trading_config.get('default_leverage', 5)
        
        # Components
        self.bybit_client: Optional[BybitClient] = None
        self.order_agent: Optional[OrderExecutionAgent] = None
        self.position_agent: Optional[PositionManagementAgent] = None
        self.sentiment_agent: Optional[CryptoSentimentAgent] = None
        self.langgraph_agent: Optional[LangGraphAgent] = None
        
        # State
        self.current_trade = None
        self.app: Optional[Application] = None
        self._pending_trades: Dict[int, Dict] = {}
    
    def set_components(
        self,
        bybit_client: BybitClient,
        order_agent: OrderExecutionAgent,
        position_agent: PositionManagementAgent,
        sentiment_agent: CryptoSentimentAgent = None,
        langgraph_agent: LangGraphAgent = None
    ):
        """Set trading components."""
        self.bybit_client = bybit_client
        self.order_agent = order_agent
        self.position_agent = position_agent
        self.sentiment_agent = sentiment_agent
        self.langgraph_agent = langgraph_agent
    
    async def build_application(self) -> Application:
        """Build and configure the Telegram application."""
        if not self.bot_token:
            raise ValueError("Telegram bot token not configured")
        
        request = HTTPXRequest(
            connect_timeout=30,
            read_timeout=30,
            write_timeout=30,
            pool_timeout=30
        )
        
        app = Application.builder().token(self.bot_token).request(request).build()
        
        # Command handlers
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("help", self._cmd_help))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("balance", self._cmd_balance))
        app.add_handler(CommandHandler("price", self._cmd_price))
        app.add_handler(CommandHandler("trade", self._cmd_trade))
        app.add_handler(CommandHandler("close", self._cmd_close))
        app.add_handler(CommandHandler("position", self._cmd_position))
        app.add_handler(CommandHandler("sentiment", self._cmd_sentiment))
        app.add_handler(CommandHandler("performance", self._cmd_performance))
        app.add_handler(CommandHandler("strategies", self._cmd_strategies))
        
        # Callback handlers
        app.add_handler(CallbackQueryHandler(self._handle_callback))
        
        # Message handlers
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self._handle_message
        ))
        
        self.app = app
        logger.info("Telegram application built successfully")
        return app
    
    async def start(self):
        """Start the Telegram bot."""
        if not self.app:
            await self.build_application()
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("Telegram bot started")
        
        # Send startup message
        await self.send_startup_message()
    
    async def stop(self):
        """Stop the Telegram bot."""
        if self.app:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    # ==========================================
    # COMMAND HANDLERS
    # ==========================================
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            mode = self.bybit_client.get_mode() if self.bybit_client else "Not Connected"
            auth_status = "✅ Connected" if (self.bybit_client and self.bybit_client.authenticated) else "❌ Not Connected"
            
            message = (
                "🤖 *Bybit Perpetual Trading Bot*\n\n"
                f"🔗 Bybit: {auth_status}\n"
                f"🌐 Mode: {mode}\n\n"
                "*Commands:*\n"
                "/status - Bot and connection status\n"
                "/balance - Check wallet balance\n"
                "/price [symbol] - Get current price\n"
                "/trade - Start a new trade\n"
                "/position - View current position\n"
                "/close - Close current position\n"
                "/sentiment - Market sentiment analysis\n"
                "/performance - Trading performance stats\n"
                "/strategies - List available strategies\n"
                "/help - Show all commands\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await update.message.reply_text("Error loading bot status")
    
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        message = (
            "📚 *Trading Bot Help*\n\n"
            "*Market Commands:*\n"
            "• `/price` - Get BTC price\n"
            "• `/price ETH` - Get specific symbol price\n"
            "• `/sentiment` - Get market sentiment\n\n"
            "*Trading Commands:*\n"
            "• `/trade` - Interactive trade setup\n"
            "• `/position` - View current position\n"
            "• `/close` - Close current position\n\n"
            "*Account Commands:*\n"
            "• `/balance` - Check wallet balance\n"
            "• `/performance` - Trading statistics\n"
            "• `/status` - Bot status\n\n"
            "*Configuration:*\n"
            "• `/strategies` - List strategies\n"
        )
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        try:
            if not self.bybit_client:
                await update.message.reply_text("❌ Bybit client not initialized")
                return
            
            mode = self.bybit_client.get_mode()
            auth = "✅ Authenticated" if self.bybit_client.authenticated else "❌ Not Authenticated"
            
            # Get positions
            positions = await self.bybit_client.get_positions()
            position_count = len(positions)
            
            # Get balance
            balance = await self.bybit_client.get_wallet_balance()
            available = balance.get('available', 0)
            
            is_paper = self.config.get('trading_flags', {}).get('paper_trading', True)
            trading_mode = "📝 Paper Trading" if is_paper else "💰 Live Trading"
            
            message = (
                "📊 *Bot Status*\n\n"
                f"🔗 Connection: {auth}\n"
                f"🌐 Network: {mode}\n"
                f"🎯 Mode: {trading_mode}\n"
                f"📈 Open Positions: {position_count}\n"
                f"💰 Available: ${fmt_money(available)} USDT\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Status command error: {e}")
            await update.message.reply_text("Error getting status")
    
    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command."""
        try:
            if not self.bybit_client:
                await update.message.reply_text("❌ Not connected to Bybit")
                return
            
            balance = await self.bybit_client.get_wallet_balance()
            
            message = (
                "💰 *Wallet Balance*\n\n"
                f"📊 Total Equity: ${fmt_money(balance.get('totalEquity', 0))}\n"
                f"💵 Wallet Balance: ${fmt_money(balance.get('walletBalance', 0))}\n"
                f"✅ Available: ${fmt_money(balance.get('available', 0))}\n"
                f"📈 Unrealized P&L: ${fmt_money(balance.get('unrealizedPnl', 0))}\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Balance command error: {e}")
            await update.message.reply_text("Error getting balance")
    
    async def _cmd_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command."""
        try:
            # Get symbol from args or use default
            args = context.args
            if args:
                symbol = args[0].upper()
                if not symbol.endswith('USDT'):
                    symbol += 'USDT'
            else:
                symbol = self.default_symbol
            
            ticker = await self.bybit_client.get_ticker(symbol)
            
            if not ticker:
                await update.message.reply_text(f"❌ Could not get price for {symbol}")
                return
            
            price = ticker.get('lastPrice', 0)
            change_pct = ticker.get('price24hPcnt', 0) * 100
            high_24h = ticker.get('highPrice24h', 0)
            low_24h = ticker.get('lowPrice24h', 0)
            volume = ticker.get('volume24h', 0)
            funding = ticker.get('fundingRate', 0) * 100
            
            change_emoji = "📈" if change_pct >= 0 else "📉"
            
            message = (
                f"💹 *{symbol}*\n\n"
                f"💰 Price: ${fmt_money(price)}\n"
                f"{change_emoji} 24h Change: {change_pct:+.2f}%\n"
                f"📊 24h High: ${fmt_money(high_24h)}\n"
                f"📉 24h Low: ${fmt_money(low_24h)}\n"
                f"📦 24h Volume: {fmt_money(volume)}\n"
                f"💸 Funding Rate: {funding:.4f}%\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Price command error: {e}")
            await update.message.reply_text("Error getting price")
    
    async def _cmd_trade(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trade command - interactive trade setup."""
        try:
            # Check for existing position
            positions = await self.bybit_client.get_positions()
            if positions:
                await update.message.reply_text(
                    "⚠️ You already have an open position. "
                    "Use /close to close it first."
                )
                return
            
            # Symbol selection keyboard
            keyboard = []
            row = []
            for symbol in self.symbols:
                row.append(InlineKeyboardButton(
                    symbol.replace('USDT', ''),
                    callback_data=f"trade_symbol_{symbol}"
                ))
                if len(row) == 3:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            
            await update.message.reply_text(
                "📊 *New Trade*\n\nSelect trading pair:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Trade command error: {e}")
            await update.message.reply_text("Error starting trade")
    
    async def _cmd_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /position command."""
        try:
            if not self.bybit_client:
                await update.message.reply_text("❌ Not connected")
                return
            
            positions = await self.bybit_client.get_positions()
            
            if not positions:
                await update.message.reply_text("📊 No open positions")
                return
            
            for pos in positions:
                side_emoji = "📈" if pos['side'] == 'Buy' else "📉"
                pnl = pos.get('unrealizedPnl', 0)
                pnl_emoji = "💰" if pnl >= 0 else "🔻"
                
                liq_price = pos.get('liqPrice')
                liq_str = f"${fmt_money(liq_price)}" if liq_price else "N/A"
                
                message = (
                    f"{side_emoji} *{pos['symbol']} Position*\n\n"
                    f"📊 Side: {pos['side']}\n"
                    f"📏 Size: {pos['size']}\n"
                    f"💵 Entry: ${fmt_money(pos['entryPrice'])}\n"
                    f"📈 Mark: ${fmt_money(pos['markPrice'])}\n"
                    f"{pnl_emoji} P&L: ${fmt_money(pnl)}\n"
                    f"⚙️ Leverage: {pos['leverage']}x\n"
                    f"⚠️ Liq Price: {liq_str}\n"
                )
                
                keyboard = [[
                    InlineKeyboardButton("❌ Close Position", callback_data=f"close_{pos['symbol']}")
                ]]
                
                await update.message.reply_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                
        except Exception as e:
            logger.error(f"Position command error: {e}")
            await update.message.reply_text("Error getting positions")
    
    async def _cmd_close(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /close command."""
        try:
            positions = await self.bybit_client.get_positions()
            
            if not positions:
                await update.message.reply_text("📊 No open positions to close")
                return
            
            # Close confirmation
            keyboard = []
            for pos in positions:
                keyboard.append([InlineKeyboardButton(
                    f"Close {pos['symbol']} ({pos['side']})",
                    callback_data=f"confirm_close_{pos['symbol']}"
                )])
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
            
            await update.message.reply_text(
                "⚠️ *Close Position*\n\nSelect position to close:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Close command error: {e}")
            await update.message.reply_text("Error processing close")
    
    async def _cmd_sentiment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /sentiment command."""
        try:
            if not self.sentiment_agent:
                await update.message.reply_text("Sentiment analysis not configured")
                return
            
            await update.message.reply_text("🔍 Analyzing market sentiment...")
            
            detailed = await self.sentiment_agent.get_detailed_sentiment()
            
            overall = detailed.get('overall', 'Neutral')
            score = detailed.get('overall_score', 0)
            emoji = self.sentiment_agent.get_sentiment_emoji(overall)
            
            message = f"{emoji} *Market Sentiment*\n\n"
            message += f"📊 Overall: *{overall}* ({score:+.2f})\n\n"
            
            # Source breakdown
            sources = detailed.get('sources', {})
            if sources:
                message += "*Sources:*\n"
                for source, data in sources.items():
                    src_emoji = self.sentiment_agent.get_sentiment_emoji(data.get('sentiment', 'Neutral'))
                    message += f"• {source}: {src_emoji} {data.get('sentiment')} ({data.get('score', 0):+.2f})\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Sentiment command error: {e}")
            await update.message.reply_text("Error getting sentiment")
    
    async def _cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /performance command."""
        try:
            trades_df = get_trade_history(days=30)
            
            if trades_df.empty:
                await update.message.reply_text("📊 No trades in the last 30 days")
                return
            
            metrics = calculate_performance_metrics(trades_df)
            
            message = (
                "📊 *30-Day Performance*\n\n"
                f"📈 Total Trades: {metrics['total_trades']}\n"
                f"✅ Winning: {metrics['winning_trades']}\n"
                f"❌ Losing: {metrics['losing_trades']}\n"
                f"🎯 Win Rate: {metrics['win_rate']:.1f}%\n"
                f"💰 Total P&L: ${fmt_money(metrics['total_pnl'])}\n"
                f"📊 Avg P&L: ${fmt_money(metrics['average_pnl'])}\n"
                f"🏆 Best Trade: ${fmt_money(metrics['best_trade'])}\n"
                f"📉 Worst Trade: ${fmt_money(metrics['worst_trade'])}\n"
                f"📈 Profit Factor: {metrics['profit_factor']:.2f}\n"
            )
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Performance command error: {e}")
            await update.message.reply_text("Error getting performance")
    
    async def _cmd_strategies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /strategies command."""
        strategies = get_available_strategies()
        
        message = "🎯 *Available Strategies*\n\n"
        for i, strategy in enumerate(strategies, 1):
            message += f"{i}. `{strategy}`\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    # ==========================================
    # CALLBACK HANDLERS
    # ==========================================
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        try:
            if data == "cancel":
                await query.edit_message_text("❌ Cancelled")
                return
            
            if data.startswith("trade_symbol_"):
                await self._handle_symbol_selection(query, context)
            
            elif data.startswith("trade_side_"):
                await self._handle_side_selection(query, context)
            
            elif data.startswith("trade_leverage_"):
                await self._handle_leverage_selection(query, context)
            
            elif data.startswith("trade_confirm_"):
                await self._handle_trade_confirm(query, context)
            
            elif data.startswith("confirm_close_"):
                await self._handle_close_confirm(query, context)
            
            elif data.startswith("close_"):
                symbol = data.replace("close_", "")
                await self._prompt_close_confirmation(query, symbol)
                
        except Exception as e:
            logger.error(f"Callback error: {e}")
            await query.edit_message_text(f"Error: {str(e)}")
    
    async def _handle_symbol_selection(self, query, context):
        """Handle symbol selection in trade flow."""
        symbol = query.data.replace("trade_symbol_", "")
        
        # Store in pending trade
        user_id = query.from_user.id
        self._pending_trades[user_id] = {'symbol': symbol}
        
        # Get current price
        price = await self.bybit_client.get_current_price(symbol)
        
        # Side selection
        keyboard = [
            [
                InlineKeyboardButton("📈 Long (Buy)", callback_data=f"trade_side_{symbol}_Buy"),
                InlineKeyboardButton("📉 Short (Sell)", callback_data=f"trade_side_{symbol}_Sell")
            ],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel")]
        ]
        
        await query.edit_message_text(
            f"📊 *{symbol}*\n\n"
            f"💰 Current Price: ${fmt_money(price)}\n\n"
            "Select direction:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_side_selection(self, query, context):
        """Handle side selection in trade flow."""
        parts = query.data.replace("trade_side_", "").split("_")
        symbol = parts[0]
        side = parts[1]
        
        user_id = query.from_user.id
        if user_id in self._pending_trades:
            self._pending_trades[user_id]['side'] = side
        else:
            self._pending_trades[user_id] = {'symbol': symbol, 'side': side}
        
        # Leverage selection
        leverages = [1, 2, 3, 5, 10, 20]
        keyboard = []
        row = []
        for lev in leverages:
            row.append(InlineKeyboardButton(
                f"{lev}x",
                callback_data=f"trade_leverage_{symbol}_{side}_{lev}"
            ))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel")])
        
        side_emoji = "📈 Long" if side == "Buy" else "📉 Short"
        
        await query.edit_message_text(
            f"📊 *{symbol}* - {side_emoji}\n\n"
            "Select leverage:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_leverage_selection(self, query, context):
        """Handle leverage selection in trade flow."""
        parts = query.data.replace("trade_leverage_", "").split("_")
        symbol = parts[0]
        side = parts[1]
        leverage = int(parts[2])
        
        user_id = query.from_user.id
        self._pending_trades[user_id] = {
            'symbol': symbol,
            'side': side,
            'leverage': leverage
        }
        
        # Get balance and calculate size
        balance = await self.bybit_client.get_wallet_balance()
        available = balance.get('available', 0)
        price = await self.bybit_client.get_current_price(symbol)
        
        risk_percent = self.config.get('trading', {}).get('risk_per_trade_percent', 2.0)
        risk_amount = available * (risk_percent / 100)
        
        # Confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"trade_confirm_{symbol}_{side}_{leverage}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]
        ]
        
        side_emoji = "📈 Long" if side == "Buy" else "📉 Short"
        
        await query.edit_message_text(
            f"📊 *Trade Confirmation*\n\n"
            f"Symbol: *{symbol}*\n"
            f"Direction: {side_emoji}\n"
            f"Leverage: *{leverage}x*\n"
            f"Price: ${fmt_money(price)}\n"
            f"Risk: ${fmt_money(risk_amount)} ({risk_percent}%)\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_trade_confirm(self, query, context):
        """Handle trade confirmation."""
        parts = query.data.replace("trade_confirm_", "").split("_")
        symbol = parts[0]
        side = parts[1]
        leverage = int(parts[2])
        
        await query.edit_message_text("⏳ Executing trade...")
        
        is_paper = self.config.get('trading_flags', {}).get('paper_trading', True)
        direction = "BUY" if side == "Buy" else "SELL"
        
        if is_paper:
            trade = await self.order_agent.get_paper_trade_details(direction, symbol, leverage)
        else:
            trade = await self.order_agent.place_trade(direction, symbol, leverage)
        
        if trade:
            self.position_agent.start_trade(trade)
            
            mode = "📝 Paper" if is_paper else "💰 Live"
            side_emoji = "📈" if side == "Buy" else "📉"
            
            await query.edit_message_text(
                f"✅ *Trade Executed*\n\n"
                f"Symbol: *{symbol}*\n"
                f"Direction: {side_emoji} {side}\n"
                f"Entry: ${fmt_money(trade.get('entry_price', 0))}\n"
                f"Size: {trade.get('quantity', 0)}\n"
                f"Leverage: {leverage}x\n"
                f"Mode: {mode}\n"
                f"Order ID: `{trade.get('order_id', 'N/A')}`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ Trade execution failed")
    
    async def _prompt_close_confirmation(self, query, symbol: str):
        """Prompt for close confirmation."""
        keyboard = [
            [
                InlineKeyboardButton("✅ Yes, Close", callback_data=f"confirm_close_{symbol}"),
                InlineKeyboardButton("❌ No, Cancel", callback_data="cancel")
            ]
        ]
        
        await query.edit_message_text(
            f"⚠️ Close {symbol} position?\n\nThis action cannot be undone.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _handle_close_confirm(self, query, context):
        """Handle close confirmation."""
        symbol = query.data.replace("confirm_close_", "")
        
        await query.edit_message_text("⏳ Closing position...")
        
        result = await self.bybit_client.close_position(symbol)
        
        if result.get('ok'):
            await query.edit_message_text(f"✅ Position closed for {symbol}")
        else:
            await query.edit_message_text(f"❌ Failed to close: {result.get('error')}")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        # Can be used for custom amount input, etc.
        pass
    
    # ==========================================
    # NOTIFICATION METHODS
    # ==========================================
    
    async def send_startup_message(self):
        """Send startup notification."""
        if not self.app or not self.chat_id:
            return
        
        try:
            mode = self.bybit_client.get_mode() if self.bybit_client else "Unknown"
            is_paper = self.config.get('trading_flags', {}).get('paper_trading', True)
            trading_mode = "📝 Paper Trading" if is_paper else "💰 Live Trading"
            
            message = (
                "🚀 *Trading Bot Started*\n\n"
                f"🔗 Bybit: {mode}\n"
                f"🎯 Mode: {trading_mode}\n\n"
                "Use /help for available commands"
            )
            
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send startup message: {e}")
    
    async def send_trade_signal(self, signal: str, symbol: str, price: float, confidence: float):
        """Send trade signal notification."""
        if not self.app or not self.chat_id:
            return
        
        try:
            emoji = "📈" if signal == "BUY" else "📉" if signal == "SELL" else "➡️"
            
            message = (
                f"{emoji} *Trading Signal*\n\n"
                f"Symbol: *{symbol}*\n"
                f"Signal: *{signal}*\n"
                f"Price: ${fmt_money(price)}\n"
                f"Confidence: {confidence:.1%}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ Execute", callback_data=f"trade_symbol_{symbol}"),
                    InlineKeyboardButton("❌ Skip", callback_data="cancel")
                ]
            ]
            
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send trade signal: {e}")
    
    async def send_position_update(self, position: Dict[str, Any]):
        """Send position update notification."""
        if not self.app or not self.chat_id:
            return
        
        try:
            pnl = position.get('unrealized_pnl', 0)
            pnl_pct = position.get('unrealized_pnl_percent', 0)
            emoji = "💰" if pnl >= 0 else "🔻"
            
            message = (
                f"{emoji} *Position Update*\n\n"
                f"Symbol: {position.get('symbol')}\n"
                f"P&L: ${fmt_money(pnl)} ({pnl_pct:+.2f}%)"
            )
            
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send position update: {e}")

