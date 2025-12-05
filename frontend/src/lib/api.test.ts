import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getApiBaseUrl, getWebSocketBaseUrl } from "./api";

describe("getApiBaseUrl", () => {
  const originalLocation = window.location;

  beforeEach(() => {
    // Reset window.location for each test
    Object.defineProperty(window, "location", {
      value: { ...originalLocation },
      writable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
    vi.unstubAllEnvs();
  });

  it("returns localhost:8000 for localhost hostname", () => {
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
  });

  afterEach(() => {
    Object.defineProperty(window, "location", {
      value: originalLocation,
      writable: true,
    });
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
