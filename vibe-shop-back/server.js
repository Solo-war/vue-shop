const express = require("express");
const cors = require("cors");
const path = require("path");
const fs = require("fs");

// Prefer tees (t-shirts) from static dataset with Unsplash sources
function buildProductsFromStaticTees() {
  try {
    const staticPath = path.join(__dirname, "backend", "static", "products.json");
    if (!fs.existsSync(staticPath)) return null;
    const raw = fs.readFileSync(staticPath, "utf8");
    const arr = JSON.parse(raw);
    if (!Array.isArray(arr) || !arr.length) return null;

    // Each item may have a single Unsplash URL; expand to 5 images per product
    const products = arr.map((it, idx) => {
      const base = String((it.images && it.images[0]) || it.image || "");
      const hasQuery = /\?/.test(base);
      const paramJoin = hasQuery ? "&" : "?";
      const images = Array.from({ length: 5 }, (_, i) => `${base}${paramJoin}sig=${i + 1}`);
      return {
        id: it.id ?? idx + 1,
        slug: it.slug || undefined,
        name: it.name ?? it.title ?? `VIBE Tee ${idx + 1}`,
        price: Number(it.price ?? 0),
        description: it.description ?? "",
        image: images[0],
        images,
      };
    });
    return products;
  } catch (e) {
    console.error("Failed to build products from static tees:", e);
    return null;
  }
}

// Try to build products dynamically from backend images (fallback to frontend)
function buildProductsFromImages() {
  const backImagesDir = path.join(
    __dirname,
    "backend",
    "public",
    "images",
    "tees",
    "images"
  );
  const frontImagesDir = path.join(
    __dirname,
    "..",
    "vibe-shop-front",
    "public",
    "images",
    "tees",
    "images"
  );

  try {
    const scan = fs.existsSync(backImagesDir) ? backImagesDir : frontImagesDir;
    if (!fs.existsSync(scan)) return null;

    const files = fs
      .readdirSync(scan)
      .filter((f) => /\.jpe?g$/i.test(f));

    // Group by numeric key before underscore, collect index after underscore
    const groups = new Map();
    for (const name of files) {
      const m = name.match(/^(\d+)_([0-9]+)\.[^.]+$/);
      if (!m) continue;
      const key = m[1];
      const idx = Number(m[2]);
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push({ idx, name });
    }

    // Create products for groups that have at least 5 images
    const keys = Array.from(groups.keys()).sort((a, b) => Number(a) - Number(b));
    const products = [];
    let seq = 1;
    for (const key of keys) {
      const all = groups
        .get(key)
        .sort((a, b) => a.idx - b.idx);

      // Heuristic: treat index 6 (or filenames containing chart/size keywords) as size-chart
      const isChart = (n) => n.idx === 6
        || /(chart|size|sizing|dimension|guide|table|таблиц|размер)/i.test(n.name || '');
      const chart = all.find(isChart) || null;
      const nonChart = all.filter((x) => x !== chart && x.idx >= 1);
      const take = chart ? 4 : 5; // keep total at 5
      const picked = nonChart.filter((x) => x.idx >= 1).slice(0, take);
      if (chart) picked.push(chart);
      if (picked.length < 5) continue; // enforce 5 photos per product
      const images = picked.map((x) => `/images/tees/images/${x.name}`);
      const name = `Футболка ${key}`;
      const slug = `tee-${key}`;
      const price = 2990 + ((seq - 1) % 10) * 100; // simple varied pricing
      products.push({
        id: seq,
        slug,
        name,
        price,
        description: "Футболка премиум качества. 100% хлопок.",
        image: images[0],
        images,
      });
      seq++;
    }

    return products;
  } catch (e) {
    console.error("Failed to build products from images:", e);
    return null;
  }
}

const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/products", (req, res) => {
  // Prefer static tees with t-shirt photos
  const fromStatic = buildProductsFromStaticTees();
  if (Array.isArray(fromStatic) && fromStatic.length) return res.json(fromStatic);

  // Fallback to legacy dynamic images grouping if static tees unavailable
  const generated = buildProductsFromImages();
  if (Array.isArray(generated) && generated.length) return res.json(generated);

  // Final fallback: old sample data
  const fallback = require("./data/products.json");
  return res.json(fallback);
});

app.get("/api/products/:id", (req, res) => {
  // Keep ordering consistent with the list source used above
  const fromStatic = buildProductsFromStaticTees();
  let list = null;
  if (Array.isArray(fromStatic) && fromStatic.length) {
    list = fromStatic;
  } else {
    const generated = buildProductsFromImages();
    list = Array.isArray(generated) && generated.length
      ? generated
      : require("./data/products.json");
  }
  const id = String(req.params.id).toLowerCase();
  const p = list.find(
    (x) => String(x.id) === id || String(x.slug || "").toLowerCase() === id
  );
  if (!p) return res.status(404).json({ error: "Not found" });
  res.json(p);
});

// Serve images: prefer backend public/images, then fallback to frontend
app.use(
  "/images",
  express.static(path.join(__dirname, "backend", "public", "images"))
);
app.use(
  "/images",
  express.static(
    path.join(__dirname, "..", "vibe-shop-front", "public", "images")
  )
);

// Fallback proxy: forward unknown /api/* routes to FastAPI (127.0.0.1:8000)
// This lets the frontend hit admin/auth/reviews endpoints even when served via this Node server.
app.use(async (req, res, next) => {
  try {
    if (!req.url.startsWith('/api/')) return next();
    // Let our local product handlers work; proxy everything else
    if (req.method === 'GET' && (req.path === '/api/products' || /^\/api\/products\//.test(req.path))) {
      return next();
    }
    const targetHost = '127.0.0.1';
    const targetPort = 8000;
    const isTLS = false;
    const http = require(isTLS ? 'https' : 'http');
    const url = require('url');
    const outPath = req.url.replace(/^\/api/, '');
    const opts = {
      host: targetHost,
      port: targetPort,
      method: req.method,
      path: outPath,
      headers: { ...req.headers, host: `${targetHost}:${targetPort}` },
    };

    const proxyReq = http.request(opts, (proxyRes) => {
      res.status(proxyRes.statusCode || 502);
      Object.entries(proxyRes.headers || {}).forEach(([k, v]) => {
        if (typeof v !== 'undefined') res.setHeader(k, v);
      });
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (err) => {
      console.error('Proxy error:', err);
      if (!res.headersSent) res.status(502).json({ detail: 'Bad Gateway' });
    });
    if (req.readable) {
      req.pipe(proxyReq);
    } else {
      proxyReq.end();
    }
  } catch (e) {
    console.error('Proxy fallback failed:', e);
    next();
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () =>
  console.log(`API listening on http://localhost:${port}`)
);
