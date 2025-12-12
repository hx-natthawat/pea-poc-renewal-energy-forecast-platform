"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type WebSocketChannel = "all" | "solar" | "voltage" | "alerts";

interface WebSocketMessage {
  type: string;
  channel?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
  message?: string;
}

interface SolarUpdate {
  station_id: string;
  power_kw: number;
  irradiance: number;
  temperature: number;
  prediction?: number;
}

interface VoltageUpdate {
  prosumer_id: string;
  phase: string;
  voltage: number;
  status: string;
  prediction?: number;
}

interface AlertUpdate {
  alert_type: string;
  severity: string;
  message: string;
  target_id?: string;
  value?: number;
}

interface UseWebSocketOptions {
  channels?: WebSocketChannel[];
  onSolarUpdate?: (data: SolarUpdate) => void;
  onVoltageUpdate?: (data: VoltageUpdate) => void;
  onAlert?: (data: AlertUpdate) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectInterval?: number;
}

// Type guards for runtime validation
function isSolarUpdate(data: unknown): data is SolarUpdate {
  return (
    typeof data === "object" &&
    data !== null &&
    "station_id" in data &&
    "power_kw" in data &&
    typeof (data as SolarUpdate).power_kw === "number"
  );
}

function isVoltageUpdate(data: unknown): data is VoltageUpdate {
  return (
    typeof data === "object" &&
    data !== null &&
    "prosumer_id" in data &&
    "voltage" in data &&
    typeof (data as VoltageUpdate).voltage === "number"
  );
}

function isAlertUpdate(data: unknown): data is AlertUpdate {
  return (
    typeof data === "object" &&
    data !== null &&
    "alert_type" in data &&
    "severity" in data &&
    "message" in data
  );
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  connectionError: string | null;
  subscribe: (channel: WebSocketChannel) => void;
  unsubscribe: (channel: WebSocketChannel) => void;
  sendMessage: (message: Record<string, unknown>) => void;
  reconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    channels = ["all"],
    onSolarUpdate,
    onVoltageUpdate,
    onAlert,
    onConnected,
    onDisconnected,
    onError,
    autoReconnect = true,
    reconnectInterval = 5000,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const connectingRef = useRef(false);

  const connect = useCallback(() => {
    // Prevent duplicate connections (handles React Strict Mode double-render)
    if (connectingRef.current || (wsRef.current && wsRef.current.readyState === WebSocket.OPEN)) {
      return;
    }

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close existing connection only if it's not connecting
    if (wsRef.current && wsRef.current.readyState !== WebSocket.CONNECTING) {
      wsRef.current.close();
    }

    // Build URL with channels - detect Kong gateway directly
    const channelParam = channels.join(",");
    const port = window.location.port;
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";

    // Kong gateway detection (port 8888) or /console path
    const isKongGateway = port === "8888" || window.location.pathname.startsWith("/console");
    const wsBaseUrl = isKongGateway
      ? `${wsProtocol}//${window.location.host}/backend/api/v1/ws`
      : `ws://localhost:8000/api/v1/ws`;
    const url = `${wsBaseUrl}?channels=${channelParam}`;

    try {
      connectingRef.current = true;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        connectingRef.current = false;
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        setIsConnected(true);
        setConnectionError(null);
        onConnected?.();
      };

      ws.onclose = () => {
        connectingRef.current = false;
        if (!mountedRef.current) return;
        setIsConnected(false);
        onDisconnected?.();

        // Auto reconnect
        if (autoReconnect && mountedRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, reconnectInterval);
        }
      };

      ws.onerror = () => {
        connectingRef.current = false;
        if (!mountedRef.current) return;
        setConnectionError("WebSocket connection error");
        onError?.(new Event("error"));
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Route message to appropriate handler with runtime type validation
          switch (message.type) {
            case "solar_update":
              if (onSolarUpdate && isSolarUpdate(message.data)) {
                onSolarUpdate(message.data);
              }
              break;

            case "voltage_update":
              if (onVoltageUpdate && isVoltageUpdate(message.data)) {
                onVoltageUpdate(message.data);
              }
              break;

            case "alert":
              if (onAlert && isAlertUpdate(message.data)) {
                onAlert(message.data);
              }
              break;

            case "connected":
            case "subscribed":
            case "unsubscribed":
            case "pong":
              // Connection management messages - no action needed
              break;

            default:
              // Unknown message type
              break;
          }
        } catch {
          console.error("Failed to parse WebSocket message");
        }
      };
    } catch (error) {
      connectingRef.current = false;
      setConnectionError("Failed to create WebSocket connection");
      console.error("WebSocket connection error:", error);
    }
  }, [
    channels,
    onSolarUpdate,
    onVoltageUpdate,
    onAlert,
    onConnected,
    onDisconnected,
    onError,
    autoReconnect,
    reconnectInterval,
  ]);

  const subscribe = useCallback((channel: WebSocketChannel) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "subscribe", channel }));
    }
  }, []);

  const unsubscribe = useCallback((channel: WebSocketChannel) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "unsubscribe", channel }));
    }
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const reconnect = useCallback(() => {
    // Force reconnect by clearing the connecting flag and closing existing connection
    connectingRef.current = false;
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    connect();
  }, [connect]);

  // Connect on mount with small delay to handle React Strict Mode
  useEffect(() => {
    mountedRef.current = true;

    // Small delay to prevent React Strict Mode double-connection issue
    const connectTimeout = setTimeout(() => {
      if (mountedRef.current) {
        connect();
      }
    }, 100);

    return () => {
      mountedRef.current = false;
      clearTimeout(connectTimeout);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      // Don't close WebSocket during Strict Mode unmount - let it connect
      // The onopen handler will close it if component is unmounted
    };
  }, [connect]);

  // Send ping every 30 seconds to keep connection alive
  useEffect(() => {
    if (!isConnected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: "ping" }));
      }
    }, 30000);

    return () => clearInterval(pingInterval);
  }, [isConnected]);

  return {
    isConnected,
    lastMessage,
    connectionError,
    subscribe,
    unsubscribe,
    sendMessage,
    reconnect,
  };
}

// Specialized hook for solar updates only
export function useSolarWebSocket(onUpdate?: (data: SolarUpdate) => void) {
  return useWebSocket({
    channels: ["solar"],
    onSolarUpdate: onUpdate,
  });
}

// Specialized hook for voltage updates only
export function useVoltageWebSocket(onUpdate?: (data: VoltageUpdate) => void) {
  return useWebSocket({
    channels: ["voltage"],
    onVoltageUpdate: onUpdate,
  });
}

// Specialized hook for alerts only
export function useAlertsWebSocket(onAlert?: (data: AlertUpdate) => void) {
  return useWebSocket({
    channels: ["alerts"],
    onAlert,
  });
}
