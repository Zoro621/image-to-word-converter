"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";

function ParticleField() {
  const ref = useRef<THREE.Points>(null!);

  const count = 1600;
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      arr[i * 3]     = (Math.random() - 0.5) * 22;
      arr[i * 3 + 1] = (Math.random() - 0.5) * 22;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 12;
    }
    return arr;
  }, []);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    ref.current.rotation.y = t * 0.035;
    ref.current.rotation.x = Math.sin(t * 0.012) * 0.08;
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#6c63ff"
        size={0.04}
        sizeAttenuation
        depthWrite={false}
        opacity={0.55}
      />
    </Points>
  );
}

function FloatingDocument({
  position,
  speed,
  scale,
}: {
  position: [number, number, number];
  speed: number;
  scale: number;
}) {
  const ref = useRef<THREE.Mesh>(null!);
  const baseY = position[1];

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    ref.current.position.y = baseY + Math.sin(t * speed) * 0.4;
    ref.current.rotation.z = Math.sin(t * speed * 0.5) * 0.06;
    ref.current.rotation.y = t * 0.1 * speed;
  });

  return (
    <mesh ref={ref} position={position} scale={scale}>
      <boxGeometry args={[0.55, 0.72, 0.04]} />
      <meshStandardMaterial
        color="#6c63ff"
        transparent
        opacity={0.12}
        roughness={0.1}
        metalness={0.3}
        emissive="#6c63ff"
        emissiveIntensity={0.4}
        wireframe={false}
      />
    </mesh>
  );
}



const documents: { position: [number, number, number]; speed: number; scale: number }[] = [
  { position: [-5.5, 1.5, -2], speed: 0.7, scale: 0.9 },
  { position: [ 5.2, -1.2, -1], speed: 0.5, scale: 0.7 },
  { position: [-3.8, -2.8, -3], speed: 0.9, scale: 0.6 },
  { position: [ 4.0, 2.5, -2.5], speed: 0.6, scale: 1.0 },
  { position: [ 0.5, 3.5, -3], speed: 0.8, scale: 0.75 },
  { position: [-5.0, 0.0, -1.5], speed: 0.4, scale: 0.5 },
];

export default function ThreeBackground() {
  return (
    <div className="fixed inset-0 pointer-events-none z-0">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        gl={{ alpha: true, antialias: true }}
        dpr={[1, 1.5]}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} intensity={0.8} color="#6c63ff" />
        <pointLight position={[-5, -5, -5]} intensity={0.4} color="#22d3ee" />

        <ParticleField />
        {documents.map((d, i) => (
          <FloatingDocument key={i} {...d} />
        ))}
      </Canvas>

      {/* Radial gradient overlay to anchor content area */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "radial-gradient(ellipse 80% 60% at 50% 50%, transparent 30%, var(--bg-base) 90%)",
        }}
      />
    </div>
  );
}
