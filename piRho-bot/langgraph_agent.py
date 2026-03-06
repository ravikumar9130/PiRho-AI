"""
AI Strategy Selection Agent using OpenAI
Recommends optimal trading strategies based on market conditions
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List

try:
    from openai import AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    AsyncOpenAI = None
    HAS_OPENAI = False

from strategy_factory import get_available_strategies

logger = logging.getLogger(__name__)


class LangGraphAgent:
    """
    AI agent using OpenAI API to recommend trading strategies
    for crypto perpetual futures.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the LangGraph agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        ai_config = config.get('ai', {})
        
        self.api_key = ai_config.get('openai_api_key', '')
        self.model_name = ai_config.get('openai_model', 'gpt-4o-mini')
        
        # Initialize OpenAI client
        self.client = None
        if HAS_OPENAI and self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
        
        # Strategy descriptions for the AI
        self.strategy_descriptions = {
            "LSTM_Momentum": "ML-based strategy using LSTM neural network for price prediction with technical confirmation.",
            "Supertrend_MACD": "Strong trend-following strategy combining Supertrend indicator with MACD crossovers.",
            "Volatility_Cluster_Reversal": "Counter-trend strategy for high volatility environments, looking for exhaustion moves.",
            "Volume_Spread_Analysis": "Detects smart money activity through volume and price spread analysis.",
            "EMA_Cross_RSI": "Fast-acting momentum strategy using EMA crossovers with RSI confirmation.",
            "Momentum_VWAP_RSI": "Intraday momentum strategy using VWAP and RSI alignment.",
            "BB_Squeeze_Breakout": "Volatility breakout strategy based on Bollinger Band squeeze patterns.",
            "MA_Crossover": "Classic moving average crossover strategy (9/21 EMA).",
            "RSI_Divergence": "Pure reversal strategy detecting RSI divergences from price.",
            "Reversal_Detector": "Advanced reversal detection for overextended trends with momentum divergence.",
            "Funding_Rate": "Crypto-specific strategy using funding rate extremes for contrarian entries.",
        }
    
    async def get_recommended_strategy(
        self,
        market_conditions: Dict[str, Any],
        sentiment: str = "Neutral",
        user_prompt: Optional[str] = None,
        symbol: str = "BTCUSDT"
    ) -> str:
        """
        Get AI-recommended strategy based on current market conditions.
        
        Args:
            market_conditions: Dictionary with market data (volatility, trend, etc.)
            sentiment: Current market sentiment
            user_prompt: Optional user preference or observation
            symbol: Trading symbol
            
        Returns:
            Recommended strategy name
        """
        if not self.client:
            logger.warning("[OpenAI Agent] No API key configured, using default strategy")
            return "Supertrend_MACD"
        
        try:
            prompt = self._build_prompt(market_conditions, sentiment, user_prompt, symbol)
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert cryptocurrency trading strategist. Respond with only the strategy name, nothing else."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=50,
            )
            
            # Extract strategy name from response
            response_text = response.choices[0].message.content.strip()
            recommended = self._parse_strategy_response(response_text)
            
            logger.info(f"[OpenAI Agent] Recommended strategy: {recommended}")
            return recommended
            
        except asyncio.TimeoutError:
            logger.error("[OpenAI Agent] API request timed out")
            return "Supertrend_MACD"
        except Exception as e:
            logger.error(f"[OpenAI Agent] Error: {e}")
            return "Supertrend_MACD"
    
    def _build_prompt(
        self,
        market_conditions: Dict[str, Any],
        sentiment: str,
        user_prompt: Optional[str],
        symbol: str
    ) -> str:
        """Build the prompt for strategy recommendation."""
        
        sections = [
            "You are an expert cryptocurrency trading strategist specializing in perpetual futures.",
            "Your task is to select the single best trading strategy for the current market conditions.",
            "",
            f"**Trading Symbol:** {symbol}",
            f"**Current Sentiment:** {sentiment}",
            "",
            "**Market Conditions:**",
        ]
        
        # Add market condition details
        for key, value in market_conditions.items():
            sections.append(f"- {key}: {value}")
        
        # Add user input if provided
        if user_prompt:
            sections.append("")
            sections.append(f"**Trader's Observation:** {user_prompt}")
        
        # Add available strategies
        sections.append("")
        sections.append("**Available Strategies:**")
        
        for i, (name, desc) in enumerate(self.strategy_descriptions.items(), 1):
            sections.append(f"{i}. **{name}**: {desc}")
        
        # Add decision criteria
        sections.append("")
        sections.append("**Selection Criteria:**")
        sections.append("- For trending markets: Prefer Supertrend_MACD, MA_Crossover, EMA_Cross_RSI")
        sections.append("- For ranging/volatile markets: Prefer BB_Squeeze_Breakout, Volatility_Cluster_Reversal")
        sections.append("- For high volume activity: Prefer Volume_Spread_Analysis")
        sections.append("- For overextended trends: Prefer Reversal_Detector, RSI_Divergence")
        sections.append("- For extreme funding rates: Prefer Funding_Rate strategy")
        sections.append("- When uncertain: Prefer Supertrend_MACD for reliable trend following")
        sections.append("")
        sections.append("Based on all the above, which single strategy name has the highest probability of success? Return ONLY the strategy name, nothing else.")
        
        return "\n".join(sections)
    
    def _parse_strategy_response(self, response: str) -> str:
        """Parse and validate the strategy name from AI response."""
        
        # Clean up response
        response = response.strip().replace("'", "").replace('"', "")
        
        # Try to extract strategy name
        valid_strategies = get_available_strategies()
        
        # Check for exact match
        for strategy in valid_strategies:
            if strategy.lower() == response.lower():
                return strategy
            if strategy.lower() in response.lower():
                return strategy
        
        # Check if any strategy name is contained in response
        for line in response.split('\n'):
            for strategy in valid_strategies:
                if strategy in line:
                    return strategy
        
        logger.warning(f"[OpenAI Agent] Could not parse strategy from: {response}")
        return "Supertrend_MACD"
    
    async def analyze_trade_loss(
        self,
        trade_details: Dict[str, Any],
        market_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze a losing trade and provide insights.
        
        Args:
            trade_details: Dictionary with trade information
            market_data: Optional market snapshot at trade time
            
        Returns:
            Analysis text
        """
        if not self.client:
            return "Analysis unavailable - No API key configured"
        
        try:
            prompt_parts = [
                "You are a crypto trading analyst. Analyze this losing trade and provide brief insights.",
                "",
                "**Trade Details:**",
                f"- Symbol: {trade_details.get('Symbol', 'Unknown')}",
                f"- Direction: {trade_details.get('TradeType', 'Unknown')}",
                f"- Entry: ${trade_details.get('EntryPrice', 0):.2f}",
                f"- Exit: ${trade_details.get('ExitPrice', 0):.2f}",
                f"- P&L: ${trade_details.get('ProfitLoss', 0):.2f}",
                f"- Strategy: {trade_details.get('Strategy', 'Unknown')}",
                f"- Exit Reason: {trade_details.get('ExitReason', 'Unknown')}",
            ]
            
            if market_data:
                prompt_parts.append("")
                prompt_parts.append("**Market Context:**")
                for key, value in market_data.items():
                    prompt_parts.append(f"- {key}: {value}")
            
            prompt_parts.append("")
            prompt_parts.append("Provide a brief 2-3 sentence analysis of what went wrong and one improvement suggestion.")
            
            prompt = "\n".join(prompt_parts)
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional crypto trading analyst. Provide concise, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=200,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"[OpenAI Agent] Analysis error: {e}")
            return f"Analysis failed: {str(e)}"
    
    async def get_market_outlook(
        self,
        symbol: str,
        timeframe: str,
        indicators: Dict[str, Any],
        sentiment: str
    ) -> Dict[str, Any]:
        """
        Get AI-generated market outlook.
        
        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
            indicators: Current indicator values
            sentiment: Market sentiment
            
        Returns:
            Dictionary with outlook details
        """
        if not self.client:
            return {
                "outlook": "Neutral",
                "confidence": 0.5,
                "summary": "AI analysis unavailable"
            }
        
        try:
            prompt = f"""Analyze the following crypto market data and provide a brief outlook.

Symbol: {symbol}
Timeframe: {timeframe}
Sentiment: {sentiment}

Indicators:
- RSI: {indicators.get('rsi', 'N/A')}
- MACD: {indicators.get('macd', 'N/A')} (Signal: {indicators.get('macd_signal', 'N/A')})
- Price vs EMA50: {indicators.get('price_vs_ema50', 'N/A')}
- Supertrend: {indicators.get('supertrend_direction', 'N/A')}

Respond with JSON format:
{{"outlook": "Bullish/Bearish/Neutral", "confidence": 0.0-1.0, "summary": "brief summary"}}
"""
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a crypto market analyst. Respond only with valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=150,
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            import json
            try:
                # Find JSON in response
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    return json.loads(response_text[start:end])
            except json.JSONDecodeError:
                pass
            
            return {
                "outlook": "Neutral",
                "confidence": 0.5,
                "summary": response_text[:200]
            }
            
        except Exception as e:
            logger.error(f"[OpenAI Agent] Outlook error: {e}")
            return {
                "outlook": "Neutral",
                "confidence": 0.5,
                "summary": f"Error: {str(e)}"
            }
