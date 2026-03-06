"use client";

import { cn } from "@/lib/utils";

interface SpinnerProps {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4 border-2",
  md: "h-6 w-6 border-2",
  lg: "h-8 w-8 border-3",
  xl: "h-12 w-12 border-4",
};

export function Spinner({ size = "md", className, label }: SpinnerProps) {
  return (
    <div className={cn("inline-flex flex-col items-center gap-2", className)}>
      <div
        className={cn(
          "animate-spin rounded-full border-brand-500 border-t-transparent",
          sizeClasses[size]
        )}
        role="status"
        aria-label={label || "Loading"}
      />
      {label && (
        <span className="text-sm text-surface-400">{label}</span>
      )}
    </div>
  );
}

// Full page loading spinner
export function PageSpinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <Spinner size="lg" label={label} />
    </div>
  );
}

// Branded loading with logo animation
export function BrandedSpinner({ className }: { className?: string }) {
  return (
    <div className={cn("flex flex-col items-center gap-4", className)}>
      <div className="relative">
        <div className="h-16 w-16 rounded-xl bg-gradient-to-br from-brand-500 to-teal-500 flex items-center justify-center animate-pulse-glow">
          <span className="text-2xl font-bold text-white font-mono">πρ</span>
        </div>
        <div className="absolute inset-0 rounded-xl border-2 border-brand-400/50 animate-ping" />
      </div>
      <div className="flex items-center gap-1">
        <span className="text-surface-400">Loading</span>
        <span className="loading-dots text-surface-400" />
      </div>
    </div>
  );
}

// Inline button spinner
export function ButtonSpinner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent",
        className
      )}
      role="status"
      aria-hidden="true"
    />
  );
}

