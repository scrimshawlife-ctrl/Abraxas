// WebSocket realtime communication for Abraxas
import { WebSocketServer } from "ws";

export function installRealtime(server) {
  const wss = new WebSocketServer({ server });
  const clients = new Set();

  wss.on("connection", (ws) => {
    clients.add(ws);
    console.log("Abraxas client connected");

    ws.on("close", () => {
      clients.delete(ws);
      console.log("Abraxas client disconnected");
    });

    ws.on("error", (error) => {
      console.error("WebSocket error:", error);
      clients.delete(ws);
    });
  });

  return {
    broadcast: (type, data) => {
      const message = JSON.stringify({ type, data, timestamp: Date.now() });
      clients.forEach((client) => {
        if (client.readyState === client.OPEN) {
          try {
            client.send(message);
          } catch (error) {
            console.error("Failed to send message:", error);
            clients.delete(client);
          }
        }
      });
    },
    getClientCount: () => clients.size
  };
}