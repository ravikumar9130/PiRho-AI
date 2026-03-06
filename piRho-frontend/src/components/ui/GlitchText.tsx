"use client";

import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

interface GlitchTextProps {
  text: string;
  className?: string;
  as?: "h1" | "h2" | "h3" | "h4" | "span" | "p";
  glitchOnHover?: boolean;
  intensity?: "low" | "medium" | "high";
}

export function GlitchText({
  text,
  className,
  as: Component = "span",
  glitchOnHover = false,
  intensity = "medium",
}: GlitchTextProps) {
  const [isGlitching, setIsGlitching] = useState(!glitchOnHover);

  const intensityStyles = {
    low: "before:animate-[glitch1_4s_infinite_linear] after:animate-[glitch2_4s_infinite_linear]",
    medium: "before:animate-[glitch1_2s_infinite_linear] after:animate-[glitch2_2s_infinite_linear]",
    high: "before:animate-[glitch1_0.5s_infinite_linear] after:animate-[glitch2_0.5s_infinite_linear]",
  };

  return (
    <Component
      className={cn(
        "relative inline-block",
        isGlitching && [
          "before:content-[attr(data-text)] before:absolute before:top-0 before:left-[2px] before:text-[#FF00FF] before:overflow-hidden before:w-full before:h-full",
          "after:content-[attr(data-text)] after:absolute after:top-0 after:left-[-2px] after:text-[#00FFFF] after:overflow-hidden after:w-full after:h-full",
          intensityStyles[intensity],
        ],
        className
      )}
      data-text={text}
      onMouseEnter={glitchOnHover ? () => setIsGlitching(true) : undefined}
      onMouseLeave={glitchOnHover ? () => setIsGlitching(false) : undefined}
    >
      {text}
    </Component>
  );
}

// Animated text that types out
interface TypewriterTextProps {
  text: string;
  className?: string;
  speed?: number;
  delay?: number;
  cursor?: boolean;
}

export function TypewriterText({
  text,
  className,
  speed = 50,
  delay = 0,
  cursor = true,
}: TypewriterTextProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [started, setStarted] = useState(false);

  useEffect(() => {
    const startTimer = setTimeout(() => setStarted(true), delay);
    return () => clearTimeout(startTimer);
  }, [delay]);

  useEffect(() => {
    if (!started) return;

    let index = 0;
    const interval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText(text.slice(0, index + 1));
        index++;
      } else {
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, started]);

  return (
    <span className={cn("font-mono", className)}>
      {displayedText}
      {cursor && (
        <span className="animate-flicker text-neon-500">|</span>
      )}
    </span>
  );
}

// Scramble text effect
interface ScrambleTextProps {
  text: string;
  className?: string;
  scrambleOnHover?: boolean;
}

export function ScrambleText({
  text,
  className,
  scrambleOnHover = true,
}: ScrambleTextProps) {
  const [displayText, setDisplayText] = useState(text);
  const chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`πρΣΔΩαβγ";

  const scramble = () => {
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split("")
          .map((char, index) => {
            if (index < iteration) return text[index];
            if (char === " ") return " ";
            return chars[Math.floor(Math.random() * chars.length)];
          })
          .join("")
      );

      iteration += 1 / 3;
      if (iteration >= text.length) {
        clearInterval(interval);
        setDisplayText(text);
      }
    }, 30);
  };

  return (
    <span
      className={cn("font-mono cursor-pointer", className)}
      onMouseEnter={scrambleOnHover ? scramble : undefined}
    >
      {displayText}
    </span>
  );
}

