"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { Logo, HeroLogo } from "@/components/ui/Logo";
import { PageTransition, SlideIn, FadeIn } from "@/components/ui/PageTransition";
import { CyberpunkBackground } from "@/components/ui/CyberpunkBackground";
import { GlitchText, ScrambleText } from "@/components/ui/GlitchText";
import { TiltCard, NeonCard } from "@/components/ui/TiltCard";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { LiveTicker } from "@/components/ui/LiveTicker";
import {
  TrendingUp,
  Shield,
  Zap,
  BarChart3,
  Brain,
  ArrowRight,
  Bot,
  ChevronRight,
  Activity,
  Lock,
  Cpu,
} from "lucide-react";

// Dynamically import 3D component to avoid SSR issues
const CryptoOrb = dynamic(
  () => import("@/components/3d/CryptoOrb").then((mod) => mod.CryptoOrb),
  { 
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-48 h-48 rounded-full bg-neon-500/10 animate-pulse-slow" />
      </div>
    ),
  }
);

export default function HomePage() {
  return (
    <PageTransition>
      <div className="min-h-screen bg-surface-950 overflow-hidden relative">
        {/* Animated Cyberpunk Background */}
        <CyberpunkBackground variant="default" showScanlines />

        {/* Header */}
        <header className="relative border-b border-neon-500/10 backdrop-blur-xl bg-surface-950/60 sticky top-0 z-50">
          <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/50 to-transparent" />
          <div className="mx-auto max-w-7xl px-4 sm:px-6 py-4 flex items-center justify-between">
            <Logo size="md" animated />
            <nav className="hidden md:flex items-center gap-8">
              <Link href="#features" className="text-surface-400 hover:text-neon-400 transition-colors text-sm uppercase tracking-wider font-mono">
                Features
              </Link>
              <Link href="/pricing" className="text-surface-400 hover:text-neon-400 transition-colors text-sm uppercase tracking-wider font-mono">
                Pricing
              </Link>
            </nav>
            <div className="flex items-center gap-2 sm:gap-4">
              <Link href="/login" className="btn-ghost text-sm font-mono uppercase tracking-wider">
                Sign In
              </Link>
              <Link href="/register" className="btn-primary text-sm font-mono uppercase tracking-wider">
                Get Started
              </Link>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="relative py-16 sm:py-20 lg:py-28 min-h-[90vh] flex items-center">
          <div className="relative mx-auto max-w-7xl px-4 sm:px-6 w-full">
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
              {/* Left side - Text content */}
              <div className="text-center lg:text-left z-10">
                <SlideIn delay={100}>
                  <div className="inline-flex items-center gap-2 rounded-full bg-neon-500/10 border border-neon-500/30 px-4 py-1.5 text-sm text-neon-400 mb-6 sm:mb-8 backdrop-blur-sm">
                    <Cpu className="h-4 w-4 animate-pulse" />
                    <span className="font-mono uppercase tracking-wider text-xs">AI-Powered Trading System</span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </SlideIn>
                
                <SlideIn delay={200}>
                  <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-display font-bold tracking-tight leading-[1.1]">
                    Trade Smarter
                    <br />
                    <span className="relative">
                      <span className="text-gradient-cyber">
                        With Institutional AI
                      </span>
                    </span>
                  </h1>
                </SlideIn>
                
                <SlideIn delay={300}>
                  <p className="mx-auto lg:mx-0 mt-6 max-w-xl text-base sm:text-lg text-surface-400 leading-relaxed font-sans">
                    <span className="text-neon-400">LSTM neural networks</span>, 11 battle-tested strategies, and <span className="text-magenta-400">GPT-powered</span> market analysis. Automated 24/7 trading for Bybit perpetual futures.
                  </p>
                </SlideIn>
                
                <SlideIn delay={400}>
                  <div className="mt-8 sm:mt-10 flex flex-col sm:flex-row items-center lg:items-start justify-center lg:justify-start gap-4">
                    <Link 
                      href="/register" 
                      className="btn-primary text-base px-8 py-3.5 w-full sm:w-auto group font-mono uppercase tracking-wider"
                    >
                      Start Free Trial
                      <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                    </Link>
                    <Link 
                      href="/pricing" 
                      className="btn-secondary text-base px-8 py-3.5 w-full sm:w-auto font-mono uppercase tracking-wider"
                    >
                      View Pricing
                    </Link>
                  </div>
                </SlideIn>
                
                <FadeIn delay={600}>
                  <div className="mt-12 flex flex-wrap items-center justify-center lg:justify-start gap-6 sm:gap-8 text-sm text-surface-500">
                    <div className="flex items-center gap-2">
                      <Lock className="h-4 w-4 text-neon-500" />
                      <span className="font-mono">Non-custodial</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4 text-neon-500" />
                      <span className="font-mono">Paper trading</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4 text-neon-500" />
                      <span className="font-mono">24/7 automation</span>
                    </div>
                  </div>
                </FadeIn>
              </div>

              {/* Right side - 3D Orb */}
              <div className="relative h-[400px] lg:h-[500px] hidden lg:block">
                <FadeIn delay={500}>
                  <div className="absolute inset-0">
                    <CryptoOrb className="w-full h-full" />
                  </div>
                </FadeIn>
              </div>
            </div>
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce-subtle">
            <div className="w-6 h-10 rounded-full border-2 border-neon-500/30 flex items-start justify-center p-2">
              <div className="w-1 h-2 bg-neon-500 rounded-full animate-pulse" />
            </div>
          </div>
        </section>

        {/* Live Ticker */}
        <LiveTicker speed="medium" className="border-neon-500/10" />

        {/* Stats Section */}
        <section className="relative py-16 sm:py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
              {[
                { value: 11, label: "Trading Strategies", suffix: "" },
                { value: 24, label: "Hour Automation", suffix: "/7" },
                { value: 100, label: "Non-Custodial", suffix: "%" },
                { value: 50, label: "Execution Speed", prefix: "<", suffix: "ms" },
              ].map((stat, index) => (
                <SlideIn key={stat.label} delay={index * 100}>
                  <NeonCard color="cyan" className="p-6 text-center">
                    <div className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold text-gradient-cyber">
                      {stat.prefix}
                      <AnimatedCounter value={stat.value} delay={index * 200} />
                      {stat.suffix}
                    </div>
                    <div className="mt-2 text-xs sm:text-sm text-surface-400 uppercase tracking-wider font-mono">
                      {stat.label}
                    </div>
                  </NeonCard>
                </SlideIn>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="relative py-16 sm:py-24">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <FadeIn>
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold">
                  <span className="text-gradient-cyber">Advanced Trading</span> Infrastructure
                </h2>
                <p className="mt-4 text-surface-400 max-w-2xl mx-auto text-base sm:text-lg">
                  Combine the power of machine learning with battle-tested trading strategies for consistent performance.
                </p>
              </div>
            </FadeIn>

            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: Brain,
                  title: "LSTM Neural Networks",
                  description: "Per-symbol trained models with attention mechanism for accurate price predictions.",
                  color: "neon",
                  delay: 100,
                },
                {
                  icon: TrendingUp,
                  title: "11 Trading Strategies",
                  description: "From MACD crossovers to funding rate arbitrage, covering all market conditions.",
                  color: "magenta",
                  delay: 150,
                },
                {
                  icon: BarChart3,
                  title: "Sentiment Analysis",
                  description: "Fear & Greed Index, CryptoPanic news, and AI-powered market sentiment.",
                  color: "purple",
                  delay: 200,
                },
                {
                  icon: Bot,
                  title: "GPT Strategy Selection",
                  description: "OpenAI analyzes market conditions and selects the optimal strategy.",
                  color: "neon",
                  delay: 250,
                },
                {
                  icon: Shield,
                  title: "Risk Management",
                  description: "Trailing stops, position sizing, and max drawdown protection built-in.",
                  color: "magenta",
                  delay: 300,
                },
                {
                  icon: Zap,
                  title: "Telegram Alerts",
                  description: "Real-time notifications for trades, signals, and performance updates.",
                  color: "purple",
                  delay: 350,
                },
              ].map((feature) => (
                <SlideIn key={feature.title} delay={feature.delay}>
                  <TiltCard glowColor={feature.color === "neon" ? "rgba(0, 255, 255, 0.2)" : feature.color === "magenta" ? "rgba(255, 0, 255, 0.2)" : "rgba(168, 85, 247, 0.2)"}>
                    <FeatureCard {...feature} />
                  </TiltCard>
                </SlideIn>
              ))}
            </div>
          </div>
        </section>

        {/* How it Works */}
        <section className="relative py-16 sm:py-24 border-t border-neon-500/10">
          <div className="mx-auto max-w-7xl px-4 sm:px-6">
            <FadeIn>
              <div className="text-center mb-16">
                <h2 className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold">
                  How <span className="text-neon-400">piRho</span> Works
                </h2>
              </div>
            </FadeIn>

            <div className="grid md:grid-cols-3 gap-8">
              {[
                {
                  step: "01",
                  title: "Connect Exchange",
                  description: "Link your Bybit account with API keys. We never touch your withdrawal permissions.",
                },
                {
                  step: "02",
                  title: "Configure Bot",
                  description: "Choose strategies, set risk parameters, and deploy your trading bot in minutes.",
                },
                {
                  step: "03",
                  title: "Monitor & Profit",
                  description: "Watch your bot trade 24/7. Get real-time alerts and detailed analytics.",
                },
              ].map((item, index) => (
                <SlideIn key={item.step} delay={index * 150}>
                  <div className="relative">
                    {/* Connector line */}
                    {index < 2 && (
                      <div className="hidden md:block absolute top-12 left-full w-full h-px bg-gradient-to-r from-neon-500/50 to-transparent z-0" />
                    )}
                    
                    <NeonCard color="dual" className="p-6 relative z-10">
                      <div className="text-5xl font-display font-bold text-neon-500/20 mb-4">
                        {item.step}
                      </div>
                      <h3 className="text-xl font-display font-semibold mb-2 text-white">
                        {item.title}
                      </h3>
                      <p className="text-surface-400 text-sm leading-relaxed">
                        {item.description}
                      </p>
                    </NeonCard>
                  </div>
                </SlideIn>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="relative py-20 sm:py-28">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-neon-500/5 to-transparent" />
          <div className="mx-auto max-w-4xl px-4 sm:px-6 text-center relative z-10">
            <SlideIn>
              <h2 className="text-3xl sm:text-4xl lg:text-5xl font-display font-bold">
                Ready to <span className="text-gradient-cyber">automate</span> your trading?
              </h2>
            </SlideIn>
            <SlideIn delay={100}>
              <p className="mt-6 text-lg text-surface-400 font-mono">
                Start with a 7-day free trial. No credit card required.
              </p>
            </SlideIn>
            <SlideIn delay={200}>
              <Link 
                href="/register" 
                className="btn-primary text-lg px-10 py-4 mt-10 inline-flex group font-mono uppercase tracking-wider"
              >
                Get Started Free
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Link>
            </SlideIn>
          </div>
        </section>

        {/* Footer */}
        <footer className="relative border-t border-neon-500/10 py-8 sm:py-12 bg-surface-950/80 backdrop-blur-xl">
          <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/30 to-transparent" />
          <div className="mx-auto max-w-7xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
            <Logo size="sm" />
            <p className="text-xs sm:text-sm text-surface-500 text-center sm:text-right font-mono">
              © 2025 piRho. Trading involves risk. Past performance is not indicative of future results.
            </p>
          </div>
        </footer>
      </div>
    </PageTransition>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  color: string;
}) {
  const colorClasses = {
    neon: "bg-neon-500/10 group-hover:bg-neon-500/20 text-neon-400",
    magenta: "bg-magenta-500/10 group-hover:bg-magenta-500/20 text-magenta-400",
    purple: "bg-purple-500/10 group-hover:bg-purple-500/20 text-purple-400",
  };

  const iconColor = colorClasses[color as keyof typeof colorClasses] || colorClasses.neon;

  return (
    <div className="card-cyber group h-full">
      <div className={`h-12 w-12 rounded-xl ${iconColor} flex items-center justify-center mb-4 transition-colors`}>
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="text-lg font-display font-semibold mb-2 text-white">{title}</h3>
      <p className="text-surface-400 text-sm leading-relaxed">{description}</p>
    </div>
  );
}
