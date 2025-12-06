import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getApiBaseUrl, getWebSocketBaseUrl } from "./api";

describe("getApiBaseUrl", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    // Reset window.location and env vars for each test
    Object.defineProperty(window, "location", {
      value: { ...originalLocation },
      writable: true,
    });
    // Clear env vars by default
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    vi.stubEnv("NEXT_PUBLIC_WS_URL", "");
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
    vi.unstubAllEnvs();
  });

  it("returns env var when NEXT_PUBLIC_API_URL is set", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.example.com");

    expect(getApiBaseUrl()).toBe("http://api.example.com");
  });

  it("returns localhost:8000 for localhost hostname when no env var", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("returns same host for production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "pea-forecast.go.th",
        protocol: "https:",
        host: "pea-forecast.go.th",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("https://pea-forecast.go.th");
  });

  it("preserves protocol in production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "example.com",
        protocol: "http:",
        host: "example.com",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("http://example.com");
  });
});

describe("getWebSocketBaseUrl", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: { ...originalLocation },
      writable: true,
    });
    // Clear env vars by default
    vi.stubEnv("NEXT_PUBLIC_API_URL", "");
    vi.stubEnv("NEXT_PUBLIC_WS_URL", "");
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
    vi.unstubAllEnvs();
  });

  it("returns env var when NEXT_PUBLIC_WS_URL is set", () => {
    vi.stubEnv("NEXT_PUBLIC_WS_URL", "wss://ws.example.com/ws");

    expect(getWebSocketBaseUrl()).toBe("wss://ws.example.com/ws");
  });

  it("returns ws://localhost:8000 for localhost", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("ws://localhost:8000/api/v1/ws");
  });

  it("returns wss:// for https production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "pea-forecast.go.th",
        protocol: "https:",
        host: "pea-forecast.go.th",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("wss://pea-forecast.go.th/api/v1/ws");
  });

  it("returns ws:// for http production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "staging.example.com",
        protocol: "http:",
        host: "staging.example.com",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("ws://staging.example.com/api/v1/ws");
  });
});
