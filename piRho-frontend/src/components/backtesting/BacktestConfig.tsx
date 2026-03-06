"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  BacktestRequest,
  IndicatorConfig,
  BacktestConfig as BacktestConfigType,
} from "@/lib/api";
import {
  Settings2,
  TrendingUp,
  Calendar,
  ChevronDown,
  ChevronRight,
  Gauge,
  BarChart3,
  Target,
  Percent,
  DollarSign,
  Clock,
} from "lucide-react";

interface BacktestConfigProps {
  strategies: string[];
  symbols: string[];
  onSubmit: (config: BacktestRequest) => void;
  isLoading: boolean;
}

export function BacktestConfigForm({
  strategies,
  symbols,
  onSubmit,
  isLoading,
}: BacktestConfigProps) {
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [strategy, setStrategy] = useState(strategies[0] || "MA_Crossover");
  const [timeframe, setTimeframe] = useState("15");
  const [startDate, setStartDate] = useState(() => {
    const date = new Date();
    date.setMonth(date.getMonth() - 3);
    return date.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().split("T")[0];
  });
  const [saveResult, setSaveResult] = useState(false);

  // Config settings
  const [initialCapital, setInitialCapital] = useState(10000);
  const [leverage, setLeverage] = useState(1);
  const [riskPerTrade, setRiskPerTrade] = useState(2.0);
  const [stopLoss, setStopLoss] = useState(2.0);
  const [takeProfit, setTakeProfit] = useState(4.0);
  const [useTrailingStop, setUseTrailingStop] = useState(false);
  const [trailingStop, setTrailingStop] = useState(1.5);
  const [slippage, setSlippage] = useState(0.1);
  const [commission, setCommission] = useState(0.06);

  // Indicator settings
  const [showIndicators, setShowIndicators] = useState(false);
  const [rsiPeriod, setRsiPeriod] = useState(14);
  const [rsiOverbought, setRsiOverbought] = useState(70);
  const [rsiOversold, setRsiOversold] = useState(30);
  const [macdFast, setMacdFast] = useState(12);
  const [macdSlow, setMacdSlow] = useState(26);
  const [macdSignal, setMacdSignal] = useState(9);
  const [emaShort, setEmaShort] = useState(9);
  const [emaMedium, setEmaMedium] = useState(21);
  const [emaLong, setEmaLong] = useState(50);
  const [emaTrend, setEmaTrend] = useState(200);
  const [bbPeriod, setBbPeriod] = useState(20);
  const [bbStdDev, setBbStdDev] = useState(2.0);
  const [atrPeriod, setAtrPeriod] = useState(14);
  const [stPeriod, setStPeriod] = useState(10);
  const [stMultiplier, setStMultiplier] = useState(3.0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const indicators: IndicatorConfig = {
      rsi_period: rsiPeriod,
      rsi_overbought: rsiOverbought,
      rsi_oversold: rsiOversold,
      macd_fast: macdFast,
      macd_slow: macdSlow,
      macd_signal: macdSignal,
      ema_short: emaShort,
      ema_medium: emaMedium,
      ema_long: emaLong,
      ema_trend: emaTrend,
      bb_period: bbPeriod,
      bb_std_dev: bbStdDev,
      atr_period: atrPeriod,
      supertrend_period: stPeriod,
      supertrend_multiplier: stMultiplier,
      vwap_enabled: true,
    };

    const config: BacktestConfigType = {
      initial_capital: initialCapital,
      leverage: leverage,
      risk_per_trade: riskPerTrade,
      stop_loss_percent: stopLoss,
      take_profit_percent: takeProfit,
      use_trailing_stop: useTrailingStop,
      trailing_stop_percent: trailingStop,
      slippage_percent: slippage,
      commission_percent: commission,
    };

    const request: BacktestRequest = {
      symbol,
      start_date: new Date(startDate).toISOString(),
      end_date: new Date(endDate).toISOString(),
      strategy,
      timeframe,
      indicators,
      config,
      save_result: saveResult,
    };

    onSubmit(request);
  };

  const timeframes = [
    { value: "1", label: "1m" },
    { value: "5", label: "5m" },
    { value: "15", label: "15m" },
    { value: "30", label: "30m" },
    { value: "60", label: "1h" },
    { value: "240", label: "4h" },
    { value: "D", label: "1D" },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Settings */}
      <div className="card-cyber p-6">
        <div className="flex items-center gap-2 mb-4">
          <Settings2 className="h-5 w-5 text-neon-400" />
          <h3 className="text-lg font-display font-semibold text-white">
            Basic Configuration
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Symbol */}
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Symbol
            </label>
            <select
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="input-cyber w-full"
            >
              {symbols.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Strategy */}
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              className="input-cyber w-full"
            >
              {strategies.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe */}
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Timeframe
            </label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="input-cyber w-full"
            >
              {timeframes.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label}
                </option>
              ))}
            </select>
          </div>

          {/* Start Date */}
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Start Date
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="input-cyber w-full pl-10"
              />
            </div>
          </div>

          {/* End Date */}
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              End Date
            </label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="input-cyber w-full pl-10"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Risk & Capital Settings */}
      <div className="card-cyber p-6">
        <div className="flex items-center gap-2 mb-4">
          <Target className="h-5 w-5 text-magenta-400" />
          <h3 className="text-lg font-display font-semibold text-white">
            Risk & Capital
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Initial Capital ($)
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="input-cyber w-full pl-10"
                min={100}
                max={10000000}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Leverage
            </label>
            <input
              type="number"
              value={leverage}
              onChange={(e) => setLeverage(Number(e.target.value))}
              className="input-cyber w-full"
              min={1}
              max={100}
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Risk Per Trade (%)
            </label>
            <div className="relative">
              <Percent className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-surface-500" />
              <input
                type="number"
                value={riskPerTrade}
                onChange={(e) => setRiskPerTrade(Number(e.target.value))}
                className="input-cyber w-full pl-10"
                min={0.1}
                max={20}
                step={0.1}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Stop Loss (%)
            </label>
            <input
              type="number"
              value={stopLoss}
              onChange={(e) => setStopLoss(Number(e.target.value))}
              className="input-cyber w-full"
              min={0.1}
              max={50}
              step={0.1}
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Take Profit (%)
            </label>
            <input
              type="number"
              value={takeProfit}
              onChange={(e) => setTakeProfit(Number(e.target.value))}
              className="input-cyber w-full"
              min={0.1}
              max={100}
              step={0.1}
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Slippage (%)
            </label>
            <input
              type="number"
              value={slippage}
              onChange={(e) => setSlippage(Number(e.target.value))}
              className="input-cyber w-full"
              min={0}
              max={2}
              step={0.01}
            />
          </div>

          <div>
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Commission (%)
            </label>
            <input
              type="number"
              value={commission}
              onChange={(e) => setCommission(Number(e.target.value))}
              className="input-cyber w-full"
              min={0}
              max={1}
              step={0.01}
            />
          </div>

          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useTrailingStop}
                onChange={(e) => setUseTrailingStop(e.target.checked)}
                className="w-4 h-4 rounded border-surface-700 bg-surface-900 text-neon-500 focus:ring-neon-500"
              />
              <span className="text-sm text-surface-300">Trailing Stop</span>
            </label>
          </div>
        </div>

        {useTrailingStop && (
          <div className="mt-4">
            <label className="block text-xs font-mono text-surface-400 mb-2 uppercase tracking-wider">
              Trailing Stop (%)
            </label>
            <input
              type="number"
              value={trailingStop}
              onChange={(e) => setTrailingStop(Number(e.target.value))}
              className="input-cyber w-48"
              min={0.1}
              max={10}
              step={0.1}
            />
          </div>
        )}
      </div>

      {/* Indicator Settings (Collapsible) */}
      <div className="card-cyber p-6">
        <button
          type="button"
          onClick={() => setShowIndicators(!showIndicators)}
          className="flex items-center gap-2 w-full text-left"
        >
          <Gauge className="h-5 w-5 text-purple-400" />
          <h3 className="text-lg font-display font-semibold text-white flex-1">
            Indicator Settings
          </h3>
          {showIndicators ? (
            <ChevronDown className="h-5 w-5 text-surface-400" />
          ) : (
            <ChevronRight className="h-5 w-5 text-surface-400" />
          )}
        </button>

        {showIndicators && (
          <div className="mt-6 space-y-6">
            {/* RSI */}
            <div>
              <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                RSI
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Period
                  </label>
                  <input
                    type="number"
                    value={rsiPeriod}
                    onChange={(e) => setRsiPeriod(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={2}
                    max={100}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Overbought
                  </label>
                  <input
                    type="number"
                    value={rsiOverbought}
                    onChange={(e) => setRsiOverbought(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={50}
                    max={100}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Oversold
                  </label>
                  <input
                    type="number"
                    value={rsiOversold}
                    onChange={(e) => setRsiOversold(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={0}
                    max={50}
                  />
                </div>
              </div>
            </div>

            {/* MACD */}
            <div>
              <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                MACD
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Fast Period
                  </label>
                  <input
                    type="number"
                    value={macdFast}
                    onChange={(e) => setMacdFast(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={2}
                    max={50}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Slow Period
                  </label>
                  <input
                    type="number"
                    value={macdSlow}
                    onChange={(e) => setMacdSlow(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={5}
                    max={100}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Signal Period
                  </label>
                  <input
                    type="number"
                    value={macdSignal}
                    onChange={(e) => setMacdSignal(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={2}
                    max={50}
                  />
                </div>
              </div>
            </div>

            {/* EMA */}
            <div>
              <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                EMA
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Short
                  </label>
                  <input
                    type="number"
                    value={emaShort}
                    onChange={(e) => setEmaShort(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={2}
                    max={50}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Medium
                  </label>
                  <input
                    type="number"
                    value={emaMedium}
                    onChange={(e) => setEmaMedium(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={5}
                    max={100}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Long
                  </label>
                  <input
                    type="number"
                    value={emaLong}
                    onChange={(e) => setEmaLong(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={10}
                    max={200}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Trend
                  </label>
                  <input
                    type="number"
                    value={emaTrend}
                    onChange={(e) => setEmaTrend(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={50}
                    max={500}
                  />
                </div>
              </div>
            </div>

            {/* Bollinger Bands */}
            <div>
              <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                Bollinger Bands
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Period
                  </label>
                  <input
                    type="number"
                    value={bbPeriod}
                    onChange={(e) => setBbPeriod(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={5}
                    max={100}
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Std Dev
                  </label>
                  <input
                    type="number"
                    value={bbStdDev}
                    onChange={(e) => setBbStdDev(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={0.5}
                    max={4}
                    step={0.1}
                  />
                </div>
              </div>
            </div>

            {/* ATR & Supertrend */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                  ATR
                </h4>
                <div>
                  <label className="block text-xs font-mono text-surface-400 mb-2">
                    Period
                  </label>
                  <input
                    type="number"
                    value={atrPeriod}
                    onChange={(e) => setAtrPeriod(Number(e.target.value))}
                    className="input-cyber w-full"
                    min={2}
                    max={50}
                  />
                </div>
              </div>

              <div>
                <h4 className="text-sm font-mono text-neon-400 mb-3 uppercase tracking-wider">
                  Supertrend
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-surface-400 mb-2">
                      Period
                    </label>
                    <input
                      type="number"
                      value={stPeriod}
                      onChange={(e) => setStPeriod(Number(e.target.value))}
                      className="input-cyber w-full"
                      min={5}
                      max={50}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-surface-400 mb-2">
                      Multiplier
                    </label>
                    <input
                      type="number"
                      value={stMultiplier}
                      onChange={(e) => setStMultiplier(Number(e.target.value))}
                      className="input-cyber w-full"
                      min={1}
                      max={10}
                      step={0.1}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Submit */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={saveResult}
            onChange={(e) => setSaveResult(e.target.checked)}
            className="w-4 h-4 rounded border-surface-700 bg-surface-900 text-neon-500 focus:ring-neon-500"
          />
          <span className="text-sm text-surface-300">Save result to history</span>
        </label>

        <button
          type="submit"
          disabled={isLoading}
          className={cn(
            "btn-primary px-8 py-3 font-mono uppercase tracking-wider",
            isLoading && "opacity-50 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Clock className="h-4 w-4 animate-spin" />
              Running Backtest...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Run Backtest
            </span>
          )}
        </button>
      </div>
    </form>
  );
}

