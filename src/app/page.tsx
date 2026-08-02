/**
 * web-app/src/app/page.tsx
 * ────────────────────────
 * WiFi CSI Home Sensing — Live Dashboard (Step 7)
 */
"use client";

import { useEffect, useRef, useState } from "react";
import styles from "./page.module.css";
import LiveMap from "../components/LiveMap";

// Match the standalone ws_server.py port (8765)
const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8765";

interface Device {
  ip: string;
  mac: string;
  name: string;
}

interface Analytics {
  movement_detected: boolean;
  active_zone: string;
  highest_variance_score: number;
  node_variances: Record<string, number>;
  tracked_zones: string[];
}

export interface PipelineFrame {
  type: string;
  timestamp: string;
  devices: Device[];
  analytics: Analytics;
}

export default function Dashboard() {
  const [connected, setConnected] = useState(false);
  const [lastFrame, setLastFrame] = useState<PipelineFrame | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;

    const connect = () => {
      console.log(`Connecting to ${WS_URL}...`);
      ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data);
          if (frame.type === "live_pipeline_frame") {
            setLastFrame(frame);
          }
        } catch (e) {
          console.error("Failed to parse frame", e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000); // Auto-reconnect
      };

      ws.onerror = () => {
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
        <h1 className={styles.title}>Home Sensing Dashboard</h1>
        <div className={styles.statusBadge} data-connected={connected}>
          <span className={styles.statusDot} />
          {connected ? "LIVE" : "DISCONNECTED"}
        </div>
      </header>

      {/* Analytics Banner */}
      <div className={styles.statsBar}>
        <Stat 
          label="Status" 
          value={lastFrame?.analytics.movement_detected ? "MOVEMENT DETECTED" : "CLEAR"} 
          alert={lastFrame?.analytics.movement_detected}
        />
        <Stat 
          label="Active Zone" 
          value={lastFrame?.analytics.active_zone ?? "Unknown"} 
        />
        <Stat 
          label="Connected Devices" 
          value={lastFrame?.devices.length ?? 0} 
        />
      </div>

      <div className={styles.grid}>
        {/* 3D Map Section */}
        <section className={styles.panel} style={{ gridColumn: "span 2" }}>
          <h2 className={styles.panelTitle}>Live 3D Presence Map</h2>
          <div className={styles.placeholderCanvas} style={{ padding: 0, overflow: 'hidden', height: '400px', background: '#111' }}>
             <LiveMap analytics={lastFrame?.analytics} />
          </div>
          <p className={styles.panelNote}>
            Zones are mapped dynamically based on active ESP32 nodes. The glowing orb indicates the current disturbance zone.
          </p>
        </section>

        {/* Device List Section */}
        <section className={styles.panel}>
          <h2 className={styles.panelTitle}>Network Devices</h2>
          <div className={styles.deviceList} style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {!lastFrame?.devices || lastFrame.devices.length === 0 ? (
              <p className={styles.waiting}>Scanning network...</p>
            ) : (
              lastFrame.devices.map((d, i) => (
                <div key={i} style={{ padding: '10px', borderBottom: '1px solid #333', fontSize: '14px' }}>
                  <div style={{ color: '#64b5f6', fontWeight: 'bold' }}>{d.name || "Unknown"}</div>
                  <div style={{ color: '#888', display: 'flex', justifyContent: 'space-between' }}>
                    <span>{d.ip}</span>
                    <span>{d.mac}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

function Stat({ label, value, alert = false }: { label: string; value: string | number; alert?: boolean }) {
  return (
    <div className={styles.stat} style={alert ? { borderColor: '#e53935', backgroundColor: 'rgba(229,57,53,0.1)' } : {}}>
      <span className={styles.statValue} style={alert ? { color: '#e53935' } : {}}>{value}</span>
      <span className={styles.statLabel}>{label}</span>
    </div>
  );
}
