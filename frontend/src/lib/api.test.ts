import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getApiBaseUrl, getWebSocketBaseUrl } from "./api";

/**
 * API URL Tests
 *
 * NEW ARCHITECTURE (Unified Approach):
 * - getApiBaseUrl() always returns "/backend" for client-side
 * - Infrastructure handles routing:
 *   - Local dev: Next.js rewrites /backend/* → localhost:8000/*
 *   - Production: Kong routes /backend/* → backend service
 *
 * This eliminates environment detection bugs and ensures consistent behavior.
 */

describe("getApiBaseUrl", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: { ...originalLocation },
      writable: true,
    });
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

  it("always returns /backend for client-side (unified approach)", () => {
    // Any location should return /backend
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
        port: "3000",
        pathname: "/",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("/backend");
  });

  it("returns /backend for Kong gateway on port 8888", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:8888",
        port: "8888",
        pathname: "/console",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("/backend");
  });

  it("returns /backend for /console path (Kong basePath)", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
        port: "3000",
        pathname: "/console/overview",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("/backend");
  });

  it("returns /backend for direct localhost access on port 3000", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
        port: "3000",
        pathname: "/",
      },
      writable: true,
    });

    // Now returns /backend - Next.js rewrites handle proxying
    expect(getApiBaseUrl()).toBe("/backend");
  });

  it("returns /backend even with env var set (client-side uses /backend)", () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.example.com");
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
        port: "3000",
        pathname: "/",
      },
      writable: true,
    });

    // Client-side always uses /backend, env var is for SSR
    expect(getApiBaseUrl()).toBe("/backend");
  });

  it("returns /backend for production (non-localhost)", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "pea-forecast.go.th",
        protocol: "https:",
        host: "pea-forecast.go.th",
        port: "",
        pathname: "/",
      },
      writable: true,
    });

    expect(getApiBaseUrl()).toBe("/backend");
  });
});

describe("getWebSocketBaseUrl", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    Object.defineProperty(window, "location", {
      value: { ...originalLocation },
      writable: true,
    });
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

  it("returns ws://localhost:8000 for local dev on port 3000", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3000",
        port: "3000",
        pathname: "/",
      },
      writable: true,
    });

    // WebSocket can't use rewrites, so direct connection for local dev
    expect(getWebSocketBaseUrl()).toBe("ws://localhost:8000/api/v1/ws");
  });

  it("returns ws://localhost:8000 for local dev on port 3001", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:3001",
        port: "3001",
        pathname: "/",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("ws://localhost:8000/api/v1/ws");
  });

  it("returns wss:// with /backend for https production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "pea-forecast.go.th",
        protocol: "https:",
        host: "pea-forecast.go.th",
        port: "",
        pathname: "/",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("wss://pea-forecast.go.th/backend/api/v1/ws");
  });

  it("returns ws:// with /backend for http production", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "staging.example.com",
        protocol: "http:",
        host: "staging.example.com",
        port: "",
        pathname: "/",
      },
      writable: true,
    });

    expect(getWebSocketBaseUrl()).toBe("ws://staging.example.com/backend/api/v1/ws");
  });

  it("returns /backend WebSocket URL for Kong gateway on port 8888", () => {
    Object.defineProperty(window, "location", {
      value: {
        hostname: "localhost",
        protocol: "http:",
        host: "localhost:8888",
        port: "8888",
        pathname: "/console",
      },
      writable: true,
    });

    // Port 8888 (Kong) uses /backend path
    expect(getWebSocketBaseUrl()).toBe("ws://localhost:8888/backend/api/v1/ws");
  });
});
