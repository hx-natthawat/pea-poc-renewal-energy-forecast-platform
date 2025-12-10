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

  it("returns localhost:8000 for direct access on port 3000", () => {
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

    expect(getApiBaseUrl()).toBe("http://localhost:8000");
  });

  it("returns env var when NEXT_PUBLIC_API_URL is set (non-Kong)", () => {
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

    expect(getApiBaseUrl()).toBe("http://api.example.com");
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

  it("returns Kong WebSocket URL for port 8888", () => {
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

    expect(getWebSocketBaseUrl()).toBe("ws://localhost:8888/backend/api/v1/ws");
  });

  it("returns ws://localhost:8000 for direct access on port 3000", () => {
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
});
