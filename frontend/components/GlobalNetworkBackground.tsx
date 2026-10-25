"use client";

import { useEffect, useRef } from "react";

interface Node {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  baseAlpha: number;
  pulsePhase: number;
  pulseSpeed: number;
  sparklePhase: number;
  sparkleSpeed: number;
  color: string;
}

interface PulseEdge {
  fromIndex: number;
  toIndex: number;
  progress: number;
  speed: number;
  color: string;
}

const PALETTE_DARK = [
  "rgba(59, 130, 246, ", // Electric Blue
  "rgba(34, 211, 238, ", // Cyan
  "rgba(147, 197, 253, ", // Soft Ice Blue
  "rgba(167, 139, 250, ", // Subtle Violet
];

const PALETTE_LIGHT = [
  "rgba(37, 99, 235, ",  // Primary Blue
  "rgba(8, 145, 178, ",  // Cyan
  "rgba(124, 58, 237, ", // Subtle Violet
  "rgba(14, 165, 233, ", // Sky Blue
];

export default function GlobalNetworkBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    let isLight = document.documentElement.getAttribute("data-theme") === "light";
    canvas.style.opacity = isLight ? "0.65" : "0.88";

    // Check prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const dpr = Math.min(window.devicePixelRatio || 1, 2);

    const setupCanvasSize = () => {
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    setupCanvasSize();

    // Dense scientific node network (75 - 140 nodes across viewport)
    const nodeCount = Math.min(Math.max(Math.floor((width * height) / 13000), 75), 140);
    const nodes: Node[] = [];

    const getPalette = () => (isLight ? PALETTE_LIGHT : PALETTE_DARK);

    for (let i = 0; i < nodeCount; i++) {
      const palette = getPalette();
      const paletteBase = palette[Math.floor(Math.random() * palette.length)];
      // Faster, fluid and lively velocity
      const moveSpeed = 0.45 + Math.random() * 0.55;
      const angle = Math.random() * Math.PI * 2;
      nodes.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: Math.cos(angle) * moveSpeed,
        vy: Math.sin(angle) * moveSpeed,
        radius: 1.3 + Math.random() * 1.6,
        baseAlpha: 0.35 + Math.random() * 0.35,
        pulsePhase: Math.random() * Math.PI * 2,
        pulseSpeed: 0.015 + Math.random() * 0.025,
        sparklePhase: Math.random() * Math.PI * 2,
        sparkleSpeed: 0.03 + Math.random() * 0.05,
        color: paletteBase,
      });
    }

    // Active light pulses travelling along network edges
    const maxPulses = 18;
    const pulses: PulseEdge[] = [];

    const spawnPulse = () => {
      if (pulses.length >= maxPulses) return;
      const fromIdx = Math.floor(Math.random() * nodes.length);
      let bestNeighbor = -1;
      let bestDist = Infinity;
      const maxDist = 185;

      for (let j = 0; j < nodes.length; j++) {
        if (j === fromIdx) continue;
        const dx = nodes[fromIdx].x - nodes[j].x;
        const dy = nodes[fromIdx].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < maxDist && dist < bestDist) {
          bestDist = dist;
          bestNeighbor = j;
        }
      }

      if (bestNeighbor !== -1) {
        pulses.push({
          fromIndex: fromIdx,
          toIndex: bestNeighbor,
          progress: 0,
          speed: 0.016 + Math.random() * 0.024,
          color: nodes[fromIdx].color,
        });
      }
    };

    // Draw single frame
    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      const maxConnectDist = 175;

      // 1. Draw rich, dense connecting network edges
      for (let i = 0; i < nodes.length; i++) {
        const ni = nodes[i];
        for (let j = i + 1; j < nodes.length; j++) {
          const nj = nodes[j];
          const dx = ni.x - nj.x;
          const dy = ni.y - nj.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxConnectDist) {
            const alpha = (1 - dist / maxConnectDist) * (isLight ? 0.16 : 0.18);
            ctx.beginPath();
            ctx.moveTo(ni.x, ni.y);
            ctx.lineTo(nj.x, nj.y);
            ctx.strokeStyle = isLight
              ? `rgba(37, 99, 235, ${alpha})`
              : `rgba(56, 189, 248, ${alpha})`;
            ctx.lineWidth = isLight ? 0.75 : 0.75;
            ctx.stroke();
          }
        }
      }

      // 2. Draw light pulses travelling on active edges
      if (!prefersReducedMotion) {
        for (let p = pulses.length - 1; p >= 0; p--) {
          const pulse = pulses[p];
          pulse.progress += pulse.speed;
          if (pulse.progress >= 1) {
            pulses.splice(p, 1);
            continue;
          }

          const from = nodes[pulse.fromIndex];
          const to = nodes[pulse.toIndex];
          if (!from || !to) {
            pulses.splice(p, 1);
            continue;
          }

          const px = from.x + (to.x - from.x) * pulse.progress;
          const py = from.y + (to.y - from.y) * pulse.progress;

          // Pulse glow
          const glowGrad = ctx.createRadialGradient(px, py, 0, px, py, 5);
          glowGrad.addColorStop(0, `${pulse.color}0.95)`);
          glowGrad.addColorStop(0.5, `${pulse.color}0.4)`);
          glowGrad.addColorStop(1, `${pulse.color}0)`);

          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fillStyle = glowGrad;
          ctx.fill();

          // Bright center
          ctx.beginPath();
          ctx.arc(px, py, 1.2, 0, Math.PI * 2);
          ctx.fillStyle = "#ffffff";
          ctx.fill();
        }

        // Randomly spawn new energetic pulses
        if (Math.random() < 0.08) {
          spawnPulse();
        }
      }

      // 3. Draw luminous & sparkling nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];

        if (!prefersReducedMotion) {
          n.x += n.vx;
          n.y += n.vy;

          // Wrap edges with gentle bounce / wrap
          if (n.x < 0) n.x = width;
          else if (n.x > width) n.x = 0;
          if (n.y < 0) n.y = height;
          else if (n.y > height) n.y = 0;

          n.pulsePhase += n.pulseSpeed;
          n.sparklePhase += n.sparkleSpeed;
        }

        const pulseScale = 1 + Math.sin(n.pulsePhase) * 0.18;
        // Non-linear sharp sparkle factor (produces glittering twinkles)
        const sparkleFactor = Math.pow(Math.max(0, Math.sin(n.sparklePhase)), 3.2);

        const currentAlpha = Math.min(
          0.92,
          n.baseAlpha * (0.8 + Math.sin(n.pulsePhase) * 0.25) + sparkleFactor * 0.4
        );

        // Radiant outer aura
        const auraRadius = n.radius * (2.4 + sparkleFactor * 1.8) * pulseScale;
        const radGrad = ctx.createRadialGradient(
          n.x,
          n.y,
          0,
          n.x,
          n.y,
          auraRadius
        );
        radGrad.addColorStop(0, `${n.color}${currentAlpha * 0.5})`);
        radGrad.addColorStop(1, `${n.color}0)`);

        ctx.beginPath();
        ctx.arc(n.x, n.y, auraRadius, 0, Math.PI * 2);
        ctx.fillStyle = radGrad;
        ctx.fill();

        // Luminous circular core (shifts toward bright sparkling white at shimmer peak)
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius + sparkleFactor * 0.5, 0, Math.PI * 2);
        if (sparkleFactor > 0.4) {
          ctx.fillStyle = `rgba(255, 255, 255, ${Math.min(1, currentAlpha + 0.35)})`;
        } else {
          ctx.fillStyle = `${n.color}${currentAlpha})`;
        }
        ctx.fill();
      }
    };

    if (prefersReducedMotion) {
      draw();
      return;
    }

    let isRunning = true;
    const animate = () => {
      if (!isRunning) return;
      draw();
      animationFrameId = requestAnimationFrame(animate);
    };

    animationFrameId = requestAnimationFrame(animate);

    const handleResize = () => {
      setupCanvasSize();
      draw();
    };

    const handleThemeChange = (e: Event) => {
      const custom = e as CustomEvent<string>;
      isLight = custom.detail === "light" || document.documentElement.getAttribute("data-theme") === "light";
      canvas.style.opacity = isLight ? "0.65" : "0.88";
      const palette = getPalette();
      for (let i = 0; i < nodes.length; i++) {
        nodes[i].color = palette[i % palette.length];
      }
      draw();
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("themechange", handleThemeChange);

    return () => {
      isRunning = false;
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("themechange", handleThemeChange);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        zIndex: 0,
        pointerEvents: "none",
        opacity: 0.88,
        transition: "opacity 0.25s ease",
      }}
    />
  );
}
