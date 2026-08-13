import React from "react";
import {
  Bell,
  LogOut,
  Search,
  Cpu,
  Activity,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const Navigation: React.FC = () => {
  const { logout } = useAuth();
  const handleLogout = () => {
    logout();
  };

  return (
    <header className="h-20 bg-white border-b border-slate-200 flex items-center justify-between px-8">

      {/* Left */}

      <div>

        <h1 className="text-2xl font-bold text-slate-800">
          AI Benchmark Dashboard
        </h1>

        <p className="text-sm text-slate-500">
          Compare multiple AI agents with standardized benchmarks
        </p>

      </div>

      {/* Center */}

      <div className="hidden lg:flex items-center bg-slate-100 rounded-xl px-4 py-2 w-96">

        <Search className="w-5 h-5 text-slate-400 mr-3" />

        <input
          placeholder="Search agents, benchmarks..."
          className="bg-transparent outline-none w-full text-sm"
        />

      </div>

      {/* Right */}

      <div className="flex items-center gap-5">

        {/* Status */}

        <div className="hidden md:flex items-center gap-2 bg-green-50 text-green-700 px-4 py-2 rounded-xl">

          <Activity className="w-4 h-4" />

          System Healthy

        </div>

        {/* Active Provider */}

        <div className="hidden xl:flex items-center gap-2 bg-purple-50 text-purple-700 px-4 py-2 rounded-xl">

          <Cpu className="w-4 h-4" />

          Ollama Connected

        </div>

        {/* Notifications */}

        <button className="relative p-2 rounded-lg hover:bg-slate-100">

          <Bell className="w-5 h-5" />

          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>

        </button>

        {/* Logout */}

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-xl transition"
        >
          <LogOut className="w-4 h-4" />

          Logout
        </button>

      </div>

    </header>
  );
};

export default Navigation;