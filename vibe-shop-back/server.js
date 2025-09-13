const express = require("express");
const cors = require("cors");
const path = require("path");
const products = require("./data/products.json");

const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/products", (req, res) => res.json(products));
app.get("/api/products/:id", (req, res) => {
  const p = products.find((x) => String(x.id) === String(req.params.id));
  if (!p) return res.status(404).json({ error: "Not found" });
  res.json(p);
});

// serve static images from /public/images if present
app.use("/images", express.static(path.join(__dirname, "public", "images")));

const port = process.env.PORT || 3000;
app.listen(port, () =>
  console.log(`API listening on http://localhost:${port}`)
);
