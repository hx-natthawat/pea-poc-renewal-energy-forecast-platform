"use client";

import type { ComponentPropsWithoutRef, ElementType, ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Responsive Container Component
 * Provides consistent padding and max-width across different screen sizes.
 * Part of v1.1.0 Mobile-Responsive Dashboard (PWA) feature.
 */

type ResponsiveContainerProps<T extends ElementType = "div"> = {
  children: ReactNode;
  className?: string;
  as?: T;
  noPadding?: boolean;
  fullWidth?: boolean;
} & Omit<ComponentPropsWithoutRef<T>, "as" | "className" | "children">;

export function ResponsiveContainer<T extends ElementType = "div">({
  children,
  className,
  as,
  noPadding = false,
  fullWidth = false,
  ...props
}: ResponsiveContainerProps<T>) {
  const Component = as || "div";
  return (
    <Component
      className={cn(
        "w-full mx-auto",
        !noPadding && "px-4 sm:px-6 lg:px-8",
        !fullWidth && "max-w-7xl",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  );
}

/**
 * Responsive Grid Component
 * Auto-adjusting grid that works well on mobile and desktop.
 */
interface ResponsiveGridProps {
  children: ReactNode;
  className?: string;
  cols?: {
    default?: number;
    sm?: number;
    md?: number;
    lg?: number;
    xl?: number;
  };
  gap?: "none" | "sm" | "md" | "lg";
}

export function ResponsiveGrid({
  children,
  className,
  cols = { default: 1, sm: 2, lg: 3 },
  gap = "md",
}: ResponsiveGridProps) {
  const gapClasses = {
    none: "gap-0",
    sm: "gap-2 sm:gap-3",
    md: "gap-4 sm:gap-6",
    lg: "gap-6 sm:gap-8",
  };

  const colClasses = [
    cols.default && `grid-cols-${cols.default}`,
    cols.sm && `sm:grid-cols-${cols.sm}`,
    cols.md && `md:grid-cols-${cols.md}`,
    cols.lg && `lg:grid-cols-${cols.lg}`,
    cols.xl && `xl:grid-cols-${cols.xl}`,
  ]
    .filter(Boolean)
    .join(" ");

  return <div className={cn("grid", colClasses, gapClasses[gap], className)}>{children}</div>;
}

/**
 * Responsive Card Component
 * Card with touch-friendly padding and interactions.
 */
interface ResponsiveCardProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
  hoverable?: boolean;
  padding?: "none" | "sm" | "md" | "lg";
}

export function ResponsiveCard({
  children,
  className,
  onClick,
  hoverable = false,
  padding = "md",
}: ResponsiveCardProps) {
  const paddingClasses = {
    none: "",
    sm: "p-3 sm:p-4",
    md: "p-4 sm:p-6",
    lg: "p-6 sm:p-8",
  };

  const baseClasses = cn(
    "bg-white rounded-xl border border-gray-200 shadow-sm",
    paddingClasses[padding],
    hoverable && "transition-shadow hover:shadow-md",
    onClick && "cursor-pointer active:scale-[0.99] transition-transform",
    onClick && "w-full text-left",
    className
  );

  if (onClick) {
    return (
      <button type="button" className={baseClasses} onClick={onClick}>
        {children}
      </button>
    );
  }

  return <div className={baseClasses}>{children}</div>;
}

/**
 * Responsive Stack Component
 * Vertical or horizontal stack with responsive spacing.
 */
interface ResponsiveStackProps {
  children: ReactNode;
  className?: string;
  direction?: "row" | "column" | "responsive";
  gap?: "none" | "sm" | "md" | "lg";
  align?: "start" | "center" | "end" | "stretch";
  justify?: "start" | "center" | "end" | "between" | "around";
}

export function ResponsiveStack({
  children,
  className,
  direction = "column",
  gap = "md",
  align = "stretch",
  justify = "start",
}: ResponsiveStackProps) {
  const gapClasses = {
    none: "gap-0",
    sm: "gap-2",
    md: "gap-4",
    lg: "gap-6",
  };

  const directionClasses = {
    row: "flex-row",
    column: "flex-col",
    responsive: "flex-col sm:flex-row",
  };

  const alignClasses = {
    start: "items-start",
    center: "items-center",
    end: "items-end",
    stretch: "items-stretch",
  };

  const justifyClasses = {
    start: "justify-start",
    center: "justify-center",
    end: "justify-end",
    between: "justify-between",
    around: "justify-around",
  };

  return (
    <div
      className={cn(
        "flex",
        directionClasses[direction],
        gapClasses[gap],
        alignClasses[align],
        justifyClasses[justify],
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * Mobile-only visibility wrapper
 */
export function MobileOnly({ children }: { children: ReactNode }) {
  return <div className="block lg:hidden">{children}</div>;
}

/**
 * Desktop-only visibility wrapper
 */
export function DesktopOnly({ children }: { children: ReactNode }) {
  return <div className="hidden lg:block">{children}</div>;
}

/**
 * Safe area padding for notched devices (iPhone X+)
 */
export function SafeAreaPadding({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={cn("pb-safe-area-inset-bottom", className)}>{children}</div>;
}
