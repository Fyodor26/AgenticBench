import React, { useEffect, useState } from "react";
import {
  Bot,
  CheckCircle2,
  XCircle,
  Settings as SettingsIcon,
  PlayCircle,
  Loader2,
  Trash2,
  X,
} from "lucide-react";
import { agentAPI } from "../api";

interface Agent {
  id: number;
  name: string;
  description: string;
  provider: string;
  model: string | null;
  api_endpoint: string | null;
  temperature: number;
  max_tokens: number;
  timeout: number;
  is_active: boolean;
}

interface AgentFormState {
  name: string;
  description: string;
  provider: string;
  model: string;
  api_endpoint: string;
  api_key: string;
  temperature: number;
  max_tokens: number;
  timeout: number;
  is_active: boolean;
}

const emptyForm: AgentFormState = {
  name: "",
  description: "",
  provider: "ollama",
  model: "",
  api_endpoint: "",
  api_key: "",
  temperature: 0.7,
  max_tokens: 2048,
  timeout: 60,
  is_active: true,
};

const Agents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<AgentFormState>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  const [testing, setTesting] = useState<number | null>(null);
  const [testResult, setTestResult] = useState<Record<number, { success: boolean; message: string }>>({});

  useEffect(() => {
    loadAgents();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const res = await agentAPI.listAgents(0, 100);
      setAgents(res.data);
      setLoadError("");
    } catch (err) {
      console.error(err);
      // No mock fallback here anymore - silently showing fake agents as if
      // they were real (as the previous version did) hides genuine backend
      // outages from the user.
      setAgents([]);
      setLoadError("Could not load agents. Is the API reachable?");
    } finally {
      setLoading(false);
    }
  };

  const openCreateModal = () => {
    setEditingId(null);
    setForm(emptyForm);
    setFormError("");
    setModalOpen(true);
  };

  const openEditModal = (agent: Agent) => {
    setEditingId(agent.id);
    setForm({
      name: agent.name,
      description: agent.description || "",
      provider: agent.provider,
      model: agent.model || "",
      api_endpoint: agent.api_endpoint || "",
      api_key: "",
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      timeout: agent.timeout,
      is_active: agent.is_active,
    });
    setFormError("");
    setModalOpen(true);
  };

  const closeModal = () => setModalOpen(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setFormError("");

    const payload: Record<string, unknown> = {
      name: form.name,
      description: form.description,
      provider: form.provider,
      model: form.model || null,
      api_endpoint: form.api_endpoint || null,
      temperature: form.temperature,
      max_tokens: form.max_tokens,
      timeout: form.timeout,
      is_active: form.is_active,
    };
    // Only send api_key if the user actually typed one, so editing an agent
    // without touching the key field doesn't wipe out the stored credential.
    if (form.api_key) payload.api_key = form.api_key;

    try {
      if (editingId) {
        await agentAPI.updateAgent(editingId, payload);
      } else {
        await agentAPI.createAgent(payload);
      }
      setModalOpen(false);
      await loadAgents();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setFormError(Array.isArray(detail) ? detail[0]?.msg : detail || "Failed to save agent.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (agent: Agent) => {
    if (!window.confirm(`Delete agent "${agent.name}"? This cannot be undone.`)) return;
    try {
      await agentAPI.deleteAgent(agent.id);
      await loadAgents();
    } catch (err) {
      console.error(err);
      window.alert("Failed to delete agent.");
    }
  };

  const testConnection = async (agent: Agent) => {
    setTesting(agent.id);
    try {
      const res = await agentAPI.testConnection(agent.id);
      setTestResult((prev) => ({ ...prev, [agent.id]: res.data }));
    } catch (err: any) {
      setTestResult((prev) => ({
        ...prev,
        [agent.id]: { success: false, message: err.response?.data?.detail || "Test failed" },
      }));
    } finally {
      setTesting(null);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">AI Providers</h1>
          <p className="text-slate-500">Configure and monitor your available AI models.</p>
        </div>

        <button
          onClick={openCreateModal}
          className="bg-purple-600 hover:bg-purple-700 text-white px-5 py-3 rounded-xl"
        >
          Add Provider
        </button>
      </div>

      {loadError && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
          {loadError}
        </div>
      )}

      {loading ? (
        <div>Loading...</div>
      ) : agents.length === 0 ? (
        <div className="text-center py-20 text-slate-500">
          No agents configured yet. Click "Add Provider" to create one.
        </div>
      ) : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-6">
          {agents.map((agent) => (
            <div key={agent.id} className="bg-white rounded-2xl border shadow-sm overflow-hidden">
              <div className="bg-slate-900 text-white p-5">
                <div className="flex justify-between">
                  <Bot className="w-8 h-8" />
                  {agent.is_active ? (
                    <CheckCircle2 className="text-green-400" />
                  ) : (
                    <XCircle className="text-red-400" />
                  )}
                </div>
                <h2 className="text-xl font-bold mt-4">{agent.name}</h2>
                <p className="text-slate-400">{agent.model || "No model set"}</p>
              </div>

              <div className="p-6 space-y-4">
                <div className="flex justify-between">
                  <span>Provider</span>
                  <span className="font-semibold capitalize">{agent.provider}</span>
                </div>

                <div className="flex justify-between">
                  <span>Status</span>
                  <span
                    className={agent.is_active ? "text-green-600 font-semibold" : "text-red-500 font-semibold"}
                  >
                    {agent.is_active ? "Active" : "Disabled"}
                  </span>
                </div>

                {testResult[agent.id] && (
                  <div
                    className={`text-sm rounded-lg p-2 ${
                      testResult[agent.id].success
                        ? "bg-green-50 text-green-700"
                        : "bg-red-50 text-red-700"
                    }`}
                  >
                    {testResult[agent.id].message}
                  </div>
                )}

                <div className="flex gap-3 pt-3">
                  <button
                    onClick={() => testConnection(agent)}
                    disabled={testing === agent.id}
                    className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl py-2 disabled:opacity-50"
                  >
                    {testing === agent.id ? (
                      <Loader2 size={18} className="animate-spin" />
                    ) : (
                      <PlayCircle size={18} />
                    )}
                    Test
                  </button>

                  <button
                    onClick={() => openEditModal(agent)}
                    className="flex-1 flex items-center justify-center gap-2 border rounded-xl py-2 hover:bg-slate-100"
                  >
                    <SettingsIcon size={18} />
                    Configure
                  </button>

                  <button
                    onClick={() => handleDelete(agent)}
                    className="flex items-center justify-center gap-2 border border-red-200 text-red-600 rounded-xl py-2 px-3 hover:bg-red-50"
                    title="Delete agent"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-auto">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">{editingId ? "Edit Agent" : "Add Provider"}</h2>
              <button onClick={closeModal} className="text-slate-400 hover:text-slate-700">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Name</label>
                <input
                  required
                  className="w-full border rounded-xl p-3"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <textarea
                  className="w-full border rounded-xl p-3"
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Provider</label>
                  <select
                    className="w-full border rounded-xl p-3"
                    value={form.provider}
                    onChange={(e) => setForm({ ...form, provider: e.target.value })}
                  >
                    <option value="ollama">Ollama</option>
                    <option value="gemini">Gemini</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Model</label>
                  <input
                    className="w-full border rounded-xl p-3"
                    placeholder="e.g. qwen3:4b"
                    value={form.model}
                    onChange={(e) => setForm({ ...form, model: e.target.value })}
                  />
                </div>
              </div>

              {form.provider === "gemini" && (
                <div>
                  <label className="block text-sm font-medium mb-1">API Key</label>
                  <input
                    type="password"
                    placeholder={editingId ? "Leave blank to keep existing key" : "AIza..."}
                    className="w-full border rounded-xl p-3"
                    value={form.api_key}
                    onChange={(e) => setForm({ ...form, api_key: e.target.value })}
                  />
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Temperature</label>
                  <input
                    type="number"
                    step="0.1"
                    min={0}
                    max={2}
                    className="w-full border rounded-xl p-3"
                    value={form.temperature}
                    onChange={(e) => setForm({ ...form, temperature: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Max Tokens</label>
                  <input
                    type="number"
                    min={1}
                    className="w-full border rounded-xl p-3"
                    value={form.max_tokens}
                    onChange={(e) => setForm({ ...form, max_tokens: Number(e.target.value) })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Timeout (s)</label>
                  <input
                    type="number"
                    min={1}
                    className="w-full border rounded-xl p-3"
                    value={form.timeout}
                    onChange={(e) => setForm({ ...form, timeout: Number(e.target.value) })}
                  />
                </div>
              </div>

              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                />
                Active
              </label>

              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-2 rounded-lg text-sm">
                  {formError}
                </div>
              )}

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-5 py-2 rounded-xl border hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white disabled:opacity-50"
                >
                  {saving ? "Saving..." : editingId ? "Save Changes" : "Create Agent"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Agents;
