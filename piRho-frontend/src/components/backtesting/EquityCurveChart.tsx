"use client";

import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  CartesianGrid,
} from "recharts";
import { EquityCurvePoint } from "@/lib/api";

interface EquityCurveChartProps {
  data: EquityCurvePoint[];
  initialCapital: number;
}

export function EquityCurveChart({ data, initialCapital }: EquityCurveChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      date: new Date(point.timestamp).toLocaleDateString(),
      time: new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    }));
  }, [data]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const minEquity = Math.min(...data.map((d) => d.equity)) * 0.98;
  const maxEquity = Math.max(...data.map((d) => d.equity)) * 1.02;

  return (
    <div className="card-cyber p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-display font-semibold text-white">
            Equity Curve
          </h3>
          <p className="text-xs text-surface-400 font-mono mt-1">
            Portfolio value over time
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-neon-500" />
            <span className="text-surface-400">Equity</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-surface-600 border-t border-dashed border-surface-500" />
            <span className="text-surface-400">Initial</span>
          </div>
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00FFFF" stopOpacity={0.3} />
                <stop offset="50%" stopColor="#00FFFF" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#00FFFF" stopOpacity={0} />
              </linearGradient>
            </defs>
            
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(100, 116, 139, 0.1)"
              vertical={false}
            />
            
            <XAxis
              dataKey="date"
              tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
              axisLine={{ stroke: "rgba(0, 255, 255, 0.1)" }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            
            <YAxis
              domain={[minEquity, maxEquity]}
              tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
              tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
              width={60}
            />
            
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(8, 13, 25, 0.95)",
                border: "1px solid rgba(0, 255, 255, 0.3)",
                borderRadius: "8px",
                boxShadow: "0 0 20px rgba(0, 255, 255, 0.1)",
              }}
              labelStyle={{
                color: "#00FFFF",
                fontFamily: "monospace",
                fontSize: 11,
                marginBottom: 8,
              }}
              itemStyle={{ color: "#fff", fontFamily: "monospace" }}
              formatter={(value: number, name: string) => {
                if (name === "equity") {
                  return [formatCurrency(value), "Equity"];
                }
                if (name === "drawdown_percent") {
                  return [`-${value.toFixed(2)}%`, "Drawdown"];
                }
                return [value, name];
              }}
              labelFormatter={(label, payload) => {
                if (payload && payload[0]) {
                  return `${label} ${payload[0].payload.time}`;
                }
                return label;
              }}
            />
            
            <ReferenceLine
              y={initialCapital}
              stroke="#64748b"
              strokeDasharray="5 5"
              strokeWidth={1}
            />
            
            <Area
              type="monotone"
              dataKey="equity"
              stroke="#00FFFF"
              strokeWidth={2}
              fill="url(#equityGradient)"
              dot={false}
              activeDot={{
                fill: "#00FFFF",
                strokeWidth: 2,
                stroke: "#fff",
                r: 5,
                style: { filter: "drop-shadow(0 0 6px #00FFFF)" },
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

interface DrawdownChartProps {
  data: EquityCurvePoint[];
}

export function DrawdownChart({ data }: DrawdownChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      ...point,
      date: new Date(point.timestamp).toLocaleDateString(),
      drawdown_pct: -point.drawdown_percent,
    }));
  }, [data]);

  return (
    <div className="card-cyber p-6">
      <div className="mb-6">
        <h3 className="text-lg font-display font-semibold text-white">
          Drawdown
        </h3>
        <p className="text-xs text-surface-400 font-mono mt-1">
          Peak-to-trough decline
        </p>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
              </linearGradient>
            </defs>
            
            <XAxis
              dataKey="date"
              tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
              axisLine={{ stroke: "rgba(244, 63, 94, 0.1)" }}
              tickLine={false}
              interval="preserveStartEnd"
            />
            
            <YAxis
              tickFormatter={(value) => `${value.toFixed(0)}%`}
              tick={{ fill: "#64748b", fontSize: 10, fontFamily: "monospace" }}
              axisLine={false}
              tickLine={false}
              width={50}
            />
            
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(8, 13, 25, 0.95)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                borderRadius: "8px",
              }}
              labelStyle={{ color: "#f43f5e", fontFamily: "monospace", fontSize: 11 }}
              formatter={(value: number) => [`${value.toFixed(2)}%`, "Drawdown"]}
            />
            
            <ReferenceLine y={0} stroke="#64748b" strokeWidth={1} />
            
            <Area
              type="monotone"
              dataKey="drawdown_pct"
              stroke="#f43f5e"
              strokeWidth={1.5}
              fill="url(#drawdownGradient)"
              dot={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

