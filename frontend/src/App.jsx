import { useState } from "react";

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const testConnection = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/health");
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: "Could not reach Express Gateway" });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center gap-6">
      <h1 className="text-3xl font-bold">Cyber Security Toolkit</h1>
      <p className="text-slate-400">Hello Chain Test: React → Express → Flask</p>

      <button
        onClick={testConnection}
        className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold"
      >
        {loading ? "Testing..." : "Test Connection"}
      </button>

      {result && (
        <pre className="bg-slate-800 p-4 rounded-lg text-sm max-w-md overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;