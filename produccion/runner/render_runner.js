// Renderiza escena.html cuadro por cuadro (Chromium sin pantalla + WebGL por software) y lo pasa a ffmpeg.
// Uso: node render_runner.js config.json salida_mudo.mp4 [--muestra seg1,seg2,...]
const http = require("http"), fs = require("fs"), path = require("path"), { spawn } = require("child_process");
const { chromium } = require("playwright");

const RAIZ = path.resolve(__dirname, "..");            // sirve produccion/ (escena, node_modules, assets, fotos)
const TIPOS = { ".html": "text/html", ".js": "text/javascript", ".ttf": "font/ttf", ".jpg": "image/jpeg", ".png": "image/png", ".json": "application/json" };

(async () => {
  const [cfgPath, salida, ...resto] = process.argv.slice(2);
  const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
  const muestra = resto[0] === "--muestra" ? resto[1].split(",").map(Number) : null;
  const srv = http.createServer((req, res) => {
    const f = path.join(RAIZ, decodeURIComponent(req.url.split("?")[0]));
    if (!f.startsWith(RAIZ) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { "Content-Type": TIPOS[path.extname(f)] || "application/octet-stream" }); fs.createReadStream(f).pipe(res);
  }).listen(0);
  const puerto = srv.address().port;
  const nav = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const pag = await nav.newPage({ viewport: { width: 1080, height: 1920 } });
  pag.on("pageerror", e => console.error("error en la página:", e.message));
  await pag.goto(`http://127.0.0.1:${puerto}/runner/escena.html`);
  await pag.waitForFunction(() => window.iniciar);
  await pag.evaluate(c => window.iniciar(c), cfg);
  if (muestra) {                                        // cuadros sueltos para revisar (renderiza todo el tramo para que la estela sea real)
    let k = 0;
    for (let f = 0; f <= Math.round(Math.max(...muestra) * cfg.fps); f++) {
      const url = await pag.evaluate(t => window.frame(t), f / cfg.fps);
      if (muestra.some(s => Math.round(s * cfg.fps) === f)) fs.writeFileSync(`${salida}_${k++}.jpg`, Buffer.from(url.split(",")[1], "base64"));
    }
  } else {
    const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(cfg.fps), "-c:v", "mjpeg", "-i", "-",
      "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", salida], { stdio: ["pipe", "inherit", "inherit"] });
    const nf = Math.round(cfg.duracion * cfg.fps), t0 = Date.now();
    for (let f = 0; f < nf; f++) {
      const url = await pag.evaluate(t => window.frame(t), f / cfg.fps);
      if (!ff.stdin.write(Buffer.from(url.split(",")[1], "base64"))) await new Promise(r => ff.stdin.once("drain", r));
      if (f % 300 === 0) console.log(`cuadro ${f}/${nf} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
    }
    ff.stdin.end(); await new Promise(r => ff.on("close", r));
  }
  await nav.close(); srv.close();
})();
