// Animated hero background: soft, slowly moving fields of blue light, like northern lights (WebGL).
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
      vec2 p = vec2(uv.x * ar, uv.y);
      float t = uTime * 0.05;

      // Domain-warped noise gives large, soft, slowly folding fields of light.
      vec2 q = vec2(fbm(p * 0.55 + vec2(0.0, t)), fbm(p * 0.55 + vec2(5.2, 1.3) - t * 0.8));
      vec2 r = vec2(fbm(p * 0.7 + 1.6 * q + vec2(1.7, 9.2) + t * 0.6),
                    fbm(p * 0.7 + 1.6 * q + vec2(8.3, 2.8) - t * 0.5));
      float f = fbm(p * 0.6 + 2.0 * r);

      // Aurora curtains: noise stretched vertically, swaying sideways over time.
      float sway = 0.35 * sin(t * 1.7 + p.y * 2.0) + 1.2 * r.x;
      float curtain = fbm(vec2(p.x * 1.6 + sway + t * 0.9, p.y * 0.35 - t * 0.35));
      curtain = smoothstep(0.48, 0.9, curtain);
      // The curtains live in a soft band that drifts up and down.
      float band = exp(-pow((uv.y - 0.58 - 0.18 * (q.y - 0.5)) * 2.1, 2.0));

      // The site's blues: deep navy blue, logo blue, a cooler cyan-blue and pale ice.
      vec3 deep = vec3(0.05, 0.11, 0.32);
      vec3 blue = vec3(0.20, 0.38, 0.86);
      vec3 cyan = vec3(0.13, 0.60, 0.82);
      vec3 ice = vec3(0.70, 0.79, 1.00);
      vec3 col = mix(deep, blue, smoothstep(0.25, 0.75, f));
      col = mix(col, cyan, smoothstep(0.45, 0.80, r.y) * 0.85);
      col = mix(col, ice, smoothstep(0.62, 0.95, r.x) * 0.55);

      vec3 o = vec3(0.016, 0.035, 0.095);
      o += col * pow(smoothstep(0.28, 0.92, f), 1.15) * 0.95;  // the large soft glow
      o += mix(col, ice, 0.25) * curtain * band * 0.75;      // the moving curtains

      // Keep the edges calm and dark so the centred text stays readable.
      float vig = smoothstep(1.3, 0.15, length(vec2((uv.x - 0.5) * 1.2, (uv.y - 0.6) * 1.1)));
      o *= mix(0.4, 1.0, vig);
      // A calmer zone right behind the headline keeps the text crisp.
      o *= 1.0 - 0.2 * exp(-pow(length(vec2((uv.x - 0.5) * 1.6, (uv.y - 0.6) * 2.4)), 2.0) * 2.5);
      o += (hash(gl_FragCoord.xy + fract(uTime) * 91.0) - 0.5) * 0.025;
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
    const scale = Math.min(window.devicePixelRatio || 1, 1.5) * 0.4;
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
