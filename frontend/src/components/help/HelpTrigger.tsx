"use client";

import { HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useHelpStore } from "@/stores/helpStore";

interface HelpTriggerProps {
  sectionId: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "subtle" | "card";
  label?: string;
}

// Icon sizes - fixed sizes (no responsive to avoid hydration issues)
const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

// Button padding - fixed sizes
const buttonSizeClasses = {
  sm: "p-1",
  md: "p-1.5",
  lg: "p-2",
};

export function HelpTrigger({
  sectionId,
  className,
  size = "md",
  variant = "default",
  label,
}: HelpTriggerProps) {
  const { isOpen, activeSection, toggleHelp } = useHelpStore();
  const isActive = isOpen && activeSection === sectionId;

  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation();
        toggleHelp(sectionId);
      }}
      className={cn(
        "inline-flex items-center justify-center rounded-full transition-all duration-200",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-pea-purple focus-visible:ring-offset-2",
        buttonSizeClasses[size],
        // Default variant - visible, with touch target for standalone use
        variant === "default" && [
          "min-w-[44px] min-h-[44px]",
          "text-pea-purple/60 hover:text-pea-purple hover:bg-pea-purple/10",
          "active:bg-pea-purple/20",
          isActive && "text-pea-purple bg-pea-purple/10",
        ],
        // Subtle variant - compact for inline use with text (no large touch target)
        variant === "subtle" && [
          "text-pea-purple/60 hover:text-pea-purple",
          "active:text-pea-purple",
          isActive && "text-pea-purple",
        ],
        // Card variant - for absolute positioning on cards, with touch target
        variant === "card" && [
          "min-w-[44px] min-h-[44px]",
          "text-pea-purple/50 hover:text-pea-purple",
          "bg-pea-purple/5 hover:bg-pea-purple/10",
          "active:bg-pea-purple/20",
          isActive && "text-pea-purple bg-pea-purple/10",
        ],
        className
      )}
      aria-label={label || `Show help for ${sectionId}`}
      aria-expanded={isActive}
      aria-haspopup="dialog"
    >
      <HelpCircle className={cn(sizeClasses[size], isActive && "fill-current")} />
    </button>
  );
}
