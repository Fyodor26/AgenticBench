import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { benchmarkAPI } from "../api/benchmark";
import { PlayCircle, Loader2, Bot } from "lucide-react";

const providers = [
  { id: "ollama", name: "Ollama" },
  { id: "gemini", name: "Gemini" },
  { id: "openai", name: "OpenAI" },
  { id: "anthropic", name: "Anthropic" },
];

const Benchmark: React.FC = () => {
  const navigate = useNavigate();

  const [taskName, setTaskName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [expectedOutput, setExpectedOutput] = useState("");

  const [selectedProviders, setSelectedProviders] = useState<string[]>([
    "ollama",
  ]);

  const [running, setRunning] = useState(false);

  const toggleProvider = (provider: string) => {
    if (selectedProviders.includes(provider)) {
      setSelectedProviders(
        selectedProviders.filter((p) => p !== provider)
      );
    } else {
      setSelectedProviders([...selectedProviders, provider]);
    }
  };

  const handleRunBenchmark = async () => {
  if (!taskName || !prompt || selectedProviders.length === 0) {
    alert("Please fill all required fields.");
    return;
  }

  try {
    setRunning(true);

    // The backend runs synchronously and scores every selected provider
    // before responding (see BenchmarkService.run), so we navigate
    // straight to the results page rather than polling a "Queued" /
    // "Running" state that nothing on the backend ever produces.
    const response = await benchmarkAPI.runBenchmark({
      task_name: taskName,
      prompt,
      expected_output: expectedOutput,
      providers: selectedProviders,
    });

    navigate(`/results/${response.data.benchmark_id}`);
  } catch (err: any) {
    console.error(err);
    const detail = err.response?.data?.detail;
    alert(Array.isArray(detail) ? detail[0]?.msg : detail || "Benchmark failed.");
  } finally {
    setRunning(false);
  }
};

  return (
    <div className="space-y-8">

      <div>

        <h1 className="text-3xl font-bold">
          Create Benchmark
        </h1>

        <p className="text-slate-500 mt-1">
          Run the same prompt across multiple AI providers.
        </p>

      </div>

      <div className="bg-white rounded-2xl shadow border p-8 space-y-6">

        <div>

          <label className="block font-medium mb-2">
            Benchmark Name
          </label>

          <input
            value={taskName}
            onChange={(e) => setTaskName(e.target.value)}
            placeholder="Summarization Benchmark"
            className="w-full border rounded-xl p-3"
          />

        </div>

        <div>

          <label className="block font-medium mb-2">
            Prompt
          </label>

          <textarea
            rows={7}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter the prompt..."
            className="w-full border rounded-xl p-3"
          />

        </div>

        <div>

          <label className="block font-medium mb-2">
            Expected Output
          </label>

          <textarea
            rows={4}
            value={expectedOutput}
            onChange={(e) =>
              setExpectedOutput(e.target.value)
            }
            placeholder="Optional..."
            className="w-full border rounded-xl p-3"
          />

        </div>

        <div>

          <label className="block font-medium mb-4">
            Select Providers
          </label>

          <div className="grid md:grid-cols-2 gap-4">

            {providers.map((provider) => (

              <button
                key={provider.id}
                type="button"
                onClick={() =>
                  toggleProvider(provider.id)
                }
                className={`border rounded-xl p-4 flex justify-between items-center transition ${
                  selectedProviders.includes(provider.id)
                    ? "border-purple-600 bg-purple-50"
                    : "hover:border-purple-300"
                }`}
              >
                <div className="flex items-center gap-3">

                  <Bot className="w-5 h-5" />

                  {provider.name}

                </div>

                <input
                  type="checkbox"
                  readOnly
                  checked={selectedProviders.includes(
                    provider.id
                  )}
                />

              </button>

            ))}

          </div>

        </div>

        <button
          disabled={running}
          onClick={handleRunBenchmark}
          className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-6 py-3 flex items-center gap-2"
        >
          {running ? (
            <>
              <Loader2 className="animate-spin w-5 h-5" />
              Running...
            </>
          ) : (
            <>
              <PlayCircle className="w-5 h-5" />
              Run Benchmark
            </>
          )}
        </button>

      </div>

    </div>
  );
};

export default Benchmark;