// Animated hero background: a dark horizon with a glowing atmosphere (WebGL).
// Renders at a reduced resolution, pauses when off screen or in a background tab,
// and draws a single still frame when the visitor prefers reduced motion.
(() => {
  const canvas = document.querySelector('[data-hero-glow]');
  if (!canvas) return;
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const gl = canvas.getContext('webgl', { antialias: false, alpha: false, depth: false, stencil: false, powerPreference: 'low-power' });
  if (!gl) { canvas.classList.add('is-fallback'); return; }

  const vertex = 'attribute vec2 p; void main() { gl_Position = vec4(p, 0.0, 1.0); }';
  const fragment = `
    precision highp float;
    uniform vec2 uRes;
    uniform float uTime;

    float hash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
    float noise(vec2 p) {
      vec2 i = floor(p), f = fract(p);
      vec2 u = f * f * (3.0 - 2.0 * f);
      return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x),
                 mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
    }
    float fbm(vec2 p) {
      float v = 0.0, a = 0.5;
      for (int k = 0; k < 5; k++) { v += a * noise(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; }
      return v;
    }

    void main() {
      vec2 uv = gl_FragCoord.xy / uRes;
      float ar = uRes.x / uRes.y;
      vec2 p = vec2((uv.x - 0.5) * ar, uv.y);
      float t = uTime * 0.04;

      // A large "planet" sits below the fold; its rim forms the horizon.
      float R = 2.2;
      vec2 c = vec2(0.0, 0.085 - R);
      float d = length(p - c) - R;

      // Slow noise makes the light breathe and the rim waver slightly.
      float w = fbm(vec2(p.x * 1.2 + t, uv.y * 1.6 - t * 0.7));
      float rim = exp(-abs(d - 0.018 * (w - 0.5)) * 34.0);
      float halo = exp(-max(d, 0.0) * 4.2) * smoothstep(-0.01, 0.02, d);
      float haze = exp(-max(d, 0.0) * 1.6) * smoothstep(-0.01, 0.02, d);
      float inner = exp(d * 9.0) * (1.0 - smoothstep(-0.01, 0.0, d));

      // Colour across the horizon: deep blue, violet, then a warm edge, drifting slowly.
      float k = p.x / ar + 0.5 + 0.16 * sin(t * 2.0 + p.x * 1.1) + 0.22 * (w - 0.5);
      // The logo's blues: deep navy blue, brighter blue and a pale ice blue.
      vec3 deep = vec3(0.11, 0.24, 0.62);
      vec3 blue = vec3(0.25, 0.44, 0.91);
      vec3 ice = vec3(0.62, 0.71, 1.00);
      vec3 col = mix(deep, blue, smoothstep(0.15, 0.55, k));
      col = mix(col, ice, smoothstep(0.55, 0.95, k) * 0.85);

      // Ribbons of light flowing through the atmosphere.
      float rib = fbm(vec2(p.x * 1.8 - t * 1.4, d * 7.0 + t * 0.8));
      rib = smoothstep(0.25, 0.85, rib);

      vec3 o = vec3(0.020, 0.043, 0.110);
      o += col * halo * (0.35 + 0.9 * rib) * 1.0;
      o += col * haze * 0.07;
      o += mix(col, vec3(1.0), 0.5) * rim * 1.3;
      o += col * inner * 0.28;

      // Faint aura in the upper corners so the top is not flat black.
      o += vec3(0.11, 0.24, 0.62) * 0.16 * exp(-length(p - vec2(-0.55 * ar, 1.05)) * 2.0);
      o += vec3(0.25, 0.44, 0.91) * 0.08 * exp(-length(p - vec2(0.60 * ar, 1.10)) * 2.4);

      // Vignette and a touch of film grain.
      o *= mix(0.6, 1.0, smoothstep(1.35, 0.25, length(vec2(p.x / ar * 1.2, uv.y - 0.35))));
      o += (hash(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) * 0.03;
      gl_FragColor = vec4(o, 1.0);
    }`;

  const compile = (type, src) => {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  };
  const vs = compile(gl.VERTEX_SHADER, vertex);
  const fs = compile(gl.FRAGMENT_SHADER, fragment);
  if (!vs || !fs) { canvas.classList.add('is-fallback'); return; }
  const prog = gl.createProgram();
  gl.attachShader(prog, vs);
  gl.attachShader(prog, fs);
  gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { canvas.classList.add('is-fallback'); return; }
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
  const uRes = gl.getUniformLocation(prog, 'uRes');
  const uTime = gl.getUniformLocation(prog, 'uTime');

  // Soft light needs no high resolution: render small and let CSS scale it up.
  const resize = () => {
    const scale = Math.min(window.devicePixelRatio || 1, 1.5) * 0.55;
    const w = Math.max(1, Math.round(canvas.clientWidth * scale));
    const h = Math.max(1, Math.round(canvas.clientHeight * scale));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w; canvas.height = h;
      gl.viewport(0, 0, w, h);
    }
    gl.uniform2f(uRes, w, h);
  };

  const start = performance.now() - 18000; // start mid-motion, not from a cold frame
  let raf = 0;
  let visible = true;
  const draw = (now) => {
    resize();
    gl.uniform1f(uTime, (now - start) / 1000);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    canvas.classList.add('is-ready');
  };
  const loop = (now) => { draw(now); raf = requestAnimationFrame(loop); };
  const run = () => {
    cancelAnimationFrame(raf);
    if (reduce) { draw(performance.now()); return; }
    if (visible && !document.hidden) raf = requestAnimationFrame(loop);
  };

  new IntersectionObserver(([e]) => { visible = e.isIntersecting; run(); }).observe(canvas);
  document.addEventListener('visibilitychange', run);
  window.addEventListener('resize', () => { if (reduce) draw(performance.now()); });
  run();
})();
