// web-app/src/components/LiveMap.tsx
"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";

interface Analytics {
  movement_detected: boolean;
  active_zone: string;
  highest_variance_score: number;
  node_variances: Record<string, number>;
  tracked_zones: string[];
}

export default function LiveMap({ analytics }: { analytics?: Analytics }) {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const markerRef = useRef<THREE.Mesh | null>(null);
  const zonesMap = useRef<Map<string, THREE.Mesh>>(new Map());
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);

  useEffect(() => {
    if (!mountRef.current) return;

    // 1. Setup Scene, Camera, Renderer
    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#111111');
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    // Position camera for an isometric-ish top-down view
    camera.position.set(0, 15, 15);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 2. Add Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 2); // Soft white light
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 5);
    scene.add(directionalLight);

    // 3. Add a Floor Grid
    const gridHelper = new THREE.GridHelper(20, 20, 0x444444, 0x222222);
    scene.add(gridHelper);

    // 4. Create the Movement Marker (glowing sphere)
    const markerGeo = new THREE.SphereGeometry(0.8, 32, 32);
    const markerMat = new THREE.MeshStandardMaterial({ 
      color: 0xff3333, 
      emissive: 0xff0000,
      emissiveIntensity: 0.5,
      transparent: true,
      opacity: 0.9
    });
    const marker = new THREE.Mesh(markerGeo, markerMat);
    marker.position.set(0, 1, 0); // Start in center
    marker.visible = false; // Hide until movement detected
    scene.add(marker);
    markerRef.current = marker;

    // 5. Animation Loop
    let animationFrameId: number;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      
      // Gentle pulsing effect for the marker
      if (markerRef.current) {
        const pulse = Math.sin(Date.now() * 0.005) * 0.2 + 0.8;
        markerRef.current.scale.set(pulse, pulse, pulse);
      }

      renderer.render(scene, camera);
    };
    animate();

    // 6. Handle Window Resize
    const handleResize = () => {
      if (!mountRef.current) return;
      const w = mountRef.current.clientWidth;
      const h = mountRef.current.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  // Update Scene when Analytics data changes
  useEffect(() => {
    if (!sceneRef.current || !analytics) return;

    const scene = sceneRef.current;

    // 1. Manage Zones (Boxes)
    // For this simple demo, we arrange unknown zones in a circle
    const radius = 5;
    const zones = analytics.tracked_zones || [];
    
    zones.forEach((zoneId, index) => {
      if (!zonesMap.current.has(zoneId)) {
        // Create new zone representation
        const angle = (index / (zones.length || 1)) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;

        const boxGeo = new THREE.BoxGeometry(2, 0.2, 2);
        const boxMat = new THREE.MeshStandardMaterial({ 
          color: 0x1976d2, 
          transparent: true, 
          opacity: 0.3 
        });
        const box = new THREE.Mesh(boxGeo, boxMat);
        box.position.set(x, 0.1, z);
        
        scene.add(box);
        zonesMap.current.set(zoneId, box);
      }
      
      // Highlight the active zone
      const box = zonesMap.current.get(zoneId);
      if (box) {
        const mat = box.material as THREE.MeshStandardMaterial;
        if (zoneId === analytics.active_zone) {
          mat.color.setHex(0x42a5f5);
          mat.opacity = 0.6;
        } else {
          mat.color.setHex(0x1976d2);
          mat.opacity = 0.3;
        }
      }
    });

    // 2. Manage Movement Marker
    if (markerRef.current) {
      if (analytics.movement_detected && analytics.active_zone !== "Unknown") {
        markerRef.current.visible = true;
        
        // Move marker to active zone
        const targetBox = zonesMap.current.get(analytics.active_zone);
        if (targetBox) {
          // Simple instant teleport for now. Smooth lerping could be added here.
          markerRef.current.position.x = targetBox.position.x;
          markerRef.current.position.z = targetBox.position.z;
        }
      } else {
        markerRef.current.visible = false;
      }
    }

  }, [analytics]);

  return <div ref={mountRef} style={{ width: "100%", height: "100%" }} />;
}
