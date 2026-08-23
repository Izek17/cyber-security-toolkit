import { useState } from "react";

function PingSweeper() {
  const [startIp, setStartIp] = useState("127.0.0.1");
  const [endIp, setEndIp] = useState("127.0.0.5");
  const [timeout, setTimeout] = useState(1);

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleScan = async () => {
        setError(null);
    setResults(null);

    // Client-side validation — stops the request before it ever
    // reaches Express, if required fields are empty.
    if (!startIp.trim() || !endIp.trim() || timeout === "") {
      setError("Start IP, End IP, and Timeout are all required.");
      return;
    }

    setLoading(true);


    try {
      const response = await fetch("http://localhost:8000/api/network/ping-sweep", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_ip: startIp,
          end_ip: endIp,
          timeout: Number(timeout),
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        // Server responded, but with an error (400 or 503).
        // data.error.message comes from our Express/Flask error structure.
        setError(data.error?.message || "Something went wrong.");
      } else {
        setResults(data.data.results);
      }
    } catch (err) {
      // This branch runs if Express itself is unreachable
      // (e.g. Express server isn't running at all).
      setError("Could not reach the Express Gateway. Is it running?");
    }

    setLoading(false);
  };

  return (
    <div className="bg-slate-800 p-6 rounded-lg max-w-2xl w-full text-white">
      <h2 className="text-xl font-bold mb-2">Network Scanner — Ping Sweeper</h2>

      <div className="bg-yellow-900 border border-yellow-600 text-yellow-200 text-sm p-3 rounded mb-4">
        ⚠️ Only scan hosts you own or have explicit permission to test
        (e.g. localhost or your own lab network).
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Start IP</label>
          <input
            className="w-full px-3 py-2 rounded bg-slate-700 text-white"
            value={startIp}
            onChange={(e) => setStartIp(e.target.value)}
            placeholder="127.0.0.1"
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">End IP</label>
          <input
            className="w-full px-3 py-2 rounded bg-slate-700 text-white"
            value={endIp}
            onChange={(e) => setEndIp(e.target.value)}
            placeholder="127.0.0.5"
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Timeout (s)</label>
          <input
            type="number"
            step="0.5"
            className="w-full px-3 py-2 rounded bg-slate-700 text-white"
            value={timeout}
            onChange={(e) => setTimeout(e.target.value)}
          />
        </div>
      </div>

      <button
        onClick={handleScan}
        disabled={loading}
        className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:cursor-not-allowed px-6 py-2 rounded-lg font-semibold mb-4"
      >
        {loading ? "Scanning..." : "Scan"}
      </button>

      {error && (
        <div className="bg-red-900 border border-red-600 text-red-200 text-sm p-3 rounded mb-4">
          {error}
        </div>
      )}

      {results && (
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-600 text-slate-400">
              <th className="py-2 pr-4">IP Address</th>
              <th className="py-2 pr-4">Status</th>
              <th className="py-2 pr-4">Response Time</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.ip} className="border-b border-slate-700">
                <td className="py-2 pr-4">{r.ip}</td>
                <td className="py-2 pr-4">
                  <span
                    className={
                      r.status === "reachable"
                        ? "text-green-400"
                        : "text-slate-500"
                    }
                  >
                    {r.status}
                  </span>
                </td>
                <td className="py-2 pr-4">
                  {r.response_time !== null ? `${r.response_time} ms` : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default PingSweeper;