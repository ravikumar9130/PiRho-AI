"""
Crypto Sentiment Analysis Agent
Analyzes news sentiment, Fear & Greed Index, and social signals for crypto markets
"""

import logging
import datetime
import json
import os
import time
import asyncio
import ssl
import aiohttp
from typing import Optional, Dict, Any, List

try:
    from newsapi import NewsApiClient
    HAS_NEWSAPI = True
except ImportError:
    HAS_NEWSAPI = False

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False

logger = logging.getLogger(__name__)


class CryptoSentimentAgent:
    """
    Agent for fetching crypto news and determining market sentiment.
    Includes Fear & Greed Index, CryptoPanic, and traditional news sources.
    """
    
    # Sentiment score thresholds
    VERY_BULLISH_THRESHOLD = 0.4
    BULLISH_THRESHOLD = 0.05
    BEARISH_THRESHOLD = -0.05
    VERY_BEARISH_THRESHOLD = -0.4
    
    def __init__(self, config: dict):
        """
        Initialize the crypto sentiment agent.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        sentiment_config = config.get('sentiment', {})
        
        # API Keys
        self.news_api_key = sentiment_config.get('news_api_key', '')
        self.cryptopanic_api_key = sentiment_config.get('cryptopanic_api_key', '')
        self.use_fear_greed = sentiment_config.get('use_fear_greed_index', True)
        
        # Initialize NewsAPI client if available
        self.newsapi = None
        if HAS_NEWSAPI and self.news_api_key:
            try:
                self.newsapi = NewsApiClient(api_key=self.news_api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize NewsAPI: {e}")
        
        # Cache configuration
        self.cache_dir = "news_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_expiration_seconds = 3600  # 1 hour
        
        # Crypto-specific keywords
        self.keywords = sentiment_config.get('keywords', [
            "Bitcoin", "Ethereum", "Crypto", "Cryptocurrency",
            "Fed", "Interest Rate", "Regulation", "SEC", "ETF",
            "Halving", "Whale", "DeFi", "Blockchain"
        ])
        
        # Symbol-specific keywords
        self.symbol_keywords = {
            "BTCUSDT": ["Bitcoin", "BTC", "Satoshi"],
            "ETHUSDT": ["Ethereum", "ETH", "Vitalik"],
            "SOLUSDT": ["Solana", "SOL"],
            "BNBUSDT": ["Binance", "BNB"],
            "XRPUSDT": ["Ripple", "XRP"],
            "DOGEUSDT": ["Dogecoin", "DOGE", "Elon"],
        }
        
        # Last sentiment cache
        self._last_sentiment = None
        self._last_sentiment_time = None
    
    async def get_market_sentiment(self, symbol: Optional[str] = None) -> str:
        """
        Get overall market sentiment from multiple sources.
        
        Args:
            symbol: Optional symbol to focus sentiment on
            
        Returns:
            Sentiment string: "Very Bullish", "Bullish", "Neutral", "Bearish", "Very Bearish"
        """
        try:
            # Check cache (sentiment valid for 30 minutes)
            if (self._last_sentiment and self._last_sentiment_time and 
                (datetime.datetime.now() - self._last_sentiment_time).seconds < 1800):
                return self._last_sentiment
            
            scores = []
            weights = []
            
            # Fear & Greed Index (weight: 2)
            if self.use_fear_greed:
                fg_score = await self._get_fear_greed_score()
                if fg_score is not None:
                    scores.append(fg_score)
                    weights.append(2)
            
            # CryptoPanic news (weight: 1.5)
            if self.cryptopanic_api_key:
                cp_score = await self._get_cryptopanic_sentiment(symbol)
                if cp_score is not None:
                    scores.append(cp_score)
                    weights.append(1.5)
            
            # General news (weight: 1)
            if self.newsapi:
                news_score = await self._get_news_sentiment(symbol)
                if news_score is not None:
                    scores.append(news_score)
                    weights.append(1)
            
            if not scores:
                logger.warning("No sentiment data available, defaulting to Neutral")
                return "Neutral"
            
            # Calculate weighted average
            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            total_weight = sum(weights)
            avg_score = weighted_sum / total_weight
            
            # Convert to sentiment string
            sentiment = self._score_to_sentiment(avg_score)
            
            # Cache result
            self._last_sentiment = sentiment
            self._last_sentiment_time = datetime.datetime.now()
            
            logger.info(f"Market Sentiment: {sentiment} (score: {avg_score:.3f})")
            return sentiment
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return "Neutral"
    
    async def _get_fear_greed_score(self) -> Optional[float]:
        """
        Fetch the Crypto Fear & Greed Index and convert to normalized score.
        
        Returns:
            Score from -1 (Extreme Fear) to 1 (Extreme Greed), or None if failed
        """
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
            
            if data and 'data' in data and data['data']:
                value = int(data['data'][0]['value'])  # 0-100
                classification = data['data'][0]['value_classification']
                
                # Normalize to -1 to 1 scale
                # 0-25: Extreme Fear (-1 to -0.5)
                # 25-45: Fear (-0.5 to 0)
                # 45-55: Neutral (0)
                # 55-75: Greed (0 to 0.5)
                # 75-100: Extreme Greed (0.5 to 1)
                normalized_score = (value - 50) / 50
                
                logger.info(f"Fear & Greed Index: {value} ({classification})")
                return normalized_score
                
        except Exception as e:
            logger.warning(f"Failed to fetch Fear & Greed Index: {e}")
        
        return None
    
    async def _get_cryptopanic_sentiment(self, symbol: Optional[str] = None) -> Optional[float]:
        """
        Fetch sentiment from CryptoPanic API.
        
        Args:
            symbol: Optional symbol to filter news
            
        Returns:
            Sentiment score from -1 to 1, or None if failed
        """
        if not self.cryptopanic_api_key:
            return None
        
        try:
            # Build URL with filters
            base_url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": self.cryptopanic_api_key,
                "kind": "news",
                "filter": "hot",
            }
            
            # Add currency filter if symbol provided
            if symbol:
                currency = symbol.replace("USDT", "")
                params["currencies"] = currency
            
            url = f"{base_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
            
            if not data or 'results' not in data:
                return None
            
            # Calculate sentiment from vote counts
            positive_votes = 0
            negative_votes = 0
            
            for post in data['results'][:20]:  # Analyze top 20 posts
                votes = post.get('votes', {})
                positive_votes += votes.get('positive', 0) + votes.get('liked', 0)
                negative_votes += votes.get('negative', 0) + votes.get('disliked', 0)
            
            total_votes = positive_votes + negative_votes
            if total_votes == 0:
                return 0
            
            score = (positive_votes - negative_votes) / total_votes
            logger.debug(f"CryptoPanic sentiment: {score:.3f} (pos: {positive_votes}, neg: {negative_votes})")
            
            return score
            
        except Exception as e:
            logger.warning(f"Failed to fetch CryptoPanic sentiment: {e}")
        
        return None
    
    async def _get_news_sentiment(self, symbol: Optional[str] = None) -> Optional[float]:
        """
        Fetch and analyze news sentiment from NewsAPI.
        
        Args:
            symbol: Optional symbol to focus on
            
        Returns:
            Sentiment score from -1 to 1, or None if failed
        """
        if not self.newsapi or not HAS_TEXTBLOB:
            return None
        
        try:
            today = datetime.date.today()
            from_date = today - datetime.timedelta(days=2)
            cache_file = os.path.join(self.cache_dir, f"news_{today.isoformat()}.json")
            
            # Check cache
            if os.path.exists(cache_file):
                cache_age = time.time() - os.path.getmtime(cache_file)
                if cache_age < self.cache_expiration_seconds:
                    logger.debug("Loading news from cache")
                    with open(cache_file, 'r') as f:
                        articles = json.load(f)
                else:
                    articles = await self._fetch_news_articles(symbol, from_date, today)
            else:
                articles = await self._fetch_news_articles(symbol, from_date, today)
            
            if not articles:
                return None
            
            # Analyze sentiment
            sentiment_scores = []
            for article in articles[:50]:  # Limit to 50 articles
                title = article.get('title', '')
                description = article.get('description', '')
                
                if title and title != "[Removed]":
                    content = f"{title}. {description}"
                    blob = TextBlob(content)
                    sentiment_scores.append(blob.sentiment.polarity)
            
            if not sentiment_scores:
                return None
            
            # Weighted average (newer = higher weight)
            weighted_sum = 0
            total_weight = 0
            n = len(sentiment_scores)
            
            for i, score in enumerate(sentiment_scores):
                weight = n - i
                weighted_sum += score * weight
                total_weight += weight
            
            avg_score = weighted_sum / total_weight if total_weight > 0 else 0
            logger.debug(f"News sentiment score: {avg_score:.3f}")
            
            return avg_score
            
        except Exception as e:
            logger.warning(f"Failed to get news sentiment: {e}")
        
        return None
    
    async def _fetch_news_articles(
        self, 
        symbol: Optional[str], 
        from_date: datetime.date,
        to_date: datetime.date
    ) -> List[Dict[str, Any]]:
        """Fetch news articles from NewsAPI."""
        try:
            # Build query
            keywords = self.keywords.copy()
            if symbol and symbol in self.symbol_keywords:
                keywords.extend(self.symbol_keywords[symbol])
            
            query = " OR ".join(f'"{kw}"' for kw in keywords[:10])
            
            logger.debug(f"Fetching news with query: {query}")
            
            result = await asyncio.to_thread(
                self.newsapi.get_everything,
                q=query,
                language='en',
                sort_by='publishedAt',
                page_size=100,
                from_param=from_date.isoformat(),
                to=to_date.isoformat()
            )
            
            articles = result.get('articles', [])
            
            # Cache results
            today = datetime.date.today()
            cache_file = os.path.join(self.cache_dir, f"news_{today.isoformat()}.json")
            with open(cache_file, 'w') as f:
                json.dump(articles, f)
            
            return articles
            
        except Exception as e:
            logger.warning(f"Failed to fetch news articles: {e}")
            return []
    
    def _score_to_sentiment(self, score: float) -> str:
        """
        Convert numerical score to sentiment string.
        
        Args:
            score: Score from -1 to 1
            
        Returns:
            Sentiment string
        """
        if score >= self.VERY_BULLISH_THRESHOLD:
            return "Very Bullish"
        elif score >= self.BULLISH_THRESHOLD:
            return "Bullish"
        elif score <= self.VERY_BEARISH_THRESHOLD:
            return "Very Bearish"
        elif score <= self.BEARISH_THRESHOLD:
            return "Bearish"
        else:
            return "Neutral"
    
    async def get_detailed_sentiment(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed sentiment breakdown from all sources.
        
        Args:
            symbol: Optional symbol to focus on
            
        Returns:
            Dictionary with detailed sentiment data
        """
        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'symbol': symbol,
            'sources': {},
            'overall': 'Neutral',
            'overall_score': 0.0,
        }
        
        try:
            scores = []
            weights = []
            
            # Fear & Greed
            if self.use_fear_greed:
                fg_score = await self._get_fear_greed_score()
                if fg_score is not None:
                    result['sources']['fear_greed'] = {
                        'score': fg_score,
                        'sentiment': self._score_to_sentiment(fg_score),
                        'weight': 2,
                    }
                    scores.append(fg_score)
                    weights.append(2)
            
            # CryptoPanic
            if self.cryptopanic_api_key:
                cp_score = await self._get_cryptopanic_sentiment(symbol)
                if cp_score is not None:
                    result['sources']['cryptopanic'] = {
                        'score': cp_score,
                        'sentiment': self._score_to_sentiment(cp_score),
                        'weight': 1.5,
                    }
                    scores.append(cp_score)
                    weights.append(1.5)
            
            # News
            if self.newsapi:
                news_score = await self._get_news_sentiment(symbol)
                if news_score is not None:
                    result['sources']['news'] = {
                        'score': news_score,
                        'sentiment': self._score_to_sentiment(news_score),
                        'weight': 1,
                    }
                    scores.append(news_score)
                    weights.append(1)
            
            # Calculate overall
            if scores:
                weighted_sum = sum(s * w for s, w in zip(scores, weights))
                total_weight = sum(weights)
                result['overall_score'] = weighted_sum / total_weight
                result['overall'] = self._score_to_sentiment(result['overall_score'])
            
        except Exception as e:
            logger.error(f"Error getting detailed sentiment: {e}")
        
        return result
    
    def get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment display."""
        emojis = {
            "Very Bullish": "🚀",
            "Bullish": "📈",
            "Neutral": "➡️",
            "Bearish": "📉",
            "Very Bearish": "🔻",
        }
        return emojis.get(sentiment, "❓")


# Backward compatibility alias
SentimentAgent = CryptoSentimentAgent
