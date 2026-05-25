import { useEffect, useState } from "react";

export function useWebSocket() {
  const [message, setMessage] = useState<Record<string, unknown> | null>(null);
  useEffect(() => {
    const url = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/live";
    const socket = new WebSocket(url);
    socket.onmessage = (event) => setMessage(JSON.parse(event.data));
    return () => socket.close();
  }, []);
  return message;
}
