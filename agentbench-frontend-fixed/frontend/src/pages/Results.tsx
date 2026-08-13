import React, { useEffect, useState } from "react";
import { benchmarkAPI } from "../api";
import { useNavigate, useParams } from "react-router-dom";
import {
  FileText,
  Calendar,
  ChevronRight,
  ArrowLeft,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import type { BenchmarkResult } from "../api/benchmark";

interface Benchmark {
  id: number;
  title: string;
  description: string;
  created_at?: string;
}

const ResultsList: React.FC = () => {
  const navigate = useNavigate();
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await benchmarkAPI.listBenchmarks();
        setBenchmarks(res.data);
      } catch (err) {
        console.error(err);
        setBenchmarks([]);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return <div className="text-center py-20">Loading benchmarks...</div>;
  }

  if (benchmarks.length === 0) {
    return <div className="text-center py-20">No benchmark history found.</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Benchmark Results</h1>
        <p className="text-slate-500 mt-1">Select a benchmark to view detailed results.</p>
      </div>

      <div className="space-y-4">
        {benchmarks.map((benchmark) => (
          <div
            key={benchmark.id}
            onClick={() => navigate(`/results/${benchmark.id}`)}
            className="bg-white border rounded-2xl shadow-sm p-6 cursor-pointer hover:shadow-md hover:border-purple-500 transition"
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-4">
                <div className="bg-purple-100 p-3 rounded-xl">
                  <FileText className="text-purple-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold">{benchmark.title}</h2>
                  <p className="text-slate-500">{benchmark.description}</p>
                  {benchmark.created_at && (
                    <div className="flex items-center gap-2 text-sm text-slate-400 mt-2">
                      <Calendar size={16} />
                      {new Date(benchmark.created_at).toLocaleString()}
                    </div>
                  )}
                </div>
              </div>
              <ChevronRight className="text-slate-400" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ResultsDetail: React.FC<{ id: string }> = ({ id }) => {
  const navigate = useNavigate();
  const [results, setResults] = useState<BenchmarkResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const res = await benchmarkAPI.getResults(Number(id));
        setResults(res.data.results || []);
      } catch (err) {
        console.error(err);
        setError("Could not load results for this benchmark.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  return (
    <div className="space-y-8">
      <button
        onClick={() => navigate("/results")}
        className="flex items-center gap-2 text-slate-500 hover:text-slate-800"
      >
        <ArrowLeft size={18} />
        Back to all results
      </button>

      <div>
        <h1 className="text-3xl font-bold">Benchmark #{id}</h1>
        <p className="text-slate-500 mt-1">Per-provider results for this run.</p>
      </div>

      {loading && <div className="py-10 text-center">Loading results...</div>}
      {!loading && error && <div className="py-10 text-center text-red-600">{error}</div>}
      {!loading && !error && results.length === 0 && (
        <div className="py-10 text-center text-slate-500">No results yet for this benchmark.</div>
      )}

      {!loading && results.length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          {results.map((r, idx) => (
            <div key={`${r.provider}-${idx}`} className="bg-white border rounded-2xl shadow-sm p-6 space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-xl font-bold capitalize">{r.provider}</h2>
                  <p className="text-slate-500 text-sm">{r.model || "No agent configured"}</p>
                </div>
                {r.success ? (
                  <CheckCircle2 className="text-green-500" />
                ) : (
                  <XCircle className="text-red-500" />
                )}
              </div>

              <div className="grid grid-cols-3 gap-3 text-center">
                <div>
                  <div className="text-2xl font-bold">{r.score.toFixed(1)}</div>
                  <div className="text-xs text-slate-500">Score</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">{r.latency.toFixed(2)}s</div>
                  <div className="text-xs text-slate-500">Latency</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">${r.cost.toFixed(4)}</div>
                  <div className="text-xs text-slate-500">Cost</div>
                </div>
              </div>

              {r.error && (
                <div className="bg-red-50 border border-red-200 text-red-600 text-sm rounded-lg p-3">
                  {r.error}
                </div>
              )}

              {r.output && (
                <div>
                  <p className="text-sm font-semibold mb-1">Output</p>
                  <p className="text-sm text-slate-600 whitespace-pre-wrap bg-slate-50 rounded-lg p-3 max-h-48 overflow-auto">
                    {r.output}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const Results: React.FC = () => {
  // Previously this component ignored the :id route param entirely, so
  // navigating to /results/123 after running a benchmark just re-rendered
  // the same list with no way to see that run's actual output/score.
  const { id } = useParams<{ id: string }>();
  return id ? <ResultsDetail id={id} /> : <ResultsList />;
};

export default Results;
