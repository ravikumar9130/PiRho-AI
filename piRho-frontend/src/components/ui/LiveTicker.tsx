"use client";

import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface TickerItem {
  symbol: string;
  price: string;
  change: number;
}

interface LiveTickerProps {
  items?: TickerItem[];
  speed?: "slow" | "medium" | "fast";
  className?: string;
}

const defaultItems: TickerItem[] = [
  { symbol: "BTC", price: "$43,521.00", change: 2.34 },
  { symbol: "ETH", price: "$2,285.50", change: -1.23 },
  { symbol: "SOL", price: "$98.45", change: 5.67 },
  { symbol: "AVAX", price: "$35.12", change: 3.45 },
  { symbol: "DOT", price: "$7.89", change: -0.87 },
  { symbol: "LINK", price: "$14.56", change: 4.21 },
  { symbol: "MATIC", price: "$0.89", change: 1.98 },
  { symbol: "ARB", price: "$1.23", change: -2.34 },
];

export function LiveTicker({
  items = defaultItems,
  speed = "medium",
  className,
}: LiveTickerProps) {
  const speedDuration = {
    slow: "60s",
    medium: "40s",
    fast: "25s",
  };

  // Double the items for seamless loop
  const doubledItems = [...items, ...items];

  return (
    <div className={cn(
      "w-full overflow-hidden bg-surface-900/50 border-y border-surface-800/50 backdrop-blur-sm",
      className
    )}>
      <div 
        className="flex items-center gap-8 py-3 whitespace-nowrap"
        style={{
          animation: `ticker ${speedDuration[speed]} linear infinite`,
        }}
      >
        {doubledItems.map((item, index) => (
          <TickerItemComponent key={`${item.symbol}-${index}`} item={item} />
        ))}
      </div>
    </div>
  );
}

function TickerItemComponent({ item }: { item: TickerItem }) {
  const isPositive = item.change >= 0;

  return (
    <div className="flex items-center gap-3 px-4">
      {/* Symbol */}
      <span className="font-mono font-semibold text-white">
        {item.symbol}
      </span>

      {/* Price */}
      <span className="font-mono text-surface-300">
        {item.price}
      </span>

      {/* Change */}
      <span
        className={cn(
          "flex items-center gap-1 font-mono text-sm",
          isPositive ? "text-neon-400" : "text-hotpink-400"
        )}
      >
        {isPositive ? (
          <TrendingUp className="h-3 w-3" />
        ) : (
          <TrendingDown className="h-3 w-3" />
        )}
        {isPositive ? "+" : ""}
        {item.change.toFixed(2)}%
      </span>

      {/* Separator dot */}
      <span className="text-surface-600">•</span>
    </div>
  );
}

// Vertical scrolling ticker for sidebar/widgets
interface VerticalTickerProps {
  items?: TickerItem[];
  className?: string;
}

export function VerticalTicker({
  items = defaultItems,
  className,
}: VerticalTickerProps) {
  return (
    <div className={cn(
      "h-32 overflow-hidden relative",
      className
    )}>
      {/* Fade gradient top */}
      <div className="absolute top-0 left-0 right-0 h-8 bg-gradient-to-b from-surface-900 to-transparent z-10" />
      
      {/* Fade gradient bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-surface-900 to-transparent z-10" />

      <div 
        className="flex flex-col gap-2"
        style={{
          animation: "scrollUp 20s linear infinite",
        }}
      >
        {[...items, ...items].map((item, index) => (
          <VerticalTickerItem key={`${item.symbol}-${index}`} item={item} />
        ))}
      </div>

      <style jsx>{`
        @keyframes scrollUp {
          0% {
            transform: translateY(0);
          }
          100% {
            transform: translateY(-50%);
          }
        }
      `}</style>
    </div>
  );
}

function VerticalTickerItem({ item }: { item: TickerItem }) {
  const isPositive = item.change >= 0;

  return (
    <div className="flex items-center justify-between px-3 py-1.5 rounded-lg bg-surface-800/30">
      <div className="flex items-center gap-2">
        <span className="font-mono font-semibold text-sm">{item.symbol}</span>
        <span className="font-mono text-xs text-surface-400">{item.price}</span>
      </div>
      <span
        className={cn(
          "font-mono text-xs",
          isPositive ? "text-neon-400" : "text-hotpink-400"
        )}
      >
        {isPositive ? "+" : ""}{item.change.toFixed(2)}%
      </span>
    </div>
  );
}

// Mini sparkline chart for ticker items
interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function Sparkline({
  data,
  width = 60,
  height = 20,
  color = "#00FFFF",
  className,
}: SparklineProps) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg 
      width={width} 
      height={height} 
      className={className}
      style={{ overflow: "visible" }}
    >
      <defs>
        <linearGradient id={`sparkline-gradient-${color.replace("#", "")}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      
      {/* Fill */}
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#sparkline-gradient-${color.replace("#", "")})`}
      />
      
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        style={{
          filter: `drop-shadow(0 0 2px ${color})`,
        }}
      />
      
      {/* End dot */}
      <circle
        cx={width}
        cy={height - ((data[data.length - 1] - min) / range) * height}
        r="2"
        fill={color}
        style={{
          filter: `drop-shadow(0 0 4px ${color})`,
        }}
      />
    </svg>
  );
}

