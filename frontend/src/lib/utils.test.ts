import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cn,
  debounce,
  formatDate,
  formatNumber,
  isClient,
  isMobileDevice,
  isTouchDevice,
} from "./utils";

describe("cn (className merger)", () => {
  it("merges multiple class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    expect(cn("foo", false && "bar", "baz")).toBe("foo baz");
  });

  it("deduplicates tailwind classes", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });

  it("handles arrays", () => {
    expect(cn(["foo", "bar"])).toBe("foo bar");
  });

  it("handles undefined and null", () => {
    expect(cn("foo", undefined, null, "bar")).toBe("foo bar");
  });
});

describe("formatNumber", () => {
  it("formats numbers with Thai locale", () => {
    const result = formatNumber(1234.567);
    expect(result).toContain("1");
    expect(result).toContain("234");
  });

  it("respects maximumFractionDigits default of 2", () => {
    const result = formatNumber(1.23456);
    // Should have at most 2 decimal places
    const parts = result.split(/[.,]/);
    if (parts.length > 1) {
      expect(parts[parts.length - 1].length).toBeLessThanOrEqual(2);
    }
  });

  it("accepts custom options", () => {
    const result = formatNumber(1234, { style: "currency", currency: "THB" });
    expect(result).toContain("1");
  });

  it("handles zero", () => {
    const result = formatNumber(0);
    expect(result).toBe("0");
  });

  it("handles negative numbers", () => {
    const result = formatNumber(-1234);
    expect(result).toContain("1");
    expect(result).toContain("234");
  });
});

describe("formatDate", () => {
  it("formats Date objects", () => {
    const date = new Date("2024-01-15T10:30:00");
    const result = formatDate(date);
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
  });

  it("formats date strings", () => {
    const result = formatDate("2024-01-15T10:30:00");
    expect(result).toBeTruthy();
    expect(typeof result).toBe("string");
  });

  it("accepts custom options", () => {
    const date = new Date("2024-01-15");
    const result = formatDate(date, { dateStyle: "full" });
    expect(result).toBeTruthy();
  });
});

describe("debounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("delays function execution", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 100);

    debouncedFn();
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("resets timer on subsequent calls", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 100);

    debouncedFn();
    vi.advanceTimersByTime(50);
    debouncedFn();
    vi.advanceTimersByTime(50);
    expect(fn).not.toHaveBeenCalled();

    vi.advanceTimersByTime(50);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("passes arguments to the function", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 100);

    debouncedFn("arg1", "arg2");
    vi.advanceTimersByTime(100);

    expect(fn).toHaveBeenCalledWith("arg1", "arg2");
  });

  it("only executes once for multiple rapid calls", () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 100);

    debouncedFn();
    debouncedFn();
    debouncedFn();
    debouncedFn();

    vi.advanceTimersByTime(100);
    expect(fn).toHaveBeenCalledTimes(1);
  });
});

describe("isClient", () => {
  it("returns true in browser environment (jsdom)", () => {
    expect(isClient()).toBe(true);
  });
});

describe("isMobileDevice", () => {
  const originalInnerWidth = window.innerWidth;

  afterEach(() => {
    Object.defineProperty(window, "innerWidth", {
      value: originalInnerWidth,
      writable: true,
    });
  });

  it("returns true for narrow screens", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 375,
      writable: true,
    });
    expect(isMobileDevice()).toBe(true);
  });

  it("returns false for wide screens", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 1024,
      writable: true,
    });
    expect(isMobileDevice()).toBe(false);
  });

  it("returns false at exactly 768px", () => {
    Object.defineProperty(window, "innerWidth", {
      value: 768,
      writable: true,
    });
    expect(isMobileDevice()).toBe(false);
  });
});

describe("isTouchDevice", () => {
  it("detects touch capability", () => {
    // jsdom doesn't have touch support by default
    const result = isTouchDevice();
    expect(typeof result).toBe("boolean");
  });
});
