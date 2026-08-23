const express = require("express");
const cors = require("cors");
const axios = require("axios");

const app = express();
const PORT = 8000;

app.use(cors());
app.use(express.json());

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

app.post("/api/network/ping-sweep", async (req, res) => {
  const { start_ip, end_ip, timeout } = req.body || {};

  // Basic validation at the gateway level, before even calling Flask.
  // This is a first line of defense — Flask still validates independently too.
  if (!start_ip || !end_ip) {
    return res.status(400).json({
      success: false,
      error: {
        code: "INVALID_INPUT",
        message: "start_ip and end_ip are required."
      }
    });
  }

  if (timeout === undefined || typeof timeout !== "number") {
    return res.status(400).json({
      success: false,
      error: {
        code: "INVALID_INPUT",
        message: "timeout is required and must be a number."
      }
    });
  }

  try {
    const flaskResponse = await axios.post(
      "http://localhost:5000/ping-sweep",
      { start_ip, end_ip, timeout },
      { timeout: 10000 } // 10 second cap so Express never hangs forever waiting on Flask
    );

    // Flask already returns a clean { success, data } or { success, error } shape.
    // We just relay it as-is, with the same HTTP status Flask gave us.
    res.status(flaskResponse.status).json(flaskResponse.data);

  } catch (error) {
    if (error.response) {
      // Flask responded, but with an error status (e.g. 400 from bad input)
      res.status(error.response.status).json(error.response.data);

    } else if (error.code === "ECONNREFUSED" || error.code === "ECONNABORTED") {
      // Flask service is down or took too long to respond
      res.status(503).json({
        success: false,
        error: {
          code: "SERVICE_UNAVAILABLE",
          message: "Network scanning service is currently unavailable. Please try again."
        }
      });

    } else {
      // Any other unexpected error — never leak internal details to the client
      res.status(500).json({
        success: false,
        error: {
          code: "INTERNAL_ERROR",
          message: "An unexpected error occurred."
        }
      });
    }
  }
});

app.listen(PORT, () => {
  console.log(`Express Gateway running on http://localhost:${PORT}`);
});