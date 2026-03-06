"use client";

import { useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
  tiltAmount?: number;
  glowOnHover?: boolean;
}

export function TiltCard({
  children,
  className,
  glowColor = "rgba(0, 255, 255, 0.3)",
  tiltAmount = 10,
  glowOnHover = true,
}: TiltCardProps) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [transform, setTransform] = useState("");
  const [glowPosition, setGlowPosition] = useState({ x: 50, y: 50 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;

    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    const rotateX = ((y - centerY) / centerY) * -tiltAmount;
    const rotateY = ((x - centerX) / centerX) * tiltAmount;

    setTransform(`perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`);
    setGlowPosition({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
    });
  };

  const handleMouseLeave = () => {
    setTransform("");
    setGlowPosition({ x: 50, y: 50 });
    setIsHovered(false);
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  return (
    <div
      ref={cardRef}
      className={cn(
        "relative transition-transform duration-200 ease-out",
        className
      )}
      style={{ transform }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      onMouseEnter={handleMouseEnter}
    >
      {/* Glow effect that follows cursor */}
      {glowOnHover && isHovered && (
        <div
          className="absolute inset-0 pointer-events-none rounded-xl opacity-0 transition-opacity duration-300"
          style={{
            opacity: isHovered ? 1 : 0,
            background: `radial-gradient(circle at ${glowPosition.x}% ${glowPosition.y}%, ${glowColor} 0%, transparent 50%)`,
          }}
        />
      )}

      {/* Shine effect */}
      {isHovered && (
        <div
          className="absolute inset-0 pointer-events-none rounded-xl overflow-hidden"
          style={{
            background: `linear-gradient(
              ${105 + (glowPosition.x - 50) * 0.5}deg,
              transparent 40%,
              rgba(255, 255, 255, 0.05) 50%,
              transparent 60%
            )`,
          }}
        />
      )}

      {children}
    </div>
  );
}

// Holographic card with rainbow shine effect
interface HolographicCardProps {
  children: React.ReactNode;
  className?: string;
}

export function HolographicCard({ children, className }: HolographicCardProps) {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const cardRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    setPosition({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100,
    });
  };

  return (
    <div
      ref={cardRef}
      className={cn(
        "relative overflow-hidden rounded-xl",
        className
      )}
      onMouseMove={handleMouseMove}
    >
      {/* Holographic overlay */}
      <div
        className="absolute inset-0 pointer-events-none opacity-50 mix-blend-overlay"
        style={{
          background: `
            linear-gradient(
              ${position.x * 3.6}deg,
              rgba(0, 255, 255, 0.3) 0%,
              rgba(255, 0, 255, 0.3) 25%,
              rgba(168, 85, 247, 0.3) 50%,
              rgba(0, 255, 255, 0.3) 75%,
              rgba(255, 0, 255, 0.3) 100%
            )
          `,
        }}
      />

      {/* Prismatic shine */}
      <div
        className="absolute inset-0 pointer-events-none opacity-20"
        style={{
          background: `radial-gradient(
            circle at ${position.x}% ${position.y}%,
            rgba(255, 255, 255, 0.8) 0%,
            transparent 50%
          )`,
        }}
      />

      {children}
    </div>
  );
}

// Neon border card
interface NeonCardProps {
  children: React.ReactNode;
  className?: string;
  color?: "cyan" | "magenta" | "purple" | "dual";
  animated?: boolean;
}

export function NeonCard({
  children,
  className,
  color = "cyan",
  animated = true,
}: NeonCardProps) {
  const colorStyles = {
    cyan: {
      border: "border-neon-500/50",
      shadow: "shadow-neon-cyan",
      gradient: "from-neon-500 to-neon-400",
    },
    magenta: {
      border: "border-magenta-500/50",
      shadow: "shadow-neon-magenta",
      gradient: "from-magenta-500 to-magenta-400",
    },
    purple: {
      border: "border-purple-500/50",
      shadow: "0 0 20px rgba(168, 85, 247, 0.3)",
      gradient: "from-purple-500 to-purple-400",
    },
    dual: {
      border: "border-neon-500/30",
      shadow: "shadow-neon-dual",
      gradient: "from-neon-500 via-purple-500 to-magenta-500",
    },
  };

  const styles = colorStyles[color];

  return (
    <div
      className={cn(
        "relative rounded-xl border bg-surface-900/50 backdrop-blur-md overflow-hidden",
        styles.border,
        animated && "hover:shadow-glow-lg transition-all duration-300",
        className
      )}
    >
      {/* Top accent line */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-px bg-gradient-to-r",
          styles.gradient,
          animated && "animate-pulse-slow"
        )}
      />

      {children}
    </div>
  );
}

