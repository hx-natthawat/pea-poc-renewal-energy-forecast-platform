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

// Icon sizes - responsive for mobile
const sizeClasses = {
  sm: "h-3.5 w-3.5 sm:h-4 sm:w-4",
  md: "h-4 w-4 sm:h-5 sm:w-5",
  lg: "h-5 w-5 sm:h-6 sm:w-6",
};

// Button padding - larger touch targets on mobile
const buttonSizeClasses = {
  sm: "p-1.5 sm:p-1",
  md: "p-2 sm:p-1.5",
  lg: "p-2.5 sm:p-2",
};

// Minimum touch target size for accessibility (44x44px on mobile)
const touchTargetClasses = "min-h-[44px] min-w-[44px] sm:min-h-0 sm:min-w-0";

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
        touchTargetClasses,
        buttonSizeClasses[size],
        // Default variant - visible on all devices
        variant === "default" && [
          "text-gray-400 hover:text-pea-purple hover:bg-pea-purple/10",
          "active:bg-pea-purple/20", // Touch feedback
          isActive && "text-pea-purple bg-pea-purple/10",
        ],
        // Subtle variant - less prominent
        variant === "subtle" && [
          "text-gray-300 hover:text-gray-500",
          "active:text-pea-purple",
          isActive && "text-pea-purple",
        ],
        // Card variant - always visible with subtle background, good for cards
        variant === "card" && [
          "text-gray-400/70 hover:text-pea-purple",
          "bg-gray-100/50 hover:bg-pea-purple/10",
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
