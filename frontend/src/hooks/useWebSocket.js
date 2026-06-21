"use client";
import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
function useWebSocket({ path, onMessage, enabled = true }) {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const retryRef = useRef(0);
  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer = null;
    const connect = () => {
      if (cancelled) return;
      try {
        const ws = new WebSocket(api.wsUrl(path));
        wsRef.current = ws;
        ws.onopen = () => {
          setConnected(true);
          retryRef.current = 0;
        };
        ws.onmessage = (e) => {
          try {
            const data = JSON.parse(e.data);
            setLastMessage(data);
            onMessage?.(data);
          } catch {
          }
        };
        ws.onclose = () => {
          setConnected(false);
          if (cancelled) return;
          const backoff = Math.min(15e3, 500 * 2 ** retryRef.current++);
          timer = setTimeout(connect, backoff);
        };
        ws.onerror = () => ws.close();
      } catch {
        const backoff = Math.min(15e3, 500 * 2 ** retryRef.current++);
        timer = setTimeout(connect, backoff);
      }
    };
    connect();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
      wsRef.current?.close();
    };
  }, [path, onMessage, enabled]);
  return { connected, lastMessage };
}
export {
  useWebSocket
};
