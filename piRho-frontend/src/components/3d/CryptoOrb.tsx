"use client";

import { useRef, useMemo, Suspense } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { 
  Float, 
  MeshDistortMaterial, 
  Sphere, 
  Trail,
  Stars,
  useTexture,
} from "@react-three/drei";
import * as THREE from "three";

// Main exported component - wraps Canvas
export function CryptoOrb({ className }: { className?: string }) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: [0, 0, 5], fov: 45 }}
        dpr={[1, 2]}
        gl={{ antialias: true, alpha: true }}
      >
        <Suspense fallback={null}>
          <Scene />
        </Suspense>
      </Canvas>
    </div>
  );
}

function Scene() {
  const { mouse } = useThree();
  
  return (
    <>
      {/* Ambient light */}
      <ambientLight intensity={0.2} />
      
      {/* Main lights */}
      <pointLight position={[10, 10, 10]} intensity={1} color="#00FFFF" />
      <pointLight position={[-10, -10, -10]} intensity={0.5} color="#FF00FF" />
      <pointLight position={[0, 10, 0]} intensity={0.3} color="#a855f7" />
      
      {/* Stars background */}
      <Stars 
        radius={50} 
        depth={50} 
        count={1000} 
        factor={2} 
        saturation={0} 
        fade 
        speed={0.5}
      />
      
      {/* Main orb */}
      <Float 
        speed={2} 
        rotationIntensity={0.5} 
        floatIntensity={0.5}
      >
        <GlowingOrb mouse={mouse} />
      </Float>
      
      {/* Orbiting particles */}
      <OrbitingParticles />
      
      {/* Neural network connections */}
      <NeuralConnections />
      
      {/* Outer rings */}
      <OrbitRings />
    </>
  );
}

function GlowingOrb({ mouse }: { mouse: THREE.Vector2 }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const materialRef = useRef<any>(null);

  useFrame((state) => {
    if (meshRef.current) {
      // Rotate based on mouse position
      meshRef.current.rotation.x = THREE.MathUtils.lerp(
        meshRef.current.rotation.x,
        mouse.y * 0.3,
        0.05
      );
      meshRef.current.rotation.y = THREE.MathUtils.lerp(
        meshRef.current.rotation.y,
        mouse.x * 0.3 + state.clock.elapsedTime * 0.2,
        0.05
      );
    }
    
    if (materialRef.current) {
      // Animate distortion
      materialRef.current.distort = 0.3 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
    }
  });

  return (
    <group>
      {/* Inner glowing core */}
      <Sphere ref={meshRef} args={[1, 64, 64]}>
        <MeshDistortMaterial
          ref={materialRef}
          color="#00d4ff"
          attach="material"
          distort={0.3}
          speed={2}
          roughness={0.2}
          metalness={0.8}
          emissive="#00FFFF"
          emissiveIntensity={0.2}
        />
      </Sphere>
      
      {/* Wireframe overlay */}
      <Sphere args={[1.02, 32, 32]}>
        <meshBasicMaterial 
          color="#00FFFF" 
          wireframe 
          transparent 
          opacity={0.15} 
        />
      </Sphere>
      
      {/* Outer glow sphere */}
      <Sphere args={[1.3, 32, 32]}>
        <meshBasicMaterial 
          color="#00FFFF" 
          transparent 
          opacity={0.05}
          side={THREE.BackSide}
        />
      </Sphere>
    </group>
  );
}

function OrbitingParticles() {
  const particlesRef = useRef<THREE.Points>(null);
  const count = 100;

  const [positions, colors] = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    
    const cyanColor = new THREE.Color("#00FFFF");
    const magentaColor = new THREE.Color("#FF00FF");
    const purpleColor = new THREE.Color("#a855f7");
    const colorOptions = [cyanColor, magentaColor, purpleColor];

    for (let i = 0; i < count; i++) {
      const radius = 1.8 + Math.random() * 0.8;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      
      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
      
      const color = colorOptions[Math.floor(Math.random() * colorOptions.length)];
      colors[i * 3] = color.r;
      colors[i * 3 + 1] = color.g;
      colors[i * 3 + 2] = color.b;
    }
    
    return [positions, colors];
  }, []);

  useFrame((state) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = state.clock.elapsedTime * 0.1;
      particlesRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.05) * 0.2;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
        <bufferAttribute
          attach="attributes-color"
          args={[colors, 3]}
        />
      </bufferGeometry>
      <pointsMaterial 
        size={0.03} 
        vertexColors 
        transparent 
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

function NeuralConnections() {
  const groupRef = useRef<THREE.Group>(null);
  const nodeCount = 8;

  const nodes = useMemo(() => {
    const nodes: THREE.Vector3[] = [];
    for (let i = 0; i < nodeCount; i++) {
      const radius = 2 + Math.random() * 0.5;
      const theta = (i / nodeCount) * Math.PI * 2;
      const phi = Math.PI / 2 + (Math.random() - 0.5) * 0.5;
      
      nodes.push(new THREE.Vector3(
        radius * Math.sin(phi) * Math.cos(theta),
        radius * Math.sin(phi) * Math.sin(theta) - 0.5,
        radius * Math.cos(phi)
      ));
    }
    return nodes;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = state.clock.elapsedTime * 0.15;
    }
  });

  return (
    <group ref={groupRef}>
      {/* Connection lines */}
      {nodes.map((node, i) => (
        <group key={i}>
          {/* Node */}
          <mesh position={node}>
            <sphereGeometry args={[0.05, 16, 16]} />
            <meshBasicMaterial color="#00FFFF" />
          </mesh>
          
          {/* Line to center */}
          <line>
            <bufferGeometry>
              <bufferAttribute
                attach="attributes-position"
                args={[new Float32Array([0, 0, 0, node.x, node.y, node.z]), 3]}
              />
            </bufferGeometry>
            <lineBasicMaterial color="#00FFFF" transparent opacity={0.2} />
          </line>
          
          {/* Line to next node */}
          {i < nodes.length - 1 && (
            <line>
              <bufferGeometry>
                <bufferAttribute
                  attach="attributes-position"
                  args={[new Float32Array([
                    node.x, node.y, node.z,
                    nodes[i + 1].x, nodes[i + 1].y, nodes[i + 1].z
                  ]), 3]}
                />
              </bufferGeometry>
              <lineBasicMaterial color="#FF00FF" transparent opacity={0.15} />
            </line>
          )}
        </group>
      ))}
    </group>
  );
}

function OrbitRings() {
  const ring1Ref = useRef<THREE.Mesh>(null);
  const ring2Ref = useRef<THREE.Mesh>(null);
  const ring3Ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    
    if (ring1Ref.current) {
      ring1Ref.current.rotation.x = Math.PI / 2;
      ring1Ref.current.rotation.z = t * 0.3;
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.x = Math.PI / 3;
      ring2Ref.current.rotation.z = -t * 0.2;
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.x = Math.PI / 4;
      ring3Ref.current.rotation.y = t * 0.25;
    }
  });

  return (
    <>
      <mesh ref={ring1Ref}>
        <torusGeometry args={[1.6, 0.01, 16, 100]} />
        <meshBasicMaterial color="#00FFFF" transparent opacity={0.3} />
      </mesh>
      <mesh ref={ring2Ref}>
        <torusGeometry args={[2, 0.008, 16, 100]} />
        <meshBasicMaterial color="#FF00FF" transparent opacity={0.2} />
      </mesh>
      <mesh ref={ring3Ref}>
        <torusGeometry args={[2.4, 0.006, 16, 100]} />
        <meshBasicMaterial color="#a855f7" transparent opacity={0.15} />
      </mesh>
    </>
  );
}

// Simpler fallback for reduced motion / low performance
export function CryptoOrbSimple({ className }: { className?: string }) {
  return (
    <div className={className}>
      <div className="relative w-full h-full flex items-center justify-center">
        {/* Static glowing orb */}
        <div 
          className="w-48 h-48 rounded-full relative animate-pulse-slow"
          style={{
            background: "radial-gradient(circle at 30% 30%, #00d4ff 0%, #0891b2 50%, #0f172a 100%)",
            boxShadow: "0 0 60px rgba(0, 255, 255, 0.4), 0 0 120px rgba(0, 255, 255, 0.2), inset 0 0 60px rgba(0, 255, 255, 0.1)",
          }}
        >
          {/* Wireframe overlay effect */}
          <div 
            className="absolute inset-0 rounded-full opacity-20"
            style={{
              background: `
                repeating-linear-gradient(0deg, transparent, transparent 8px, rgba(0, 255, 255, 0.3) 8px, rgba(0, 255, 255, 0.3) 9px),
                repeating-linear-gradient(90deg, transparent, transparent 8px, rgba(0, 255, 255, 0.3) 8px, rgba(0, 255, 255, 0.3) 9px)
              `,
            }}
          />
        </div>
        
        {/* Orbit rings */}
        <div 
          className="absolute w-72 h-72 rounded-full border border-neon-500/30 animate-spin-slow"
          style={{ animationDuration: "20s" }}
        />
        <div 
          className="absolute w-80 h-80 rounded-full border border-magenta-500/20 animate-spin-slow"
          style={{ animationDuration: "25s", animationDirection: "reverse" }}
        />
        
        {/* Glow effect */}
        <div 
          className="absolute w-64 h-64 rounded-full blur-3xl opacity-30"
          style={{
            background: "radial-gradient(circle, #00FFFF 0%, transparent 70%)",
          }}
        />
      </div>
    </div>
  );
}

// Trading chart visualization (alternative hero)
export function TradingChart3D({ className }: { className?: string }) {
  return (
    <div className={className}>
      <Canvas camera={{ position: [0, 2, 5], fov: 50 }}>
        <Suspense fallback={null}>
          <ChartScene />
        </Suspense>
      </Canvas>
    </div>
  );
}

function ChartScene() {
  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#00FFFF" />
      
      <Stars radius={50} depth={50} count={500} factor={2} fade speed={0.5} />
      
      {/* 3D Candlesticks */}
      <CandlestickChart />
    </>
  );
}

function CandlestickChart() {
  const groupRef = useRef<THREE.Group>(null);
  
  const candles = useMemo(() => {
    const data = [];
    let price = 50;
    
    for (let i = 0; i < 20; i++) {
      const open = price;
      const change = (Math.random() - 0.5) * 10;
      const close = price + change;
      const high = Math.max(open, close) + Math.random() * 3;
      const low = Math.min(open, close) - Math.random() * 3;
      
      data.push({
        x: i * 0.4 - 4,
        open,
        close,
        high,
        low,
        bullish: close > open,
      });
      
      price = close;
    }
    
    return data;
  }, []);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.1;
    }
  });

  return (
    <group ref={groupRef} position={[0, -1, 0]}>
      {candles.map((candle, i) => {
        const bodyHeight = Math.abs(candle.close - candle.open) * 0.05;
        const bodyY = ((candle.open + candle.close) / 2 - 50) * 0.05;
        const wickHeight = (candle.high - candle.low) * 0.05;
        const wickY = ((candle.high + candle.low) / 2 - 50) * 0.05;
        
        return (
          <group key={i} position={[candle.x, 0, 0]}>
            {/* Candle body */}
            <mesh position={[0, bodyY, 0]}>
              <boxGeometry args={[0.2, Math.max(bodyHeight, 0.02), 0.2]} />
              <meshStandardMaterial 
                color={candle.bullish ? "#00FFFF" : "#FF00FF"}
                emissive={candle.bullish ? "#00FFFF" : "#FF00FF"}
                emissiveIntensity={0.3}
              />
            </mesh>
            
            {/* Wick */}
            <mesh position={[0, wickY, 0]}>
              <boxGeometry args={[0.02, wickHeight, 0.02]} />
              <meshBasicMaterial color={candle.bullish ? "#00FFFF" : "#FF00FF"} />
            </mesh>
          </group>
        );
      })}
      
      {/* Base grid */}
      <gridHelper args={[10, 20, "#00FFFF", "#1e293b"]} position={[0, -2.5, 0]} />
    </group>
  );
}

