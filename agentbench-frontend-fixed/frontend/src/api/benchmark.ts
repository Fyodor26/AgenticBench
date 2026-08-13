import apiClient from "./client";

/* ---------------- BENCHMARKS ---------------- */

export interface BenchmarkRequest {
  task_name: string;
  prompt: string;
  expected_output?: string;
  providers: string[];
}

export interface BenchmarkResult {
  provider: string;
  model: string | null;
  score: number;
  latency: number;
  tokens: number;
  cost: number;
  output: string;
  success: boolean;
  error?: string | null;
}

export interface BenchmarkResponse {
  benchmark_id: number;
  status: string;
  results: BenchmarkResult[];
}

export const benchmarkAPI = {
  // Runs synchronously and returns the full result set - the backend now
  // executes every selected provider (previously only the first selected
  // provider was ever run; the rest were silently ignored).
  runBenchmark: (data: BenchmarkRequest) =>
    apiClient.post<BenchmarkResponse>("/benchmarks/run", data),

  // Benchmark run history for the current user (backed by Task rows with
  // category "Benchmark" - see backend BenchmarkService.get_all).
  listBenchmarks: () => apiClient.get("/benchmarks"),

  // `benchmark_id` returned above is the underlying Task id, and
  // GET /benchmarks/{id}/results is scoped to the requesting user.
  getResults: (id: number) => apiClient.get(`/benchmarks/${id}/results`),
};
