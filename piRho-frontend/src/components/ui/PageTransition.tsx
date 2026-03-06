"use client";

import { useEffect, useState, Children, cloneElement, isValidElement } from "react";
import { cn } from "@/lib/utils";

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export function PageTransition({ children, className }: PageTransitionProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div
      className={cn(
        "transition-all duration-500 ease-out",
        mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4",
        className
      )}
    >
      {children}
    </div>
  );
}

interface StaggeredListProps {
  children: React.ReactNode;
  className?: string;
  staggerDelay?: number; // in ms
}

export function StaggeredList({ 
  children, 
  className,
  staggerDelay = 100 
}: StaggeredListProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const childrenArray = Children.toArray(children);

  return (
    <div className={className}>
      {childrenArray.map((child, index) => {
        if (!isValidElement(child)) return child;

        return cloneElement(child as React.ReactElement<{ style?: React.CSSProperties; className?: string }>, {
          style: {
            ...((child as React.ReactElement<{ style?: React.CSSProperties }>).props.style || {}),
            transitionDelay: `${index * staggerDelay}ms`,
          },
          className: cn(
            (child as React.ReactElement<{ className?: string }>).props.className,
            "transition-all duration-500 ease-out",
            mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"
          ),
        });
      })}
    </div>
  );
}

interface FadeInProps {
  children: React.ReactNode;
  className?: string;
  delay?: number; // in ms
  duration?: number; // in ms
}

export function FadeIn({ 
  children, 
  className,
  delay = 0,
  duration = 500 
}: FadeInProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={cn(
        "transition-opacity ease-out",
        mounted ? "opacity-100" : "opacity-0",
        className
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

interface SlideInProps {
  children: React.ReactNode;
  className?: string;
  direction?: "up" | "down" | "left" | "right";
  delay?: number;
  duration?: number;
}

export function SlideIn({ 
  children, 
  className,
  direction = "up",
  delay = 0,
  duration = 500 
}: SlideInProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const directionClasses = {
    up: mounted ? "translate-y-0" : "translate-y-8",
    down: mounted ? "translate-y-0" : "-translate-y-8",
    left: mounted ? "translate-x-0" : "translate-x-8",
    right: mounted ? "translate-x-0" : "-translate-x-8",
  };

  return (
    <div
      className={cn(
        "transition-all ease-out",
        mounted ? "opacity-100" : "opacity-0",
        directionClasses[direction],
        className
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

interface ScaleInProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
}

export function ScaleIn({ 
  children, 
  className,
  delay = 0,
  duration = 300 
}: ScaleInProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={cn(
        "transition-all absolute top-1/3 ease-out",
        mounted ? "opacity-100 scale-100" : "opacity-0 scale-95",
        className
      )}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
}

