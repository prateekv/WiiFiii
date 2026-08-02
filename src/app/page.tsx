/**
 * web-app/src/app/page.tsx
 * ────────────────────────
 * WiFi CSI Home Sensing — Dashboard Skeleton
 *
 * Currently: connects to backend WebSocket and shows live connection status.
 * TODO: replace placeholder panels with Three.js heatmap + device list.
 */
"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./page.module.css";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";

interface CsiFrame {
  type: string;
  tick: number;
  heatmap: number[][];
  devices: number;
}

export default function Dashboard() {
  const [connected, setConnected] = useState(false);
  const [lastFrame, setLastFrame] = useState<CsiFrame | null>(null);
  const [fps, setFps] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const frameCount = useRef(0);

  useEffect(() => {
    let ws: WebSocket;

    const connect = () => {
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[WS] Connected to backend");
        setConnected(true);
      };

      ws.onmessage = (event) => {
        const frame: CsiFrame = JSON.parse(event.data);
        setLastFrame(frame);
        frameCount.current += 1;
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

    // FPS counter
    const fpsInterval = setInterval(() => {
      setFps(frameCount.current);
      frameCount.current = 0;
    }, 1000);

    return () => {
      ws?.close();
      clearInterval(fpsInterval);
    };
  }, []);

  return (
    <main className={styles.main}>
      {/* ── Header ────────────────────────────────────────────── */}
      <header className={styles.header}>
        <h1 className={styles.title}>WiFi CSI Home Sensing</h1>
        <div className={styles.statusBadge} data-connected={connected}>
          <span className={styles.statusDot} />
          {connected ? "Backend Connected" : "Connecting…"}
        </div>
      </header>

      {/* ── Stats bar ─────────────────────────────────────────── */}
      <div className={styles.statsBar}>
        <Stat label="Frames/sec" value={fps} />
        <Stat label="Devices" value={lastFrame?.devices ?? "—"} />
        <Stat label="Tick" value={lastFrame?.tick ?? "—"} />
      </div>

      {/* ── Main panels ───────────────────────────────────────── */}
      <div className={styles.grid}>
        {/* Heatmap placeholder */}
        <section className={styles.panel} id="panel-heatmap">
          <h2 className={styles.panelTitle}>Live Presence Heatmap</h2>
          <div className={styles.placeholderCanvas}>
            {lastFrame ? (
              <MiniHeatmap data={lastFrame.heatmap} />
            ) : (
              <p className={styles.waiting}>Waiting for CSI data…</p>
            )}
          </div>
          <p className={styles.panelNote}>
            Three.js 3D overlay will replace this grid in the next phase.
          </p>
        </section>

        {/* Device list placeholder */}
        <section className={styles.panel} id="panel-devices">
          <h2 className={styles.panelTitle}>Connected Devices</h2>
          <div className={styles.placeholderList}>
            <p className={styles.waiting}>ARP scanner not yet wired up.</p>
            <p className={styles.waiting}>Will show IP / MAC / hostname here.</p>
          </div>
        </section>

        {/* Signal chart placeholder */}
        <section className={styles.panel} id="panel-signal">
          <h2 className={styles.panelTitle}>CSI Signal (raw amplitude)</h2>
          <div className={styles.placeholderCanvas}>
            <p className={styles.waiting}>Chart.js time-series goes here.</p>
          </div>
        </section>
      </div>
    </main>
  );
}

/* ── Tiny heatmap component (CSS grid) ───────────────────────────────────── */
function MiniHeatmap({ data }: { data: number[][] }) {
  return (
    <div className={styles.heatmapGrid}>
      {data.flat().map((val, i) => (
        <div
          key={i}
          className={styles.heatmapCell}
          style={{ opacity: val }}
          title={val.toFixed(2)}
        />
      ))}
    </div>
  );
}

/* ── Stat card ────────────────────────────────────────────────────────────── */
function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className={styles.stat}>
      <span className={styles.statValue}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}
