import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  PlayCircle,
  Bot,
  BarChart3,
  Trophy,
  Settings,
  Cpu,
} from "lucide-react";

const Sidebar: React.FC = () => {
  const location = useLocation();

  const menu = [
    {
      title: "Dashboard",
      path: "/",
      icon: LayoutDashboard,
    },
    {
      title: "Benchmark",
      path: "/benchmark",
      icon: PlayCircle,
    },
    {
      title: "Agents",
      path: "/agents",
      icon: Bot,
    },
    {
      title: "Results",
      path: "/results",
      icon: BarChart3,
    },
    {
      title: "Leaderboard",
      path: "/leaderboard",
      icon: Trophy,
    },
    {
      title: "Settings",
      path: "/settings",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-72 bg-slate-950 text-white flex flex-col border-r border-slate-800">

      {/* Logo */}

      <div className="p-6 border-b border-slate-800">

        <div className="flex items-center gap-3">

          <div className="w-11 h-11 rounded-xl bg-purple-600 flex items-center justify-center">

            <Cpu className="w-6 h-6" />

          </div>

          <div>

            <h1 className="text-xl font-bold">
              AgentBench
            </h1>

            <p className="text-sm text-slate-400">
              AI Benchmark Platform
            </p>

          </div>

        </div>

      </div>

      {/* Navigation */}

      <div className="flex-1 px-4 py-6">

        <p className="text-xs uppercase tracking-widest text-slate-500 mb-4">
          Navigation
        </p>

        <div className="space-y-2">

          {menu.map((item) => {

            const Icon = item.icon;

            const active =
              location.pathname === item.path;

            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex
                  items-center
                  gap-3
                  rounded-xl
                  px-4
                  py-3
                  transition-all
                  ${
                    active
                      ? "bg-purple-600 text-white shadow-lg"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }
                `}
              >
                <Icon className="w-5 h-5" />

                <span>{item.title}</span>

              </Link>
            );
          })}

        </div>

      </div>

      {/* System Status */}

      <div className="border-t border-slate-800 p-5">

        <p className="text-xs uppercase text-slate-500 mb-4">
          Providers
        </p>

        <div className="space-y-3">

          <div className="flex justify-between">

            <span>Ollama</span>

            <span className="text-green-400">
              ● Online
            </span>

          </div>

          <div className="flex justify-between">

            <span>Gemini</span>

            <span className="text-yellow-400">
              ● Not Configured
            </span>

          </div>

          <div className="flex justify-between">

            <span>OpenAI</span>

            <span className="text-slate-500">
              ● Disabled
            </span>

          </div>

        </div>

      </div>

    </aside>
  );
};

export default Sidebar;