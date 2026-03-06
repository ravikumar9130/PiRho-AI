"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import { Header } from "@/components/dashboard/Header";
import { api, DashboardStats, DailySummary, SignalLog } from "@/lib/api";
import { SignalLogList } from "@/components/dashboard/SignalLog";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { PageTransition, SlideIn } from "@/components/ui/PageTransition";
import { SkeletonStatCard, SkeletonChart } from "@/components/ui/Skeleton";
import { AnimatedCounter, AnimatedStat } from "@/components/ui/AnimatedCounter";
import { NeonCard, TiltCard } from "@/components/ui/TiltCard";
import { Sparkline } from "@/components/ui/LiveTicker";
import {
  TrendingUp,
  TrendingDown,
  Bot,
  Activity,
  Target,
  BarChart3,
  ArrowRight,
  Zap,
  ChevronRight,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import Link from "next/link";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const { data: session } = useSession();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [dailyData, setDailyData] = useState<DailySummary[]>([]);
  const [signalLogs, setSignalLogs] = useState<SignalLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSignals, setLoadingSignals] = useState(true);

  useEffect(() => {
    async function fetchData() {
      if (!session?.accessToken) return;
      
      try {
        const [statsData, dailyRes, signals] = await Promise.all([
          api.getDashboard(session.accessToken),
          api.getDailySummary(session.accessToken, 7),
          api.getSignalLogs(session.accessToken, 20).catch(() => []),
        ]);
        setStats(statsData);
        setDailyData(dailyRes.summary);
        setSignalLogs(signals);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
        setLoadingSignals(false);
      }
    }
    
    fetchData();
  }, [session]);

  if (loading) {
    return (
      <>
        <Header title="Dashboard" />
        <div className="p-4 lg:p-6">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <SkeletonStatCard key={i} />
            ))}
          </div>
          <div className="grid gap-4 lg:gap-6 lg:grid-cols-2 mt-6">
            <SkeletonChart />
            <SkeletonChart />
          </div>
        </div>
      </>
    );
  }

  return (
    <PageTransition>
      <Header title="Dashboard" />
      <div className="p-4 lg:p-6 space-y-6">
        {/* Welcome Banner */}
        <SlideIn delay={0}>
          <NeonCard color="dual" className="p-6">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h2 className="text-xl md:text-2xl font-display font-bold text-white">
                  Welcome back, <span className="text-neon-400">{session?.user?.name || "Trader"}</span>
                </h2>
                <p className="text-surface-400 mt-1 text-sm font-mono">
                  Your trading bots are actively monitoring the markets
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link href="/dashboard/bots" className="btn-primary font-mono uppercase tracking-wider text-xs">
                  <Bot className="h-4 w-4 mr-2" />
                  Manage Bots
                </Link>
              </div>
            </div>
          </NeonCard>
        </SlideIn>

        {/* Stats Grid */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 items-stretch">
          <SlideIn delay={50}>
            <TiltCard glowColor="rgba(0, 255, 255, 0.2)" tiltAmount={5}>
              <CyberStatCard
                label="Today's P&L"
                value={stats?.today_pnl || 0}
                icon={stats?.today_pnl && stats.today_pnl >= 0 ? TrendingUp : TrendingDown}
                trend={stats?.today_pnl && stats.today_pnl >= 0 ? "up" : "down"}
                format="currency"
                // sparklineData={dailyData.map(d => d.pnl)}
              />
            </TiltCard>
          </SlideIn>
          <SlideIn delay={100}>
            <TiltCard glowColor="rgba(0, 255, 255, 0.2)" tiltAmount={5}>
              <CyberStatCard
                label="Active Positions"
                value={stats?.active_positions || 0}
                icon={Activity}
                format="number"
              />
            </TiltCard>
          </SlideIn>
          <SlideIn delay={150}>
            <TiltCard glowColor="rgba(0, 255, 255, 0.2)" tiltAmount={5}>
              <CyberStatCard
                label="Running Bots"
                value={stats?.running_bots || 0}
                icon={Bot}
                format="number"
              />
            </TiltCard>
          </SlideIn>
          <SlideIn delay={200}>
            <TiltCard glowColor="rgba(0, 255, 255, 0.2)" tiltAmount={5}>
              <CyberStatCard
                label="7-Day Win Rate"
                value={(stats?.win_rate_7d || 0) * 100}
                icon={Target}
                format="percent"
              />
            </TiltCard>
          </SlideIn>
        </div>

        {/* Charts Row */}
        <div className="grid gap-4 lg:gap-6 lg:grid-cols-2">
          {/* P&L Chart */}
          <SlideIn delay={250}>
            <div className="card-cyber">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-display font-semibold text-white">7-Day Performance</h2>
                  <p className="text-xs text-surface-400 font-mono mt-1">Profit & Loss Overview</p>
                </div>
                <div className="p-2 rounded-lg bg-neon-500/10 border border-neon-500/20">
                  <BarChart3 className="h-5 w-5 text-neon-400" />
                </div>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={dailyData}>
                    <defs>
                      <linearGradient id="pnlGradientCyber" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00FFFF" stopOpacity={0.3} />
                        <stop offset="50%" stopColor="#00FFFF" stopOpacity={0.1} />
                        <stop offset="95%" stopColor="#00FFFF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="date"
                      tickFormatter={(date) => new Date(date).toLocaleDateString("en-US", { weekday: "short" })}
                      tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                      axisLine={{ stroke: "rgba(0, 255, 255, 0.1)" }}
                      tickLine={false}
                    />
                    <YAxis
                      tickFormatter={(value) => `$${value}`}
                      tick={{ fill: "#64748b", fontSize: 11, fontFamily: "monospace" }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "rgba(8, 13, 25, 0.95)",
                        border: "1px solid rgba(0, 255, 255, 0.3)",
                        borderRadius: "8px",
                        boxShadow: "0 0 20px rgba(0, 255, 255, 0.1)",
                      }}
                      labelStyle={{ color: "#00FFFF", fontFamily: "monospace", fontSize: 11 }}
                      itemStyle={{ color: "#fff", fontFamily: "monospace" }}
                      formatter={(value) => [formatCurrency(Number(value) || 0), "P&L"]}
                      labelFormatter={(date) => new Date(date).toLocaleDateString()}
                    />
                    <Area
                      type="monotone"
                      dataKey="pnl"
                      stroke="#00FFFF"
                      strokeWidth={2}
                      fill="url(#pnlGradientCyber)"
                      dot={{
                        fill: "#00FFFF",
                        strokeWidth: 0,
                        r: 3,
                      }}
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
          </SlideIn>

          {/* Quick Actions */}
          <SlideIn delay={300}>
            <div className="card-cyber h-full">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-display font-semibold text-white">Quick Actions</h2>
                  <p className="text-xs text-surface-400 font-mono mt-1">Get started with common tasks</p>
                </div>
                <Zap className="h-5 w-5 text-magenta-400" />
              </div>
              <div className="space-y-3">
                <QuickActionCard
                  href="/dashboard/bots"
                  icon={Bot}
                  title="Create Trading Bot"
                  description="Configure a new automated strategy"
                  color="neon"
                />
                <QuickActionCard
                  href="/dashboard/positions"
                  icon={Activity}
                  title="View Positions"
                  description="Monitor your open trades"
                  color="magenta"
                />
                <QuickActionCard
                  href="/dashboard/settings"
                  icon={Target}
                  title="Connect Exchange"
                  description="Add your Bybit API keys"
                  color="purple"
                />
              </div>
            </div>
          </SlideIn>
        </div>

        {/* Signal Log */}
        <SlideIn delay={350}>
          <div className="card-cyber">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-display font-semibold text-white">Signal Log</h2>
                <p className="text-xs text-surface-400 font-mono mt-1">
                  Complete transparency on why trades triggered
                </p>
              </div>
            </div>
            <SignalLogList logs={signalLogs} loading={loadingSignals} />
          </div>
        </SlideIn>

        {/* Recent Activity */}
        <SlideIn delay={400}>
          <div className="card-cyber">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-display font-semibold text-white">Recent Trades</h2>
                <p className="text-xs text-surface-400 font-mono mt-1">Last 24 hours activity</p>
              </div>
              <Link 
                href="/dashboard/history" 
                className="text-xs text-neon-400 hover:text-neon-300 font-mono uppercase tracking-wider flex items-center gap-1 transition-colors"
              >
                View All
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
            <div className="text-center py-8 text-surface-500">
              <Activity className="h-12 w-12 mx-auto mb-3 text-surface-600" />
              <p className="font-mono text-sm">No recent trades</p>
              <p className="text-xs text-surface-600 mt-1">Trades will appear here once your bots start executing</p>
            </div>
          </div>
        </SlideIn>
      </div>
    </PageTransition>
  );
}

function CyberStatCard({
  label,
  value,
  icon: Icon,
  trend,
  format,
  sparklineData,
}: {
  label: string;
  value: number;
  icon: React.ComponentType<{ className?: string }>;
  trend?: "up" | "down";
  format: "currency" | "percent" | "number";
  sparklineData?: number[];
}) {
  const formatValue = () => {
    switch (format) {
      case "currency":
        return formatCurrency(value);
      case "percent":
        return `${value.toFixed(1)}%`;
      default:
        return value.toString();
    }
  };

  const trendConfig = {
    up: {
      color: "text-neon-400",
      bgColor: "bg-neon-500/10 border-neon-500/30",
      glowColor: "#00FFFF",
    },
    down: {
      color: "text-hotpink-400",
      bgColor: "bg-hotpink-500/10 border-hotpink-500/30",
      glowColor: "#f43f5e",
    },
    neutral: {
      color: "text-surface-300",
      bgColor: "bg-surface-800 border-surface-700",
      glowColor: "transparent",
    },
  };

  const config = trendConfig[trend || "neutral"];

  return (
    <div className="card-cyber p-5 h-full flex flex-col">
      <div className="flex items-start justify-between flex-shrink-0">
        <div className="flex-1">
          <span className="text-xs text-surface-400 uppercase tracking-wider font-mono block mb-2">
            {label}
          </span>
          <span className={cn(
            "text-2xl font-display font-bold block",
            config.color
          )}>
            {format === "currency" && value !== 0 ? (
              <AnimatedCounter 
                value={Math.abs(value)} 
                prefix={value >= 0 ? "$" : "-$"}
                duration={1500}
              />
            ) : format === "percent" ? (
              <AnimatedCounter 
                value={value} 
                suffix="%"
                decimals={1}
                duration={1500}
              />
            ) : (
              <AnimatedCounter value={value} duration={1500} />
            )}
          </span>
        </div>
        <div className={cn(
          "p-2.5 rounded-xl border transition-colors flex-shrink-0",
          config.bgColor
        )}>
          <Icon className={cn("h-5 w-5", config.color)} />
        </div>
      </div>
      
      {/* Mini sparkline - only show if data exists and keep it compact */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-3 pt-3 border-t border-surface-800/50 flex-shrink-0">
          <Sparkline 
            data={sparklineData} 
            width={120} 
            height={20} 
            color={config.glowColor}
          />
        </div>
      )}
    </div>
  );
}

function QuickActionCard({
  href,
  icon: Icon,
  title,
  description,
  color,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  color: "neon" | "magenta" | "purple";
}) {
  const colorClasses = {
    neon: {
      bg: "bg-neon-500/10 group-hover:bg-neon-500/20 border-neon-500/20",
      text: "text-neon-400",
    },
    magenta: {
      bg: "bg-magenta-500/10 group-hover:bg-magenta-500/20 border-magenta-500/20",
      text: "text-magenta-400",
    },
    purple: {
      bg: "bg-purple-500/10 group-hover:bg-purple-500/20 border-purple-500/20",
      text: "text-purple-400",
    },
  };

  const classes = colorClasses[color];

  return (
    <Link
      href={href}
      className="flex items-center justify-between p-4 rounded-xl bg-surface-900/50 border border-surface-800/50 hover:border-neon-500/20 transition-all duration-300 group hover:bg-surface-900/80"
    >
      <div className="flex items-center gap-4">
        <div className={cn(
          "h-11 w-11 rounded-xl flex items-center justify-center transition-colors border",
          classes.bg
        )}>
          <Icon className={cn("h-5 w-5", classes.text)} />
        </div>
        <div>
          <p className="font-display font-medium text-white">{title}</p>
          <p className="text-xs text-surface-400 font-mono mt-0.5">{description}</p>
        </div>
      </div>
      <ArrowRight className="h-5 w-5 text-surface-500 group-hover:text-neon-400 group-hover:translate-x-1 transition-all" />
    </Link>
  );
}
