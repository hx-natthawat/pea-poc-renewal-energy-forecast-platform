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

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  connectionError: string | null;
  subscribe: (channel: WebSocketChannel) => void;
  unsubscribe: (channel: WebSocketChannel) => void;
  sendMessage: (message: Record<string, unknown>) => void;
  reconnect: () => void;
}

import { getWebSocketBaseUrl } from "@/lib/api";

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

  const connect = useCallback(() => {
    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Build URL with channels - call getWebSocketBaseUrl() here to ensure browser context
    const channelParam = channels.join(",");
    const wsBaseUrl = getWebSocketBaseUrl();
    const url = `${wsBaseUrl}?channels=${channelParam}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        setIsConnected(true);
        setConnectionError(null);
        onConnected?.();
      };

      ws.onclose = () => {
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

      ws.onerror = (event) => {
        if (!mountedRef.current) return;
        setConnectionError("WebSocket connection error");
        onError?.(event);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          // Route message to appropriate handler
          switch (message.type) {
            case "solar_update":
              if (onSolarUpdate && message.data) {
                onSolarUpdate(message.data as unknown as SolarUpdate);
              }
              break;

            case "voltage_update":
              if (onVoltageUpdate && message.data) {
                onVoltageUpdate(message.data as unknown as VoltageUpdate);
              }
              break;

            case "alert":
              if (onAlert && message.data) {
                onAlert(message.data as unknown as AlertUpdate);
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
    connect();
  }, [connect]);

  // Connect on mount
  useEffect(() => {
    mountedRef.current = true;
    connect();

    return () => {
      mountedRef.current = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
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
