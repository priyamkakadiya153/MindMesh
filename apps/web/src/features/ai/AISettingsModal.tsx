import React, { useState, useEffect } from 'react';
import {
  Cpu,
  X,
  Zap,
  Sliders,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  DollarSign,
  Clock,
  Save,
  Activity
} from 'lucide-react';
import {
  getAIProviders,
  getAIModels,
  getAISettings,
  updateAISettings,
  getAIHealth,
  testAIConnection
} from './api';
import { useAuth } from '../auth/auth-provider';

interface AISettingsModalProps {
  workspaceId: string;
  isOpen: boolean;
  onClose: () => void;
}

export interface AISettings {
  workspace_id: string;
  organization_id: string;
  provider: string;
  model: string;
  temperature: number;
  top_p: number;
  max_tokens: number;
  fallback_provider: string;
  fallback_model: string;
  system_prompt?: string;
}

export interface TestResult {
  content: string;
  model: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  latency_ms: number;
  finish_reason: string;
}

export const AISettingsModal: React.FC<AISettingsModalProps> = ({
  workspaceId,
  isOpen,
  onClose
}) => {
  const { token, user } = useAuth();
  const orgId = user?.organization_id || '';

  const [settings, setSettings] = useState<AISettings | null>(null);
  const [providers, setProviders] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [health, setHealth] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  const loadData = async () => {
    if (!token || !workspaceId) return;
    try {
      setLoading(true);
      const [provRes, modRes, setRes, hlthRes] = await Promise.all([
        getAIProviders(token, orgId).catch(() => []),
        getAIModels(token, orgId).catch(() => []),
        getAISettings(token, orgId, workspaceId).catch(() => null),
        getAIHealth(token, orgId).catch(() => [])
      ]);
      setProviders(provRes);
      setModels(modRes);
      if (setRes) setSettings(setRes);
      setHealth(hlthRes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) loadData();
  }, [isOpen, workspaceId, token]);

  const handleSave = async () => {
    if (!settings || !token) return;
    try {
      setSaving(true);
      await updateAISettings(token, orgId, settings);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!token || !settings) return;
    try {
      setTesting(true);
      const res = await testAIConnection(token, orgId, {
        prompt: 'Hello MindMesh AI! Test provider connection and latency.',
        workspace_id: workspaceId,
        provider: settings.provider,
        model: settings.model
      });
      setTestResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setTesting(false);
    }
  };

  if (!isOpen || !settings) return null;

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-bgDialog border border-borderColor rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 px-6 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-accentSubtle border border-accent/20 text-accentText rounded-xl">
              <Cpu size={20} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">
                Multi-LLM Provider & Workspace AI Configuration
              </h3>
              <p className="text-[11px] text-textMuted font-mono">
                Google Gemini • OpenAI • Anthropic Claude • Ollama Local
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-textMuted hover:text-textPrimary rounded-lg hover:bg-bgHover">
            <X size={18} />
          </button>
        </div>

        {/* Form Controls */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Provider & Model Selectors */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Primary AI Provider</label>
              <select
                value={settings.provider}
                onChange={(e) => setSettings({ ...settings, provider: e.target.value })}
                className="w-full bg-bgInput border border-borderColor rounded-xl px-3.5 py-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="gemini">Google Gemini (Cloud)</option>
                <option value="openai">OpenAI (Cloud)</option>
                <option value="claude">Anthropic Claude (Cloud)</option>
                <option value="ollama">Ollama (Local LLM)</option>
                <option value="mock">Mock Adapter (Offline Fallback)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-textSecondary">Primary Model</label>
              <select
                value={settings.model}
                onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                className="w-full bg-bgInput border border-borderColor rounded-xl px-3.5 py-2.5 text-xs text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
                <option value="llama3">Llama 3 (Local)</option>
              </select>
            </div>
          </div>

          {/* Hyperparameters Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-bgCard p-4 rounded-xl border border-borderColor">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-textMuted">Temperature</span>
                <span className="font-mono text-accentText font-bold">{settings.temperature}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="2.0"
                step="0.05"
                value={settings.temperature}
                onChange={(e) => setSettings({ ...settings, temperature: parseFloat(e.target.value) })}
                className="w-full accent-accent"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-textMuted">Top P</span>
                <span className="font-mono text-accentText font-bold">{settings.top_p}</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={settings.top_p}
                onChange={(e) => setSettings({ ...settings, top_p: parseFloat(e.target.value) })}
                className="w-full accent-accent"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-textMuted">Max Output Tokens</span>
                <span className="font-mono text-accentText font-bold">{settings.max_tokens}</span>
              </div>
              <input
                type="number"
                min="256"
                max="16384"
                value={settings.max_tokens}
                onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) || 2048 })}
                className="w-full bg-bgInput border border-borderColor rounded-lg px-2.5 py-1 text-xs text-textPrimary font-mono"
              />
            </div>
          </div>

          {/* Failover Provider Config */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-textSecondary">Fallback Provider (Failover Chain)</label>
            <select
              value={settings.fallback_provider}
              onChange={(e) => setSettings({ ...settings, fallback_provider: e.target.value })}
              className="w-full bg-bgInput border border-borderColor rounded-xl px-3.5 py-2.5 text-xs text-textPrimary focus:outline-none"
            >
              <option value="openai">OpenAI (GPT-4o Mini)</option>
              <option value="gemini">Google Gemini</option>
              <option value="mock">Mock Adapter Fallback</option>
            </select>
          </div>

          {/* Connection Test Output Card */}
          {testResult && (
            <div className="bg-bgCard border border-borderColor rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-borderMuted pb-2 text-xs">
                <span className="flex items-center gap-1.5 text-successText font-medium">
                  <CheckCircle2 size={14} /> Provider Test Successful ({testResult.provider})
                </span>
                <div className="flex items-center gap-3 text-[11px] font-mono text-textMuted">
                  <span className="flex items-center gap-1"><Clock size={11} /> {testResult.latency_ms} ms</span>
                  <span className="flex items-center gap-1"><DollarSign size={11} /> ${testResult.estimated_cost_usd}</span>
                  <span>{testResult.total_tokens} Tokens</span>
                </div>
              </div>

              <p className="text-xs font-mono text-textSecondary bg-bgInput p-3 rounded-lg border border-borderColor">
                {testResult.content}
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 px-6 border-t border-borderMuted bg-bgHeader flex items-center justify-between">
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-bgTertiary hover:bg-bgHover text-textSecondary rounded-xl text-xs font-semibold transition-colors border border-borderMuted"
          >
            <Zap size={14} className={testing ? 'animate-spin' : ''} />
            <span>{testing ? 'Testing...' : 'Test Provider Connection'}</span>
          </button>

          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-2 text-xs font-medium text-textMuted hover:text-textPrimary">
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 bg-accent hover:bg-accentHover disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Save size={14} />
              <span>{saving ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
