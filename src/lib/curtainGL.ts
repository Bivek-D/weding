/**
 * The dokhona curtains, drawn live on the GPU.
 *
 * A per-pixel port of design/build/art_bodo2.py → curtain_frames(): the flat cloth (exported by
 * design/build/curtain_tex.py) is gathered toward the outer edges as the curtains zip open (middle
 * rows first), folded, given a rolled hem, tied back with an emerald aronai, lit from the top left, and
 * casts a soft shadow on the stage. Because it is computed for every frame instead of blending 36
 * pre-rendered images, the motion is continuous at the display's own frame rate, and the whole thing is
 * a 7 KB texture instead of 4.4 MB of frames.
 */

const VERT = `
attribute vec2 p;
void main() { gl_Position = vec4(p, 0.0, 1.0); }
`;

const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform sampler2D cloth;   // RGB colour, A = thread height / 2  (480 x 1388)
uniform sampler2D tie;     // emerald aronai tie-back (192 x 38)
uniform vec2 res;          // canvas size, px
uniform float t;           // 0 closed .. 1 open
uniform vec4 fit;          // x0, y0, scale (canvas px per curtain px), unused

const float W = 640.0;
const float H = 1388.0;
const float HALF = 320.0;
const float WC = 480.0;
const float YT = 832.0;           // int(H * .6): tie-back height
const float TIE_H = 38.0;
const float TIE_W = 192.0;
const float PI = 3.14159265;

float sstep(float s) { return s * s * (3.0 - 2.0 * s); }

// inner edge x of the LEFT curtain for row y
float edgeAt(float y) {
  float eo = y < YT
    ? 0.10 + 0.2 * pow(cos(PI * 0.5 * clamp(y / YT, 0.0, 1.0)), 1.3)
    : 0.10 + 0.09 * pow(clamp((y - YT) / (H - YT), 0.0, 1.0), 0.75);
  eo *= W;
  float s = sstep(clamp((t - abs(y / H - 0.48) * 0.55) / 0.6, 0.0, 1.0));
  return HALF + 6.0 + (eo - HALF - 6.0) * s;
}

float tieK() { return clamp((t - 0.8) / 0.2, 0.0, 1.0); }

// anti-aliasing: where the gathered folds get finer than the screen can show, flatten them smoothly
// (no moiré). dph/dx of the fold phase, measured in screen pixels.
float foldFade(float u, float E) {
  float dphdx = 2.0 * PI * 10.0 * 0.92 * pow(max(u, 0.02), -0.08) / E;
  float perPx = dphdx / fit.z;               // radians per screen pixel
  return 1.0 - smoothstep(0.9, 1.9, perPx);  // full folds below ~7 px period, gone at ~3 px
}

// height of the left curtain at (x, y), x in 0..HALF
float heightAt(float x, float y) {
  float E = edgeAt(y);
  float u = clamp(x / E, 0.0, 1.0);
  float th = texture2D(cloth, vec2((u * (WC - 1.0) + 0.5) / WC, (y + 0.5) / H)).a * 2.0;
  float squeeze = clamp(1.0 - E / HALF, 0.0, 1.0);
  float ph = 2.0 * PI * 10.0 * pow(u, 0.92) + y / 260.0 * (1.0 - squeeze);
  float h = cos(ph) * foldFade(u, E) * (3.0 + 17.0 * squeeze) + th * 2.0;
  float dpx = E - x;
  if (x < E) h += 7.0 * exp(-(dpx / 7.0) * (dpx / 7.0));
  float k = tieK();
  float r = y - (YT - floor(TIE_H / 2.0));
  float et = floor(edgeAt(YT));
  if (k > 0.0 && r >= 0.0 && r < TIE_H && x < et + 6.0) h += 6.0 * k * sin(PI * r / (TIE_H - 1.0));
  return h;
}

// either curtain, mirrored: the right one is the left one flipped about the centre
float heightStage(float x, float y) {
  return x < HALF ? heightAt(x, y) : heightAt(W - 1.0 - x, y);
}

// smooth 0..1 approximation of a gaussian-blurred step (normal CDF)
float cdf(float z) { return 1.0 / (1.0 + exp(-1.702 * z)); }

// blurred coverage of both curtains at (x, y) with blur sigma
float cover(float x, float y, float sigma) {
  float E = edgeAt(clamp(y, 0.0, H - 1.0));
  float l = cdf((E - x) / sigma);
  float r = cdf((x - (W - 1.0 - E)) / sigma);
  return max(l, r);
}

void main() {
  // canvas px (top-left origin) -> curtain px
  vec2 c = vec2(gl_FragCoord.x, res.y - gl_FragCoord.y);
  vec2 q = (c - fit.xy) / fit.z;
  float x = q.x, y = clamp(q.y, 0.0, H - 1.0);

  bool right = x >= HALF;
  float xl = right ? W - 1.0 - x : x;
  float E = edgeAt(y);
  float inside = xl < E ? 1.0 : 0.0;

  // colour and ambient occlusion
  float u = clamp(xl / E, 0.0, 1.0);
  vec3 col = texture2D(cloth, vec2((u * (WC - 1.0) + 0.5) / WC, (y + 0.5) / H)).rgb;
  float squeeze = clamp(1.0 - E / HALF, 0.0, 1.0);
  float ph = 2.0 * PI * 10.0 * pow(u, 0.92) + y / 260.0 * (1.0 - squeeze);
  float dpx = E - xl;
  float ao = 1.0 - (0.12 + 0.34 * squeeze) * (0.5 - 0.5 * cos(ph) * foldFade(u, E));
  ao *= 1.0 - 0.35 * exp(-((dpx - 2.0) / 2.5) * ((dpx - 2.0) / 2.5)) * inside;
  ao *= 1.0 - 0.25 * exp(-y / (H * 0.07));
  float a = smoothstep(-0.9, 0.9, dpx);   // the soft cut of gaussian(Af, .7)

  // the aronai tie-back fades in at the end
  float k = tieK();
  float r = y - (YT - floor(TIE_H / 2.0));
  float et = floor(edgeAt(YT));
  if (k > 0.0 && r >= 0.0 && r < TIE_H && xl < et + 6.0) {
    vec3 tc = texture2D(tie, vec2((min(xl, TIE_W - 1.0) + 0.5) / TIE_W, (r + 0.5) / TIE_H)).rgb;
    col = mix(col, tc, k);
    ao = mix(ao, 1.0, k);
    a = max(a, k);
  }

  // light from the top left (art_bodo2.light with k = .8, spec = .28, amb = .52)
  float st = max(1.2, 1.0 / fit.z);          // at least one screen pixel
  float gx = (heightStage(x + st, y) - heightStage(x - st, y)) / (2.0 * st);
  float gy = (heightStage(x, y + st) - heightStage(x, y - st)) / (2.0 * st);
  vec3 n = vec3(-gx * 0.8, -gy * 0.8, 1.0);
  vec3 L = normalize(vec3(-1.0, -1.0, 1.5));
  float d = dot(n, L) / length(n);
  float mul = 0.52 + 0.48 * d / L.z;
  float hl = pow(max(d - L.z, 0.0), 1.5) * 0.28 * 6.0;
  vec3 lit = col * mul * ao + hl;

  // the curtains' shadow on the stage behind: cast down and right, plus a contact shadow
  float castSh = cover(x - 20.0, y - 14.0, 16.0) * 0.5;
  float contact = cover(x, y, 6.0) * 0.3;
  float sa = clamp(max(castSh, contact), 0.0, 1.0) * (1.0 - a);

  // premultiplied output (the canvas composites premultiplied)
  vec3 shade = vec3(0.165, 0.086, 0.031);
  gl_FragColor = vec4(lit * a + shade * sa, a + sa);
}
`;

export type Curtain = { draw: (t: number) => void; resize: () => void; ready: Promise<void>; dispose: () => void };

async function bitmap(src: string) {
  const blob = await fetch(src).then((r) => r.blob());
  // keep the raw RGB under the alpha (the alpha channel carries height, not transparency)
  return createImageBitmap(blob, { premultiplyAlpha: "none", colorSpaceConversion: "none" });
}

/** Returns null when WebGL isn't available, so the caller can fall back to the pre-rendered frames. */
export function createCurtain(canvas: HTMLCanvasElement): Curtain | null {
  const gl = canvas.getContext("webgl", { premultipliedAlpha: true, alpha: true, antialias: false, powerPreference: "high-performance" });
  if (!gl) return null;

  const sh = (type: number, src: string) => {
    const s = gl.createShader(type)!;
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s) || "shader");
    return s;
  };
  let prog: WebGLProgram;
  try {
    prog = gl.createProgram()!;
    gl.attachShader(prog, sh(gl.VERTEX_SHADER, VERT));
    gl.attachShader(prog, sh(gl.FRAGMENT_SHADER, FRAG));
    gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog) || "link");
  } catch (e) {
    console.warn("curtain: WebGL shader failed, using frames", e);
    return null;
  }
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, "p");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  const U = (n: string) => gl.getUniformLocation(prog, n);
  const uRes = U("res"), uT = U("t"), uFit = U("fit");
  gl.uniform1i(U("cloth"), 0);
  gl.uniform1i(U("tie"), 1);

  const tex = (unit: number, img: ImageBitmap) => {
    const tx = gl.createTexture();
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, tx);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.pixelStorei(gl.UNPACK_COLORSPACE_CONVERSION_WEBGL, gl.NONE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    // non-power-of-two sizes: clamp, no mipmaps
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    return tx;
  };

  let loaded = false;
  let last = 0;
  const textures: WebGLTexture[] = [];

  const draw = (t: number) => {
    last = t;
    if (!loaded) return;
    const w = canvas.width, h = canvas.height;
    // cover-fit the 640 x 1388 curtain into the canvas, centred (same as the old frame drawing)
    const k = Math.max(w / 640, h / 1388);
    gl.viewport(0, 0, w, h);
    gl.uniform2f(uRes, w, h);
    gl.uniform1f(uT, Math.min(1, Math.max(0, t)));
    gl.uniform4f(uFit, (w - 640 * k) / 2, (h - 1388 * k) / 2, k, 0);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };

  const ready = Promise.all([bitmap("/art/curtain-gl/cloth.webp"), bitmap("/art/curtain-gl/tie.webp")]).then(([c, ti]) => {
    textures.push(tex(0, c)!, tex(1, ti)!);
    c.close();
    ti.close();
    loaded = true;
    draw(last);
  });

  return {
    draw,
    ready,
    resize: () => draw(last),
    dispose: () => {
      textures.forEach((x) => gl.deleteTexture(x));
      gl.deleteProgram(prog);
      gl.getExtension("WEBGL_lose_context")?.loseContext();
    },
  };
}
