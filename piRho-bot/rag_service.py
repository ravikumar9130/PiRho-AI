"""
RAG Service - Retrieval Augmented Generation for Trading Context

This service provides historical trade performance context to enhance
AI strategy selection and loss analysis.

NOTE: This is a minimal implementation. For full functionality,
implement proper vector database integration and semantic search.
"""

import logging
import os
import pandas as pd
from typing import Optional, Dict, Any

class RAGService:
    """
    Retrieves historical trading context for AI-powered decision making.
    """
    
    def __init__(self, config: dict):
        """
        Initialize RAG Service.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.trade_log_path = "output/trade_log.xlsx"
        os.makedirs('output', exist_ok=True)
        logging.info("RAGService initialized")
    
    def _load_data(self, path: str) -> Optional[pd.DataFrame]:
        """
        Load trade log data from Excel file.
        
        Args:
            path: Path to trade log Excel file
            
        Returns:
            DataFrame with trade data or None if file doesn't exist
        """
        try:
            if os.path.exists(path) and os.path.getsize(path) > 0:
                df = pd.read_excel(path)
                logging.debug(f"Loaded {len(df)} trades from {path}")
                return df
            else:
                logging.debug(f"Trade log file not found or empty: {path}")
                return pd.DataFrame()
        except Exception as e:
            logging.error(f"Failed to load trade log from {path}: {e}")
            return pd.DataFrame()
    
    def retrieve_context_for_strategy_selection(self, market_conditions: set) -> Optional[str]:
        """
        Retrieve historical performance context for strategy selection.
        
        This method analyzes past trades to find which strategies performed
        best under similar market conditions.
        
        Args:
            market_conditions: Set of current market condition tags
                (e.g., {'VIX_HIGH', 'IV_HIGH'})
                
        Returns:
            String containing historical context or None if insufficient data
        """
        try:
            df = self._load_data(self.trade_log_path)
            
            if df.empty or 'Strategy' not in df.columns:
                logging.debug("No historical data available for RAG context")
                return None
            
            # Filter trades by market conditions (if we had condition tags in log)
            # For now, analyze overall strategy performance
            
            strategy_performance = {}
            for strategy in df['Strategy'].unique():
                strategy_trades = df[df['Strategy'] == strategy]
                if len(strategy_trades) > 0:
                    wins = (strategy_trades['ProfitLoss'] > 0).sum()
                    total = len(strategy_trades)
                    win_rate = (wins / total * 100) if total > 0 else 0
                    avg_pnl = strategy_trades['ProfitLoss'].mean()
                    strategy_performance[strategy] = {
                        'win_rate': win_rate,
                        'avg_pnl': avg_pnl,
                        'total_trades': total
                    }
            
            if not strategy_performance:
                return None
            
            # Build context string
            context_parts = ["Historical Strategy Performance:\n"]
            for strategy, perf in sorted(strategy_performance.items(), 
                                       key=lambda x: x[1]['win_rate'], 
                                       reverse=True):
                context_parts.append(
                    f"- {strategy}: {perf['win_rate']:.1f}% win rate, "
                    f"avg P/L: {perf['avg_pnl']:.2f}, "
                    f"trades: {perf['total_trades']}"
                )
            
            context = "\n".join(context_parts)
            logging.info("RAG context generated for strategy selection")
            return context
            
        except Exception as e:
            logging.error(f"Error retrieving strategy selection context: {e}")
            return None
    
    def retrieve_context_for_loss_analysis(self, trade_details: Dict[str, Any]) -> Optional[str]:
        """
        Retrieve historical context for analyzing losing trades.
        
        This method finds similar losing trades from history to provide
        context for understanding why a trade failed.
        
        Args:
            trade_details: Dictionary containing trade information
                (Symbol, Strategy, EntryPrice, ExitPrice, ProfitLoss, etc.)
                
        Returns:
            String containing relevant historical context or None
        """
        try:
            df = self._load_data(self.trade_log_path)
            
            if df.empty:
                return None
            
            # Find similar losing trades
            strategy = trade_details.get('Strategy', '')
            symbol = trade_details.get('Symbol', '')
            
            similar_trades = df[
                (df['ProfitLoss'] < 0) &  # Only losing trades
                (df['Strategy'] == strategy)  # Same strategy
            ]
            
            if len(similar_trades) == 0:
                return None
            
            # Analyze patterns in similar losing trades
            avg_loss = similar_trades['ProfitLoss'].mean()
            common_reasons = []
            
            if 'Rationale' in similar_trades.columns:
                # If we have AI-generated rationales, summarize them
                rationales = similar_trades['Rationale'].dropna()
                if len(rationales) > 0:
                    common_reasons.append(
                        f"Found {len(similar_trades)} similar losing trades "
                        f"with average loss of {avg_loss:.2f}"
                    )
            
            context = "\n".join(common_reasons) if common_reasons else None
            logging.debug("RAG context generated for loss analysis")
            return context
            
        except Exception as e:
            logging.error(f"Error retrieving loss analysis context: {e}")
            return None

