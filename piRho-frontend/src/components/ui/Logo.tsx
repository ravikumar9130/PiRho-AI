"use client";

import { cn } from "@/lib/utils";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  showText?: boolean;
  className?: string;
  animated?: boolean;
}

const sizeClasses = {
  sm: { container: "h-8 w-8", text: "text-lg", logoText: "text-sm" },
  md: { container: "h-10 w-10", text: "text-xl", logoText: "text-base" },
  lg: { container: "h-12 w-12", text: "text-2xl", logoText: "text-lg" },
  xl: { container: "h-16 w-16", text: "text-3xl", logoText: "text-xl" },
};

export function Logo({ 
  size = "md", 
  showText = true, 
  className,
  animated = false 
}: LogoProps) {
  const sizes = sizeClasses[size];

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div
        className={cn(
          "rounded-xl relative overflow-hidden",
          "flex items-center justify-center",
          "transition-all duration-300",
          "bg-surface-900 border border-neon-500/50",
          animated && "hover:shadow-neon-cyan hover:scale-105 hover:border-neon-400",
          sizes.container
        )}
        style={{
          boxShadow: "0 0 15px rgba(0, 255, 255, 0.2), inset 0 0 15px rgba(0, 255, 255, 0.1)",
        }}
      >
        {/* Animated gradient background */}
        <div 
          className="absolute inset-0 opacity-50"
          style={{
            background: "linear-gradient(135deg, rgba(0, 255, 255, 0.2) 0%, transparent 50%, rgba(255, 0, 255, 0.2) 100%)",
          }}
        />
        {/* Top glow line */}
        <div 
          className="absolute top-0 left-0 right-0 h-px"
          style={{
            background: "linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.8), transparent)",
          }}
        />
        <LogoMark className={cn("text-neon-400 font-bold font-mono relative z-10", sizes.logoText)} />
      </div>
      {showText && (
        <span className={cn(
          "font-display font-bold tracking-wider",
          "bg-gradient-to-r from-neon-400 via-neon-300 to-magenta-400 bg-clip-text text-transparent",
          sizes.text
        )}>
          piRho
        </span>
      )}
    </div>
  );
}

// Just the πρ mark for favicons and minimal contexts
export function LogoMark({ className }: { className?: string }) {
  return (
    <span className={cn("select-none", className)}>
      πρ
    </span>
  );
}

// Large animated logo for hero sections
export function HeroLogo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-4", className)}>
      <div className="relative">
        <div
          className={cn(
            "h-16 w-16 rounded-2xl relative overflow-hidden",
            "flex items-center justify-center",
            "bg-surface-900 border border-neon-500/50",
            "animate-pulse-neon"
          )}
        >
          {/* Animated gradient */}
          <div 
            className="absolute inset-0"
            style={{
              background: "linear-gradient(135deg, rgba(0, 255, 255, 0.3) 0%, transparent 50%, rgba(255, 0, 255, 0.3) 100%)",
            }}
          />
          {/* Top glow line */}
          <div 
            className="absolute top-0 left-0 right-0 h-px"
            style={{
              background: "linear-gradient(90deg, transparent, rgba(0, 255, 255, 1), transparent)",
            }}
          />
          <LogoMark className="text-neon-400 font-bold font-mono text-2xl relative z-10" />
        </div>
        {/* Glow effect behind */}
        <div 
          className="absolute -inset-2 rounded-2xl opacity-50 blur-xl -z-10 animate-pulse-slow"
          style={{
            background: "linear-gradient(135deg, #00FFFF 0%, #FF00FF 100%)",
          }}
        />
        {/* Outer glow ring */}
        <div 
          className="absolute -inset-1 rounded-2xl opacity-30 blur-lg -z-10"
          style={{
            background: "linear-gradient(135deg, #00FFFF 0%, #FF00FF 100%)",
          }}
        />
      </div>
      <span 
        className="text-4xl font-display font-bold tracking-wider bg-gradient-to-r from-neon-400 via-neon-300 to-magenta-400 bg-clip-text text-transparent"
        style={{
          textShadow: "0 0 30px rgba(0, 255, 255, 0.3)",
        }}
      >
        piRho
      </span>
    </div>
  );
}

// SVG version for favicon generation
export function LogoSVG({ 
  size = 32, 
  className 
}: { 
  size?: number; 
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00FFFF" />
          <stop offset="100%" stopColor="#FF00FF" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="1" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <rect width="32" height="32" rx="8" fill="#0f172a" stroke="url(#logoGradient)" strokeWidth="1"/>
      <text
        x="16"
        y="22"
        textAnchor="middle"
        fill="#00FFFF"
        fontSize="14"
        fontWeight="bold"
        fontFamily="monospace"
        filter="url(#glow)"
      >
        πρ
      </text>
    </svg>
  );
}

// Favicon component (for dynamic favicon)
export function FaviconSVG() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="faviconGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#00FFFF" />
          <stop offset="100%" stopColor="#FF00FF" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="6" fill="#030712" stroke="url(#faviconGradient)" strokeWidth="1"/>
      <text
        x="16"
        y="21"
        textAnchor="middle"
        fill="#00FFFF"
        fontSize="12"
        fontWeight="bold"
        fontFamily="ui-monospace, monospace"
      >
        πρ
      </text>
    </svg>
  );
}
