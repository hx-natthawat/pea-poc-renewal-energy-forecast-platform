"use client";

import { HelpCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useHelpStore } from "@/stores/helpStore";

interface HelpTriggerProps {
  sectionId: string;
  className?: string;
  size?: "sm" | "md" | "lg";
  variant?: "default" | "subtle";
  label?: string;
}

const sizeClasses = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

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
      onClick={() => toggleHelp(sectionId)}
      className={cn(
        "inline-flex items-center justify-center rounded-full transition-all duration-200",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-pea-purple focus-visible:ring-offset-2",
        buttonSizeClasses[size],
        variant === "default" && [
          "text-gray-400 hover:text-pea-purple hover:bg-pea-purple/10",
          isActive && "text-pea-purple bg-pea-purple/10",
        ],
        variant === "subtle" && [
          "text-gray-300 hover:text-gray-500",
          isActive && "text-pea-purple",
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
