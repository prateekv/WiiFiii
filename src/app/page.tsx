/**
 * web-app/src/app/page.tsx
 * ────────────────────────
 * WiFi CSI Home Sensing — Live Pipeline Verifier
 *
 * Currently: connects to backend WebSocket and logs the combined live 
 * CSI + device scanner data to the browser console.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./page.module.css";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";

export default function Dashboard() {
  const [connected, setConnected] = useState(false);
  const [lastDataTime, setLastDataTime] = useState<string>("Waiting for data...");
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WS] Connected to backend pipeline");
        setConnected(true);
      };

      ws.onmessage = (event) => {
        const frame = JSON.parse(event.data);
        
        // Log the raw live pipeline data to the console so the user can verify
        console.log("[Live Pipeline Data]", frame);
        
        setLastDataTime(new Date().toLocaleTimeString());
      };

      ws.onclose = () => {
        console.log("[WS] Disconnected — retrying in 2s…");
        setConnected(false);
        setTimeout(connect, 2000);
      };

      ws.onerror = (err) => {
        console.error("[WS] Error:", err);
        ws.close();
      };
    };

    connect();

    return () => {
      ws?.close();
    };
  }, []);

  return (
    <main className={styles.main}>
      <header className={styles.header}>
        <h1 className={styles.title}>WiFi CSI Home Sensing</h1>
        <div className={styles.statusBadge} data-connected={connected}>
          <span className={styles.statusDot} />
          {connected ? "Backend Connected" : "Connecting…"}
        </div>
      </header>

      <div className={styles.grid} style={{ display: 'flex', justifyContent: 'center', marginTop: '4rem' }}>
        <section className={styles.panel} style={{ textAlign: 'center', maxWidth: '600px' }}>
          <h2 className={styles.panelTitle}>Live Pipeline Verification</h2>
          <div style={{ margin: '2rem 0', padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px' }}>
            <h3 style={{ marginBottom: '1rem' }}>Open your Browser Console (F12)</h3>
            <p style={{ color: '#888' }}>
              The frontend is currently just logging the raw live data stream.<br/>
              You should see a continuous stream of JSON objects containing both the connected WiFi devices and the ESP32 CSI nodes.
            </p>
          </div>
          <p className={styles.statValue} style={{ fontSize: '1rem' }}>
            Last data received: <span style={{ color: '#fff' }}>{lastDataTime}</span>
          </p>
        </section>
      </div>
    </main>
  );
}
