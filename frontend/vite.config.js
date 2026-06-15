import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const hmrHost = process.env.VITE_HMR_HOST;
const hmrProtocol = process.env.VITE_HMR_PROTOCOL ?? "wss";
const hmrClientPort = process.env.VITE_HMR_CLIENT_PORT
  ? Number(process.env.VITE_HMR_CLIENT_PORT)
  : 443;

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    hmr: hmrHost
      ? {
          host: hmrHost,
          protocol: hmrProtocol,
          clientPort: hmrClientPort,
        }
      : undefined,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
      "/health": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
