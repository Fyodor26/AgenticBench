import React, { useEffect, useState } from "react";
import {
  Save,
  Cpu,
  Key,
  Globe,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { settingsAPI } from "../api";

const Settings: React.FC = () => {
  const [ollamaUrl, setOllamaUrl] = useState("http://localhost:11434");
  const [geminiKey, setGeminiKey] = useState("");
  const [geminiKeySet, setGeminiKeySet] = useState(false);
  const [openaiKey, setOpenaiKey] = useState("");
  const [openaiKeySet, setOpenaiKeySet] = useState(false);
  const [judgeModel, setJudgeModel] = useState("gemini");
  const [temperature, setTemperature] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2048);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; message: string } | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await settingsAPI.getSettings();
        setOllamaUrl(res.data.ollama_base_url);
        setGeminiKeySet(res.data.gemini_api_key_set);
        setOpenaiKeySet(res.data.openai_api_key_set);
        setJudgeModel(res.data.judge_model);
        setTemperature(res.data.temperature);
        setMaxTokens(res.data.max_tokens);
      } catch (err) {
        console.error(err);
        setStatus({ type: "error", message: "Could not load your saved settings." });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  // Previously this just called alert("Settings saved.") and threw the
  // values away - nothing was ever sent to the backend, so a refresh lost
  // everything the user typed. This now actually persists via PUT
  // /settings (API keys are encrypted at rest server-side and are never
  // sent back to the client in plaintext, hence the write-only fields
  // above only being cleared/re-masked after a successful save).
  const handleSave = async () => {
    setSaving(true);
    setStatus(null);
    try {
      const payload: Record<string, unknown> = {
        ollama_base_url: ollamaUrl,
        judge_model: judgeModel,
        temperature,
        max_tokens: maxTokens,
      };
      if (geminiKey) payload.gemini_api_key = geminiKey;
      if (openaiKey) payload.openai_api_key = openaiKey;

      const res = await settingsAPI.saveSettings(payload);
      setGeminiKeySet(res.data.gemini_api_key_set);
      setOpenaiKeySet(res.data.openai_api_key_set);
      setGeminiKey("");
      setOpenaiKey("");
      setStatus({ type: "success", message: "Settings saved." });
    } catch (err) {
      console.error(err);
      setStatus({ type: "error", message: "Failed to save settings." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-20">Loading settings...</div>;
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-slate-500 mt-1">Configure providers and benchmark defaults.</p>
      </div>

      {/* Ollama */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <Cpu />
          <h2 className="text-xl font-bold">Ollama</h2>
        </div>
        <label className="block font-medium mb-2">Base URL</label>
        <input
          className="w-full border rounded-xl p-3"
          value={ollamaUrl}
          onChange={(e) => setOllamaUrl(e.target.value)}
        />
      </div>

      {/* Gemini */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <Key />
          <h2 className="text-xl font-bold">Gemini</h2>
        </div>
        <label className="block font-medium mb-2">
          API Key {geminiKeySet && <span className="text-green-600 text-sm">(saved &middot; leave blank to keep)</span>}
        </label>
        <input
          type="password"
          className="w-full border rounded-xl p-3"
          placeholder={geminiKeySet ? "••••••••••••" : "AIza..."}
          value={geminiKey}
          onChange={(e) => setGeminiKey(e.target.value)}
        />
      </div>

      {/* OpenAI */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <div className="flex items-center gap-3 mb-6">
          <Globe />
          <h2 className="text-xl font-bold">OpenAI</h2>
        </div>
        <label className="block font-medium mb-2">
          API Key {openaiKeySet && <span className="text-green-600 text-sm">(saved &middot; leave blank to keep)</span>}
        </label>
        <input
          type="password"
          className="w-full border rounded-xl p-3"
          placeholder={openaiKeySet ? "••••••••••••" : "sk-..."}
          value={openaiKey}
          onChange={(e) => setOpenaiKey(e.target.value)}
        />
      </div>

      {/* Benchmark Defaults */}
      <div className="bg-white rounded-2xl border shadow-sm p-6">
        <h2 className="text-xl font-bold mb-6">Benchmark Defaults</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <label className="block mb-2 font-medium">Judge Model</label>
            <select
              className="w-full border rounded-xl p-3"
              value={judgeModel}
              onChange={(e) => setJudgeModel(e.target.value)}
            >
              <option value="gemini">Gemini</option>
              <option value="openai">GPT-4o</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>

          <div>
            <label className="block mb-2 font-medium">Temperature</label>
            <input
              type="number"
              step="0.1"
              min={0}
              max={2}
              className="w-full border rounded-xl p-3"
              value={temperature}
              onChange={(e) => setTemperature(Number(e.target.value))}
            />
          </div>

          <div>
            <label className="block mb-2 font-medium">Max Tokens</label>
            <input
              type="number"
              min={1}
              max={32000}
              className="w-full border rounded-xl p-3"
              value={maxTokens}
              onChange={(e) => setMaxTokens(Number(e.target.value))}
            />
          </div>
        </div>
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="bg-purple-600 hover:bg-purple-700 text-white rounded-xl px-6 py-3 flex items-center gap-2 disabled:opacity-50"
      >
        <Save size={18} />
        {saving ? "Saving..." : "Save Settings"}
      </button>

      {status && (
        <div
          className={`flex items-center gap-2 ${
            status.type === "success" ? "text-green-600" : "text-red-600"
          }`}
        >
          {status.type === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          {status.message}
        </div>
      )}
    </div>
  );
};

export default Settings;
