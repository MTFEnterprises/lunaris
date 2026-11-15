import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

function createLunarTexture() {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('Canvas 2D context is unavailable.');

  context.fillStyle = '#858585';
  context.fillRect(0, 0, canvas.width, canvas.height);

  let seed = 0x4c554e41;
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 0x100000000;
  };

  for (let index = 0; index < 620; index += 1) {
    const x = random() * canvas.width;
    const y = random() * canvas.height;
    const radius = 2 + random() ** 2 * 18;
    const crater = context.createRadialGradient(x, y, radius * 0.15, x, y, radius);
    crater.addColorStop(0, 'rgba(48, 48, 48, 0.85)');
    crater.addColorStop(0.68, 'rgba(100, 100, 100, 0.72)');
    crater.addColorStop(0.82, 'rgba(205, 205, 205, 0.78)');
    crater.addColorStop(1, 'rgba(75, 75, 75, 0.22)');
    context.fillStyle = crater;
    context.beginPath();
    context.arc(x, y, radius, 0, Math.PI * 2);
    context.fill();
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

export default function RotatingMoon3D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [renderError, setRenderError] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const context = canvas.getContext('webgl2', { alpha: true, antialias: true });
    if (!context) {
      console.error('The rotating Moon illustration requires WebGL 2.');
      setRenderError(true);
      return;
    }

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ canvas, context, alpha: true, antialias: true });
    } catch (error) {
      console.error('Unable to initialize the rotating Moon illustration.', error);
      setRenderError(true);
      return;
    }

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.z = 3.4;

    const texture = createLunarTexture();
    const geometry = new THREE.SphereGeometry(1, 96, 64);
    const material = new THREE.MeshStandardMaterial({
      map: texture,
      bumpMap: texture,
      bumpScale: 0.045,
      roughness: 1,
      metalness: 0,
    });
    const moon = new THREE.Mesh(geometry, material);
    moon.rotation.x = 0.18;
    scene.add(moon);
    scene.add(new THREE.AmbientLight(0xb7c5df, 1.15));

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
    keyLight.position.set(-3, 2, 4);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x7183a5, 0.55);
    fillLight.position.set(3, -1, -3);
    scene.add(fillLight);

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x030711, 1);
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const resize = () => {
      const { clientWidth, clientHeight } = canvas;
      if (clientWidth === 0 || clientHeight === 0) return;
      renderer.setSize(clientWidth, clientHeight, false);
      camera.aspect = clientWidth / clientHeight;
      camera.updateProjectionMatrix();
      renderer.render(scene, camera);
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(canvas);
    resize();

    let animationFrame = 0;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let previousFrameTime = 0;
    const animate = (timestamp: number) => {
      animationFrame = window.requestAnimationFrame(animate);
      if (previousFrameTime > 0) {
        const deltaSeconds = Math.min((timestamp - previousFrameTime) / 1000, 0.1);
        moon.rotation.y += deltaSeconds * 0.14;
      }
      previousFrameTime = timestamp;
      renderer.render(scene, camera);
    };
    if (!reducedMotion) animate();

    return () => {
      window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
      geometry.dispose();
      material.dispose();
      texture.dispose();
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative h-[260px] w-full overflow-hidden rounded-2xl border border-white/10 bg-[#030711]">
      <canvas ref={canvasRef} aria-label="Slowly rotating illustrative 3D Moon" className="h-full w-full" />
      {renderError && (
        <p className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-slate-400">
          3D rendering is unavailable in this browser.
        </p>
      )}
      <span className="absolute bottom-3 left-3 rounded-md border border-white/10 bg-slate-950/80 px-2 py-1 text-[10px] text-slate-400">
        Illustrative surface, not a geospatial texture
      </span>
    </div>
  );
}
