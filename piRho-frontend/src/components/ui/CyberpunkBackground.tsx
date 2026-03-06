"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface CyberpunkBackgroundProps {
  className?: string;
  variant?: "default" | "minimal" | "intense";
  showGrid?: boolean;
  showOrbs?: boolean;
  showParticles?: boolean;
  showScanlines?: boolean;
}

export function CyberpunkBackground({
  className,
  variant = "default",
  showGrid = true,
  showOrbs = true,
  showParticles = true,
  showScanlines = false,
}: CyberpunkBackgroundProps) {
  return (
    <div className={cn("fixed inset-0 pointer-events-none overflow-hidden", className)}>
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-surface-950 via-surface-900 to-surface-black" />

      {/* Animated grid */}
      {showGrid && <AnimatedGrid variant={variant} />}

      {/* Floating neon orbs */}
      {showOrbs && <FloatingOrbs variant={variant} />}

      {/* Particle field */}
      {showParticles && <ParticleField variant={variant} />}

      {/* Scanlines overlay */}
      {showScanlines && <Scanlines />}

      {/* Noise texture */}
      <div className="absolute inset-0 opacity-[0.015]">
        <div className="w-full h-full bg-noise" />
      </div>

      {/* Vignette effect */}
      <div 
        className="absolute inset-0"
        style={{
          background: "radial-gradient(ellipse at center, transparent 0%, rgba(0, 0, 0, 0.4) 100%)",
        }}
      />
    </div>
  );
}

function AnimatedGrid({ variant }: { variant: string }) {
  const intensity = variant === "intense" ? 0.08 : variant === "minimal" ? 0.02 : 0.04;
  
  return (
    <>
      {/* Primary grid */}
      <div 
        className="absolute inset-0 animate-grid-flow"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 255, 255, ${intensity}) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 255, ${intensity}) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
        }}
      />
      
      {/* Secondary magenta grid (offset) */}
      <div 
        className="absolute inset-0"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255, 0, 255, ${intensity * 0.5}) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 0, 255, ${intensity * 0.5}) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          backgroundPosition: "30px 30px",
          opacity: 0.5,
        }}
      />

      {/* Perspective floor grid */}
      <div 
        className="absolute bottom-0 left-0 right-0 h-[40vh] overflow-hidden"
        style={{
          perspective: "500px",
        }}
      >
        <div 
          className="absolute inset-0"
          style={{
            backgroundImage: `
              linear-gradient(rgba(0, 255, 255, 0.15) 1px, transparent 1px),
              linear-gradient(90deg, rgba(0, 255, 255, 0.08) 1px, transparent 1px)
            `,
            backgroundSize: "40px 40px",
            transform: "rotateX(60deg)",
            transformOrigin: "center bottom",
            animation: "gridFlow 20s linear infinite",
          }}
        />
        {/* Gradient fade */}
        <div 
          className="absolute inset-0"
          style={{
            background: "linear-gradient(180deg, rgba(3, 7, 18, 1) 0%, transparent 30%, transparent 70%, rgba(3, 7, 18, 0.8) 100%)",
          }}
        />
      </div>
    </>
  );
}

function FloatingOrbs({ variant }: { variant: string }) {
  const orbCount = variant === "intense" ? 4 : variant === "minimal" ? 2 : 3;
  
  const orbs = [
    { color: "rgba(0, 255, 255, 0.15)", size: "40%", top: "10%", left: "20%", delay: "0s" },
    { color: "rgba(255, 0, 255, 0.12)", size: "35%", top: "60%", left: "70%", delay: "2s" },
    { color: "rgba(168, 85, 247, 0.10)", size: "30%", top: "40%", left: "10%", delay: "4s" },
    { color: "rgba(0, 212, 255, 0.08)", size: "45%", top: "70%", left: "40%", delay: "6s" },
  ].slice(0, orbCount);

  return (
    <>
      {orbs.map((orb, i) => (
        <div
          key={i}
          className="absolute rounded-full blur-3xl animate-float-slow"
          style={{
            background: `radial-gradient(circle, ${orb.color} 0%, transparent 70%)`,
            width: orb.size,
            height: orb.size,
            top: orb.top,
            left: orb.left,
            animationDelay: orb.delay,
            animationDuration: `${8 + i * 2}s`,
          }}
        />
      ))}
      
      {/* Central glow */}
      <div 
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[60%] rounded-full blur-3xl"
        style={{
          background: "radial-gradient(ellipse at center, rgba(0, 255, 255, 0.03) 0%, transparent 50%)",
        }}
      />
    </>
  );
}

function ParticleField({ variant }: { variant: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isReducedMotion, setIsReducedMotion] = useState(false);

  useEffect(() => {
    // Check for reduced motion preference
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setIsReducedMotion(mediaQuery.matches);
    
    const handleChange = (e: MediaQueryListEvent) => setIsReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handleChange);
    
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || isReducedMotion) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    const particleCount = variant === "intense" ? 80 : variant === "minimal" ? 30 : 50;
    
    interface Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      opacity: number;
      color: string;
    }

    const particles: Particle[] = [];
    const colors = ["#00FFFF", "#FF00FF", "#a855f7", "#3b82f6"];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 0.5,
        speedX: (Math.random() - 0.5) * 0.3,
        speedY: (Math.random() - 0.5) * 0.3,
        opacity: Math.random() * 0.5 + 0.2,
        color: colors[Math.floor(Math.random() * colors.length)],
      });
    }

    let animationId: number;

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((particle, i) => {
        particle.x += particle.speedX;
        particle.y += particle.speedY;

        // Wrap around screen
        if (particle.x < 0) particle.x = canvas.width;
        if (particle.x > canvas.width) particle.x = 0;
        if (particle.y < 0) particle.y = canvas.height;
        if (particle.y > canvas.height) particle.y = 0;

        // Draw particle with glow
        ctx.save();
        ctx.globalAlpha = particle.opacity;
        ctx.shadowBlur = 10;
        ctx.shadowColor = particle.color;
        ctx.fillStyle = particle.color;
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Draw connections to nearby particles
        particles.slice(i + 1).forEach((other) => {
          const dx = particle.x - other.x;
          const dy = particle.y - other.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance < 120) {
            ctx.save();
            ctx.globalAlpha = (1 - distance / 120) * 0.15;
            ctx.strokeStyle = particle.color;
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(particle.x, particle.y);
            ctx.lineTo(other.x, other.y);
            ctx.stroke();
            ctx.restore();
          }
        });
      });

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", resize);
      cancelAnimationFrame(animationId);
    };
  }, [variant, isReducedMotion]);

  if (isReducedMotion) return null;

  return (
    <canvas 
      ref={canvasRef} 
      className="absolute inset-0 opacity-60"
      style={{ mixBlendMode: "screen" }}
    />
  );
}

function Scanlines() {
  return (
    <>
      {/* Static scanlines */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, transparent, transparent 1px, rgba(0, 0, 0, 0.3) 1px, rgba(0, 0, 0, 0.3) 2px)",
        }}
      />
      {/* Animated scan line */}
      <div 
        className="absolute left-0 right-0 h-px bg-gradient-to-r from-transparent via-neon-500/30 to-transparent animate-scanline"
        style={{
          boxShadow: "0 0 20px 5px rgba(0, 255, 255, 0.3)",
        }}
      />
    </>
  );
}

// Simpler version for dashboard/internal pages
export function DashboardBackground({ className }: { className?: string }) {
  return (
    <div className={cn("fixed inset-0 pointer-events-none overflow-hidden -z-10", className)}>
      {/* Base gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-surface-950 via-surface-900 to-surface-950" />
      
      {/* Subtle grid */}
      <div 
        className="absolute inset-0 opacity-30"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0, 255, 255, 0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 255, 255, 0.02) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />
      
      {/* Corner glows */}
      <div 
        className="absolute -top-1/4 -left-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
        style={{
          background: "radial-gradient(circle, rgba(0, 255, 255, 0.05) 0%, transparent 70%)",
        }}
      />
      <div 
        className="absolute -bottom-1/4 -right-1/4 w-1/2 h-1/2 rounded-full blur-3xl"
        style={{
          background: "radial-gradient(circle, rgba(255, 0, 255, 0.03) 0%, transparent 70%)",
        }}
      />
    </div>
  );
}

// Matrix-style falling code (optional, for accent areas)
export function MatrixRain({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    const chars = "πρΣΔΩ01αβγδ∞∑∏√∫≈≠≤≥".split("");
    const fontSize = 14;
    const columns = canvas.width / fontSize;
    const drops: number[] = [];

    for (let i = 0; i < columns; i++) {
      drops[i] = Math.random() * -100;
    }

    const draw = () => {
      ctx.fillStyle = "rgba(3, 7, 18, 0.05)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = "#00FFFF";
      ctx.font = `${fontSize}px monospace`;

      for (let i = 0; i < drops.length; i++) {
        const char = chars[Math.floor(Math.random() * chars.length)];
        ctx.globalAlpha = Math.random() * 0.5 + 0.1;
        ctx.fillText(char, i * fontSize, drops[i] * fontSize);

        if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i] += 0.5;
      }
    };

    const interval = setInterval(draw, 50);

    return () => clearInterval(interval);
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className={cn("absolute inset-0 opacity-20", className)}
    />
  );
}

