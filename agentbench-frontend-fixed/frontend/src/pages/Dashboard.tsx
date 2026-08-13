import React, { useEffect, useState } from "react";
import {
  Bot,
  Trophy,
  Activity,
  Clock,
  PlayCircle,
  ArrowUpRight,
} from "lucide-react";
import { agentAPI, leaderboardAPI, statsAPI } from "../api";
import { useNavigate } from "react-router-dom";

interface LeaderboardEntry {
  agent_id: number;
  agent_name: string;
  average_score: number;
  rank: number;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [stats, setStats] = useState({
    totalAgents: 0,
    totalRuns: 0,
    topScore: 0,
    successRate: 0,
  });

  useEffect(() => {
    const load = async () => {
      try {
        // Previously this only ever fetched the agent count and hardcoded
        // everything else (totalRuns: 0, successRate: 98.4, leaderboard:
        // []) - the dashboard never reflected real activity. Both of these
        // endpoints now exist and are wired up for real.
        const [agentsRes, statsRes, leaderboardRes] = await Promise.all([
          agentAPI.listAgents(0, 1000),
          statsAPI.getOverview(),
          leaderboardAPI.getLeaderboard(5, 0),
        ]);

        setLeaderboard(leaderboardRes.data);

        setStats({
          totalAgents: agentsRes.data.length,
          totalRuns: statsRes.data.total_evaluations,
          topScore: leaderboardRes.data[0]?.average_score ?? 0,
          successRate: statsRes.data.success_rate,
        });
        setLoadError("");
      } catch (err) {
        console.error(err);
        setLoadError("Some dashboard data could not be loaded.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const cards = [
    { title: "Agents", value: stats.totalAgents, icon: Bot, color: "bg-purple-600" },
    { title: "Benchmark Runs", value: stats.totalRuns, icon: Activity, color: "bg-blue-600" },
    { title: "Top Score", value: stats.topScore.toFixed(1), icon: Trophy, color: "bg-green-600" },
    { title: "Success Rate", value: `${stats.successRate}%`, icon: Clock, color: "bg-orange-500" },
  ];

  return (
    <div className="space-y-8">
      {/* Hero */}
      <div className="rounded-2xl bg-gradient-to-r from-purple-700 to-indigo-700 text-white p-8">
        <h1 className="text-4xl font-bold">Welcome to AgentBench</h1>
        <p className="mt-2 text-purple-100">
          Benchmark multiple AI models, compare outputs, evaluate quality, and discover the
          best-performing agent.
        </p>
        <button
          onClick={() => navigate("/benchmark")}
          className="mt-6 flex items-center gap-2 bg-white text-purple-700 px-5 py-3 rounded-xl font-semibold hover:bg-gray-100 transition"
        >
          <PlayCircle className="w-5 h-5" />
          Run Benchmark
        </button>
      </div>

      {loadError && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-3 rounded-lg text-sm">
          {loadError}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="bg-white rounded-2xl shadow-sm border p-6">
              <div className="flex justify-between">
                <div>
                  <p className="text-slate-500 text-sm">{card.title}</p>
                  <h2 className="text-3xl font-bold mt-2">{card.value}</h2>
                </div>
                <div className={`${card.color} w-12 h-12 rounded-xl flex items-center justify-center text-white`}>
                  <Icon size={22} />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Leaderboard */}
        <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border">
          <div className="flex justify-between items-center p-6 border-b">
            <h2 className="text-xl font-bold">Top Performing Agents</h2>
            <button onClick={() => navigate("/leaderboard")} title="View full leaderboard">
              <ArrowUpRight className="text-slate-400 hover:text-purple-600" />
            </button>
          </div>

          {loading ? (
            <div className="p-6">Loading...</div>
          ) : leaderboard.length === 0 ? (
            <div className="p-6 text-slate-500">No evaluations yet - run a benchmark to populate this.</div>
          ) : (
            <div className="divide-y">
              {leaderboard.map((agent) => (
                <div
                  key={agent.agent_id}
                  className="flex justify-between items-center px-6 py-5 hover:bg-slate-50 transition"
                >
                  <div>
                    <p className="font-semibold">
                      #{agent.rank} {agent.agent_name}
                    </p>
                    <p className="text-sm text-slate-500">AI Model</p>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-xl">{agent.average_score.toFixed(1)}</div>
                    <div className="w-32 bg-slate-200 rounded-full h-2 mt-2">
                      <div
                        className="bg-gradient-to-r from-purple-600 to-blue-500 h-2 rounded-full"
                        style={{ width: `${Math.min(100, agent.average_score)}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* System */}
        <div className="bg-white rounded-2xl shadow-sm border p-6">
          <h2 className="text-xl font-bold mb-5">Getting Started</h2>
          <div className="space-y-4 text-sm text-slate-600">
            <p>1. Add an AI provider under <b>Agents</b>.</p>
            <p>2. Configure API keys under <b>Settings</b>.</p>
            <p>3. Run a benchmark from the <b>Benchmark</b> page.</p>
            <p>4. Compare providers on the <b>Leaderboard</b>.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
