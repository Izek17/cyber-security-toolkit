const express = require("express");
const cors = require("cors");
const axios = require("axios");

const app = express();
const PORT = 8000;

app.use(cors());

app.get("/api/health", async (req, res) => {
  try {
    const flaskResponse = await axios.get("http://localhost:5000/health");
    res.json({
      gateway: "Express is alive!",
      flaskService: flaskResponse.data
    });
  } catch (error) {
    res.status(500).json({ error: "Could not reach Flask service" });
  }
});

app.listen(PORT, () => {
  console.log(`Express Gateway running on http://localhost:${PORT}`);
});