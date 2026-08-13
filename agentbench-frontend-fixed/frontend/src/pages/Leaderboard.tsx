import React, { useEffect, useState } from "react";
import {
  Trophy,
  Medal,
  Award,
  Clock,
  Coins,
  Target,
} from "lucide-react";
import { leaderboardAPI } from "../api";

interface LeaderboardEntry {
  agent_id: number;
  agent_name: string;
  provider: string;
  average_score: number;
  average_execution_time: number;
  total_cost: number;
  evaluation_count: number;
  success_rate: number;
  rank: number;
}

const Leaderboard: React.FC = () => {
  const [leaders, setLeaders] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, []);

 const loadLeaderboard = async () => {
  try {
    const res = await leaderboardAPI.getLeaderboard();

    setLeaders(res.data);
  } catch (err) {
    console.error(err);

    setLeaders([]);
  } finally {
    setLoading(false);
  }
};

  const getIcon = (index: number) => {
    if (index === 0)
      return <Trophy className="text-yellow-500 w-6 h-6" />;

    if (index === 1)
      return <Medal className="text-gray-400 w-6 h-6" />;

    if (index === 2)
      return <Award className="text-orange-500 w-6 h-6" />;

    return (
      <span className="font-bold text-slate-500">
        #{index + 1}
      </span>
    );
  };

  return (
    <div className="space-y-8">

      <div>

        <h1 className="text-3xl font-bold">
          Leaderboard
        </h1>

        <p className="text-slate-500 mt-1">
          Overall ranking of AI providers based on benchmark performance.
        </p>

      </div>

      {loading ? (
  <div className="text-center py-20">
    Loading leaderboard...
  </div>
) : leaders.length === 0 ? (
  <div className="bg-white rounded-2xl border p-10 text-center">
    <h2 className="text-xl font-semibold">
      No benchmark results yet
    </h2>

    <p className="text-slate-500 mt-2">
      Run your first benchmark to generate rankings.
    </p>
  </div>
) : (
        <div className="space-y-5">

          {leaders.map((agent, index) => (

            <div
              key={agent.agent_id}
              className="bg-white rounded-2xl border shadow-sm p-6"
            >

              <div className="flex justify-between items-center">

                <div className="flex items-center gap-5">

                  {getIcon(index)}

                  <div>

                    <h2 className="text-xl font-bold">
                      {agent.agent_name}
                    </h2>

                    <p className="text-slate-500">
                      Rank #{index + 1}
                    </p>

                  </div>

                </div>

                <div className="text-right">

                  <div className="text-3xl font-bold text-purple-600">
                    {agent.average_score.toFixed(1)}
                  </div>

                  <div className="text-sm text-slate-500">
                    Overall Score
                  </div>

                </div>

              </div>

              <div className="grid grid-cols-4 gap-5 mt-8">

                <div className="bg-slate-100 rounded-xl p-4">

                  <div className="flex items-center gap-2 mb-2">

                    <Target size={18} />

                    Score

                  </div>

                  <div className="text-2xl font-bold">
                    {agent.average_score.toFixed(1)}
                  </div>

                </div>

                <div className="bg-slate-100 rounded-xl p-4">

                  <div className="flex items-center gap-2 mb-2">

                    <Clock size={18} />

                    Latency

                  </div>

                  <div className="text-2xl font-bold">
                    {agent.average_execution_time.toFixed(2)}s
                  </div>

                </div>

                <div className="bg-slate-100 rounded-xl p-4">

                  <div className="flex items-center gap-2 mb-2">

                    <Coins size={18} />

                    Cost

                  </div>

                  <div className="text-2xl font-bold">
                    ${agent.total_cost.toFixed(4)}
                  </div>

                </div>

                <div className="bg-slate-100 rounded-xl p-4">

                  <div className="mb-2">
                    Runs
                  </div>

                  <div className="text-2xl font-bold">
                    {agent.evaluation_count}
                  </div>

                </div>

              </div>

            </div>

          ))}

        </div>
      )}
    </div>
  );
};

export default Leaderboard;