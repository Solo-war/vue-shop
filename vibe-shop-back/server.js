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

    // Each item may have a single Unsplash URL; expand to 6 images per product
    const products = arr.map((it, idx) => {
      const base = String((it.images && it.images[0]) || it.image || "");
      const hasQuery = /\?/.test(base);
      const paramJoin = hasQuery ? "&" : "?";
      const images = Array.from({ length: 6 }, (_, i) => `${base}${paramJoin}sig=${i + 1}`);
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

    // Create products for groups that have at least 6 images
    const keys = Array.from(groups.keys()).sort((a, b) => Number(a) - Number(b));
    const products = [];
    let seq = 1;
    for (const key of keys) {
      const arr = groups
        .get(key)
        .sort((a, b) => a.idx - b.idx)
        .filter((x) => x.idx >= 1 && x.idx <= 6)
        .slice(0, 6);
      if (arr.length < 6) continue; // enforce 6 photos per product
      const images = arr.map((x) => `/images/tees/images/${x.name}`);
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

const port = process.env.PORT || 3000;
app.listen(port, () =>
  console.log(`API listening on http://localhost:${port}`)
);
