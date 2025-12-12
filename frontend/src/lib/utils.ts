import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to merge Tailwind CSS classes.
 * Combines clsx for conditional classes with tailwind-merge for deduplication.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a number with locale-specific formatting.
 */
export function formatNumber(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat("th-TH", {
    maximumFractionDigits: 2,
    ...options,
  }).format(value);
}

/**
 * Format a date with locale-specific formatting.
 */
export function formatDate(date: Date | string, options?: Intl.DateTimeFormatOptions): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return new Intl.DateTimeFormat("th-TH", {
    dateStyle: "medium",
    timeStyle: "short",
    ...options,
  }).format(d);
}

/**
 * Debounce function for search inputs, resize handlers, etc.
 */
export function debounce<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Check if code is running on the client side.
 */
export function isClient(): boolean {
  return typeof window !== "undefined";
}

/**
 * Check if device is mobile based on screen width.
 */
export function isMobileDevice(): boolean {
  if (!isClient()) return false;
  return window.innerWidth < 768;
}

/**
 * Check if device supports touch.
 */
export function isTouchDevice(): boolean {
  if (!isClient()) return false;
  return "ontouchstart" in window || navigator.maxTouchPoints > 0;
}
