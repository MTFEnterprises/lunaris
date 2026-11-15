import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { SITES } from './data';

/* ================================================================== */
/*  Interactive 3D Moon (Three.js)                                     */
/*  - drag to rotate (with inertia), hover parallax, click hotspots    */
/*  - real sun direction: lit side follows today's lunar phase          */
/* ================================================================== */

export interface MoonGlobeProps {
  selected: number;
  onSelect: (index: number) => void;
  rotating: boolean;
  resetSignal: number;
  zoom: number;
  sunLon: number;
}

/** lat/lon (degrees) -> point on a sphere of radius r. Lon 0 faces +x by default. */
export function latLonToVec3(lat: number, lon: number, r: number) {
  const phi = ((90 - lat) * Math.PI) / 180;
  const theta = ((lon + 180) * Math.PI) / 180;
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta));
}

/** Rotation that brings (lat, lon) in front of the camera with north kept up. */
function facingQuat(lat: number, lon: number) {
  const qY = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), ((-90 - lon) * Math.PI) / 180);
  const qX = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), (lat * Math.PI) / 180);
  return qX.multiply(qY);
}

/* ------------------------- procedural textures ---------------------- */
function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// name, lat, lon, half-height (deg), half-width (deg)
const MARIA: [number, number, number, number][] = [
  [32.8, -15.6, 14, 20],
  [28, 17.5, 9, 12],
  [8.5, 31, 9, 15],
  [-4, 52, 8, 11],
  [17, 59, 5, 8],
  [18, -57, 20, 22],
  [-21, -16, 8, 12],
  [-24, -39, 5, 7],
  [58, -1, 4, 26],
  [-14, 5, 5, 8],
];

function makeMoonTextures() {
  const W = 2048;
  const H = 1024;
  const rand = mulberry32(20261114);

  const color = document.createElement('canvas');
  color.width = W;
  color.height = H;
  const c = color.getContext('2d');

  const bump = document.createElement('canvas');
  bump.width = W;
  bump.height = H;
  const b = bump.getContext('2d');

  const colorTex = new THREE.CanvasTexture(color);
  const bumpTex = new THREE.CanvasTexture(bump);
  if (!c || !b) return { colorTex, bumpTex };

  // base regolith
  c.fillStyle = '#a9a9ab';
  c.fillRect(0, 0, W, H);
  b.fillStyle = '#808080';
  b.fillRect(0, 0, W, H);

  // fine grain
  for (let i = 0; i < 26000; i++) {
    const x = rand() * W;
    const y = rand() * H;
    const v = 110 + Math.floor(rand() * 90);
    c.fillStyle = `rgba(${v},${v},${v},0.10)`;
    c.fillRect(x, y, 2 + rand() * 4, 2 + rand() * 4);
    const g = 90 + Math.floor(rand() * 90);
    b.fillStyle = `rgba(${g},${g},${g},0.10)`;
    b.fillRect(x, y, 2 + rand() * 4, 2 + rand() * 4);
  }

  // dark basaltic maria
  for (const [lat, lon, ry, rx] of MARIA) {
    const px = ((lon + 180) / 360) * W;
    const py = ((90 - lat) / 180) * H;
    const rpx = (rx / 360) * W;
    const rpy = (ry / 180) * H;
    c.save();
    c.translate(px, py);
    c.scale(1, rpy / rpx);
    const g = c.createRadialGradient(0, 0, 0, 0, 0, rpx);
    g.addColorStop(0, 'rgba(78,78,82,0.85)');
    g.addColorStop(0.65, 'rgba(84,84,88,0.62)');
    g.addColorStop(1, 'rgba(84,84,88,0)');
    c.fillStyle = g;
    c.beginPath();
    c.arc(0, 0, rpx, 0, Math.PI * 2);
    c.fill();
    c.restore();
  }

  // craters
  for (let i = 0; i < 2200; i++) {
    const lat = Math.asin(rand() * 2 - 1) * (180 / Math.PI);
    const x = rand() * W;
    const y = ((90 - lat) / 180) * H;
    const r = 1.5 + Math.pow(rand(), 4.2) * 34;
    const sx = 1 / Math.max(0.25, Math.cos((lat * Math.PI) / 180));

    c.save();
    c.translate(x, y);
    c.scale(sx, 1);
    const g = c.createRadialGradient(0, 0, 0, 0, 0, r);
    g.addColorStop(0, 'rgba(70,70,74,0.34)');
    g.addColorStop(0.72, 'rgba(90,90,94,0.14)');
    g.addColorStop(0.9, 'rgba(215,220,230,0.32)');
    g.addColorStop(1, 'rgba(215,220,230,0)');
    c.fillStyle = g;
    c.beginPath();
    c.arc(0, 0, r, 0, Math.PI * 2);
    c.fill();
    c.restore();

    b.save();
    b.translate(x, y);
    b.scale(sx, 1);
    const h = b.createRadialGradient(0, 0, 0, 0, 0, r);
    h.addColorStop(0, 'rgba(30,30,30,0.85)');
    h.addColorStop(0.72, 'rgba(60,60,60,0.35)');
    h.addColorStop(0.88, 'rgba(255,255,255,0.8)');
    h.addColorStop(1, 'rgba(255,255,255,0)');
    b.fillStyle = h;
    b.beginPath();
    b.arc(0, 0, r, 0, Math.PI * 2);
    b.fill();
    b.restore();
  }

  colorTex.colorSpace = THREE.SRGBColorSpace;
  colorTex.anisotropy = 4;
  colorTex.needsUpdate = true;
  bumpTex.needsUpdate = true;
  return { colorTex, bumpTex };
}

function disposeObject(root: THREE.Object3D) {
  root.traverse((o) => {
    if (o instanceof THREE.Mesh || o instanceof THREE.Line || o instanceof THREE.Points) {
      o.geometry.dispose();
      const m = o.material;
      if (Array.isArray(m)) m.forEach((x) => x.dispose());
      else m.dispose();
    }
  });
}

/* ------------------------------ component --------------------------- */
export default function MoonGlobe({ selected, onSelect, rotating, resetSignal, zoom, sunLon }: MoonGlobeProps) {
  const hostRef = useRef<HTMLDivElement>(null);

  // latest props, readable from inside the animation loop
  const selectedRef = useRef(selected);
  const onSelectRef = useRef(onSelect);
  const rotatingRef = useRef(rotating);
  const zoomRef = useRef(zoom);
  const sunLonRef = useRef(sunLon);

  // scene handles shared between effects
  const flyRef = useRef<THREE.Quaternion | null>(null);
  const lightRef = useRef<THREE.DirectionalLight | null>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    selectedRef.current = selected;
    onSelectRef.current = onSelect;
    rotatingRef.current = rotating;
    zoomRef.current = zoom;
  }, [selected, onSelect, rotating, zoom]);

  /* ---- main scene (created once) ---- */
  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);
    const canvas = renderer.domElement;
    canvas.style.display = 'block';
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.touchAction = 'none';
    canvas.style.cursor = 'grab';
    host.appendChild(canvas);

    /* lights */
    scene.add(new THREE.AmbientLight(0xc4cad6, 0.34));
    const rim = new THREE.DirectionalLight(0x3b82f6, 0.9);
    rim.position.set(-3, 1.5, -2);
    scene.add(rim);
    const sun = new THREE.DirectionalLight(0xfff6e8, 3.0);
    sun.position.copy(latLonToVec3(0, sunLonRef.current, 6));
    lightRef.current = sun;

    /* moon */
    const moonGroup = new THREE.Group();
    scene.add(moonGroup);
    moonGroup.add(sun); // light rotates with the moon surface: sun stays at a fixed lunar longitude

    const { colorTex, bumpTex } = makeMoonTextures();
    const moonMesh = new THREE.Mesh(
      new THREE.SphereGeometry(1, 96, 64),
      new THREE.MeshStandardMaterial({
        map: colorTex,
        bumpMap: bumpTex,
        bumpScale: 0.035,
        roughness: 1,
        metalness: 0,
        emissive: new THREE.Color(0x1a3158), // faint earthshine on the night side
        emissiveIntensity: 0.8,
      })
    );
    moonGroup.add(moonMesh);

    // graticule
    const gPts: number[] = [];
    const push = (v: THREE.Vector3) => gPts.push(v.x, v.y, v.z);
    for (let lat = -60; lat <= 60; lat += 30) {
      for (let lon = -180; lon < 180; lon += 6) {
        push(latLonToVec3(lat, lon, 1.003));
        push(latLonToVec3(lat, lon + 6, 1.003));
      }
    }
    for (let lon = -180; lon < 180; lon += 30) {
      for (let lat = -90; lat < 90; lat += 6) {
        push(latLonToVec3(lat, lon, 1.003));
        push(latLonToVec3(lat + 6, lon, 1.003));
      }
    }
    const gGeo = new THREE.BufferGeometry();
    gGeo.setAttribute('position', new THREE.Float32BufferAttribute(gPts, 3));
    moonGroup.add(new THREE.LineSegments(gGeo, new THREE.LineBasicMaterial({ color: 0x67e8f9, transparent: true, opacity: 0.1 })));

    // dot layer (fibonacci sphere)
    const dPts: number[] = [];
    const N = 1600;
    const golden = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < N; i++) {
      const y = 1 - (i / (N - 1)) * 2;
      const rr = Math.sqrt(1 - y * y);
      const t = golden * i;
      dPts.push(Math.cos(t) * rr * 1.008, y * 1.008, Math.sin(t) * rr * 1.008);
    }
    const dGeo = new THREE.BufferGeometry();
    dGeo.setAttribute('position', new THREE.Float32BufferAttribute(dPts, 3));
    moonGroup.add(new THREE.Points(dGeo, new THREE.PointsMaterial({ color: 0xbae6fd, size: 0.006, transparent: true, opacity: 0.35, depthWrite: false })));

    // fresnel glow
    const glow = new THREE.Mesh(
      new THREE.SphereGeometry(1.14, 64, 48),
      new THREE.ShaderMaterial({
        transparent: true,
        side: THREE.BackSide,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
        vertexShader: 'varying vec3 vN; void main(){ vN = normalize(normalMatrix * normal); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
        fragmentShader: 'varying vec3 vN; void main(){ float i = pow(max(0.0, 0.72 - dot(vN, vec3(0.0,0.0,1.0))), 3.0); gl_FragColor = vec4(0.18,0.5,1.0,1.0) * i * 1.15; }',
      })
    );
    scene.add(glow);

    /* hotspots */
    interface Hot {
      core: THREE.Mesh;
      ring: THREE.Mesh;
      coreMat: THREE.MeshBasicMaterial;
      ringMat: THREE.MeshBasicMaterial;
    }
    const hots: Hot[] = [];
    const hitSpheres: THREE.Mesh[] = [];
    SITES.forEach((s, i) => {
      const pos = latLonToVec3(s.lat, s.lon, 1.012);
      const normal = pos.clone().normalize();
      const coreMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8 });
      const core = new THREE.Mesh(new THREE.SphereGeometry(0.014, 16, 16), coreMat);
      core.position.copy(pos);
      const ringMat = new THREE.MeshBasicMaterial({ color: 0x67e8f9, transparent: true, opacity: 0.8, side: THREE.DoubleSide, depthWrite: false });
      const ring = new THREE.Mesh(new THREE.RingGeometry(0.022, 0.028, 40), ringMat);
      ring.position.copy(pos);
      ring.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), normal);
      const hit = new THREE.Mesh(
        new THREE.SphereGeometry(0.07, 12, 12),
        new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false })
      );
      hit.position.copy(pos);
      hit.userData.siteIndex = i;
      moonGroup.add(core, ring, hit);
      hots.push({ core, ring, coreMat, ringMat });
      hitSpheres.push(hit);
    });

    /* orbit rings + satellites */
    const orbitGroup = new THREE.Group();
    scene.add(orbitGroup);
    const rings = [
      { r: 1.3, tiltX: 1.15, tiltZ: 0.2, speed: 0.55 },
      { r: 1.45, tiltX: 0.55, tiltZ: -0.5, speed: -0.38 },
      { r: 1.6, tiltX: -0.35, tiltZ: 0.7, speed: 0.27 },
    ].map((cfg, i) => {
      const g = new THREE.Group();
      g.rotation.set(cfg.tiltX, 0, cfg.tiltZ);
      const pts: THREE.Vector3[] = [];
      for (let k = 0; k <= 128; k++) {
        const a = (k / 128) * Math.PI * 2;
        pts.push(new THREE.Vector3(Math.cos(a) * cfg.r, 0, Math.sin(a) * cfg.r));
      }
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x38bdf8, transparent: true, opacity: 0.22 })));
      const sat = new THREE.Mesh(new THREE.SphereGeometry(0.02, 12, 12), new THREE.MeshBasicMaterial({ color: i === 0 ? 0xfbbf24 : 0xe0f2fe }));
      g.add(sat);
      orbitGroup.add(g);
      return { sat, r: cfg.r, speed: cfg.speed, phase: i * 2.1 };
    });

    /* stars */
    const sPts: number[] = [];
    const sr = mulberry32(7);
    for (let i = 0; i < 1800; i++) {
      const u = sr() * 2 - 1;
      const t = sr() * Math.PI * 2;
      const rr = Math.sqrt(1 - u * u);
      const d = 25 + sr() * 10;
      sPts.push(Math.cos(t) * rr * d, u * d, Math.sin(t) * rr * d);
    }
    const sGeo = new THREE.BufferGeometry();
    sGeo.setAttribute('position', new THREE.Float32BufferAttribute(sPts, 3));
    scene.add(new THREE.Points(sGeo, new THREE.PointsMaterial({ color: 0xffffff, size: 0.07, transparent: true, opacity: 0.75, depthWrite: false })));

    // a few brighter stars
    const bPts: number[] = [];
    for (let i = 0; i < 140; i++) {
      const u = sr() * 2 - 1;
      const t = sr() * Math.PI * 2;
      const rr = Math.sqrt(1 - u * u);
      const d = 24 + sr() * 8;
      bPts.push(Math.cos(t) * rr * d, u * d, Math.sin(t) * rr * d);
    }
    const bGeo = new THREE.BufferGeometry();
    bGeo.setAttribute('position', new THREE.Float32BufferAttribute(bPts, 3));
    scene.add(new THREE.Points(bGeo, new THREE.PointsMaterial({ color: 0xdbeafe, size: 0.16, transparent: true, opacity: 0.95, depthWrite: false })));

    /* start orientation: lunar longitude 0 faces the camera */
    moonGroup.quaternion.copy(facingQuat(0, 0));

    /* sizing */
    let aspect = 1;
    const resize = () => {
      const w = Math.max(1, host.clientWidth);
      const h = Math.max(1, host.clientHeight);
      aspect = w / h;
      renderer.setSize(w, h, false);
      camera.aspect = aspect;
      camera.updateProjectionMatrix();
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(host);

    /* interaction */
    const raycaster = new THREE.Raycaster();
    const ndc = new THREE.Vector2();
    const pick = (clientX: number, clientY: number) => {
      const rect = canvas.getBoundingClientRect();
      ndc.set(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
      raycaster.setFromCamera(ndc, camera);
      const first = raycaster.intersectObjects([moonMesh, ...hitSpheres], false)[0];
      const idx = first ? (first.object.userData.siteIndex as number | undefined) : undefined;
      return typeof idx === 'number' ? idx : -1;
    };

    let dragging = false;
    let moved = 0;
    let lastX = 0;
    let lastY = 0;
    let velX = 0;
    let velY = 0;
    let mx = 0;
    let my = 0;
    const qTmp = new THREE.Quaternion();
    const qA = new THREE.Quaternion();
    const qB = new THREE.Quaternion();
    const AX = new THREE.Vector3(1, 0, 0);
    const AY = new THREE.Vector3(0, 1, 0);

    const rotateBy = (dx: number, dy: number) => {
      qA.setFromAxisAngle(AY, dx);
      qB.setFromAxisAngle(AX, dy);
      qTmp.copy(qA).multiply(qB);
      moonGroup.quaternion.premultiply(qTmp).normalize();
    };

    const onDown = (e: PointerEvent) => {
      dragging = true;
      moved = 0;
      lastX = e.clientX;
      lastY = e.clientY;
      velX = 0;
      velY = 0;
      flyRef.current = null;
      canvas.setPointerCapture(e.pointerId);
      canvas.style.cursor = 'grabbing';
    };
    const onMove = (e: PointerEvent) => {
      const rect = host.getBoundingClientRect();
      mx = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      my = ((e.clientY - rect.top) / rect.height) * 2 - 1;
      if (dragging) {
        const dx = e.clientX - lastX;
        const dy = e.clientY - lastY;
        lastX = e.clientX;
        lastY = e.clientY;
        moved += Math.abs(dx) + Math.abs(dy);
        velX = dx * 0.005;
        velY = dy * 0.005;
        rotateBy(velX, velY);
      } else {
        canvas.style.cursor = pick(e.clientX, e.clientY) >= 0 ? 'pointer' : 'grab';
      }
    };
    const onUp = (e: PointerEvent) => {
      if (!dragging) return;
      dragging = false;
      if (canvas.hasPointerCapture(e.pointerId)) canvas.releasePointerCapture(e.pointerId);
      canvas.style.cursor = 'grab';
      if (moved < 5) {
        velX = 0;
        velY = 0;
        const idx = pick(e.clientX, e.clientY);
        if (idx >= 0) onSelectRef.current(idx);
      }
    };
    const onLeave = () => {
      mx = 0;
      my = 0;
    };
    canvas.addEventListener('pointerdown', onDown);
    canvas.addEventListener('pointermove', onMove);
    canvas.addEventListener('pointerup', onUp);
    canvas.addEventListener('pointercancel', onUp);
    host.addEventListener('pointerleave', onLeave);

    /* loop */
    let raf = 0;
    let last = performance.now();
    let camDist = zoomRef.current;
    let camX = 0;
    let camY = 0;

    const loop = (now: number) => {
      raf = requestAnimationFrame(loop);
      const dt = Math.min(0.05, (now - last) / 1000);
      last = now;
      const t = now / 1000;

      // fly-to
      const target = flyRef.current;
      if (target && !dragging) {
        moonGroup.quaternion.slerp(target, 1 - Math.exp(-dt * 5));
        if (moonGroup.quaternion.angleTo(target) < 0.002) {
          moonGroup.quaternion.copy(target);
          flyRef.current = null;
        }
      } else if (!dragging) {
        // inertia
        if (Math.abs(velX) > 1e-5 || Math.abs(velY) > 1e-5) {
          rotateBy(velX * dt * 60, velY * dt * 60);
          const damp = Math.pow(0.95, dt * 60);
          velX *= damp;
          velY *= damp;
        } else if (rotatingRef.current) {
          rotateBy(0.09 * dt, 0);
        }
      }

      // camera: zoom (fit narrow containers) + soft parallax
      const fit = Math.max(1, 0.95 / aspect);
      camDist += (zoomRef.current * fit - camDist) * (1 - Math.exp(-dt * 6));
      camX += (mx * 0.18 - camX) * (1 - Math.exp(-dt * 3));
      camY += (-my * 0.12 - camY) * (1 - Math.exp(-dt * 3));
      camera.position.set(camX, camY, camDist);
      camera.lookAt(0, 0, 0);

      // satellites
      for (const s of rings) {
        const a = s.phase + t * s.speed;
        s.sat.position.set(Math.cos(a) * s.r, 0, Math.sin(a) * s.r);
      }

      // hotspot pulse
      hots.forEach((h, i) => {
        const active = i === selectedRef.current;
        const ph = (t * 0.8 + i * 0.3) % 1;
        const base = active ? 1.5 : 1;
        h.ring.scale.setScalar(base * (1 + ph * (active ? 1.6 : 1.1)));
        h.ringMat.opacity = (active ? 0.95 : 0.7) * (1 - ph);
        h.core.scale.setScalar(active ? 1.5 : 1);
        h.coreMat.color.setHex(active ? 0xffffff : 0x38bdf8);
      });

      renderer.render(scene, camera);
    };
    raf = requestAnimationFrame(loop);

    mountedRef.current = true;

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      canvas.removeEventListener('pointerdown', onDown);
      canvas.removeEventListener('pointermove', onMove);
      canvas.removeEventListener('pointerup', onUp);
      canvas.removeEventListener('pointercancel', onUp);
      host.removeEventListener('pointerleave', onLeave);
      disposeObject(scene);
      colorTex.dispose();
      bumpTex.dispose();
      renderer.dispose();
      if (canvas.parentElement === host) host.removeChild(canvas);
      lightRef.current = null;
      flyRef.current = null;
      mountedRef.current = false;
    };
  }, []);

  /* ---- sun direction follows the lunar phase ---- */
  useEffect(() => {
    sunLonRef.current = sunLon;
    lightRef.current?.position.copy(latLonToVec3(0, sunLon, 6));
  }, [sunLon]);

  /* ---- fly to the selected site ---- */
  useEffect(() => {
    const s = SITES[selected];
    if (!s) return;
    flyRef.current = facingQuat(s.lat, s.lon);
  }, [selected]);

  /* ---- reset view ---- */
  const firstReset = useRef(true);
  useEffect(() => {
    if (firstReset.current) {
      firstReset.current = false;
      return;
    }
    flyRef.current = facingQuat(0, 0);
  }, [resetSignal]);

  return <div ref={hostRef} className="absolute inset-0" />;
}
