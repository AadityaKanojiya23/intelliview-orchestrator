"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

/**
 * Connect to a backend WebSocket endpoint with exponential-backoff reconnect.
 *
 * - Backoff caps at 15 s; resets to 500 ms on successful open.
 * - Cancels cleanly on unmount or when `enabled` flips false.
 * - Never schedules two reconnects in a row for the same onclose.
 */
export function useWebSocket({ path, onMessage, enabled = true }) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const retryRef = useRef(0);

  useEffect(() => {
    if (!enabled) return undefined;

    let cancelled = false;
    let timer = null;
    let reconnectScheduled = false;

    function scheduleReconnect() {
      if (cancelled || reconnectScheduled) return;
      reconnectScheduled = true;
      const delay = Math.min(15_000, 500 * 2 ** retryRef.current);
      timer = setTimeout(() => {
        reconnectScheduled = false;
        retryRef.current = Math.min(retryRef.current + 1, 8);
        connect();
      }, delay);
    }

    function connect() {
      if (cancelled) return;
      try {
        const ws = new WebSocket(api.wsUrl(path));
        wsRef.current = ws;

        ws.onopen = () => {
          if (cancelled) {
            ws.close();
            return;
          }
          setConnected(true);
          retryRef.current = 0;
        };

        ws.onmessage = (event) => {
          if (cancelled) return;
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
            onMessage?.(data);
          } catch {
            // ignore non-JSON frames
          }
        };

        ws.onerror = () => {
          // Browsers fire onerror before onclose; let onclose handle reconnect.
        };

        ws.onclose = () => {
          setConnected(false);
          wsRef.current = null;
          scheduleReconnect();
        };
      } catch {
        scheduleReconnect();
      }
    }

    connect();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      const ws = wsRef.current;
      if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
        ws.close();
      }
      wsRef.current = null;
    };
  }, [path, onMessage, enabled]);

  return { connected, lastMessage };
}

export default useWebSocket;
