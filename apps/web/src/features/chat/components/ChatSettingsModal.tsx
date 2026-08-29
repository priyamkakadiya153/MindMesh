import React, { useState } from 'react';
import { X, Sliders, Cpu, Sparkles, Save, RotateCcw } from 'lucide-react';

interface ChatSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  settings: {
    provider: string;
    model: string;
    temperature: number;
    maxTokens: number;
    topP: number;
    systemPrompt: string;
  };
  onSaveSettings: (newSettings: any) => void;
}

const PROVIDERS = [
  { id: 'gemini', name: 'Google Gemini', defaultModel: 'gemini-2.5-flash' },
  { id: 'openai', name: 'OpenAI', defaultModel: 'gpt-4o-mini' },
  { id: 'anthropic', name: 'Anthropic Claude', defaultModel: 'claude-3-5-sonnet' },
  { id: 'azure', name: 'Azure OpenAI', defaultModel: 'gpt-4o' },
  { id: 'ollama', name: 'Ollama (Local)', defaultModel: 'llama3' },
  { id: 'lmstudio', name: 'LM Studio (Local)', defaultModel: 'local-model' }
];

export const ChatSettingsModal: React.FC<ChatSettingsModalProps> = ({
  isOpen,
  onClose,
  settings,
  onSaveSettings
}) => {
  const [provider, setProvider] = useState(settings.provider || 'gemini');
  const [model, setModel] = useState(settings.model || 'gemini-2.5-flash');
  const [temperature, setTemperature] = useState(settings.temperature ?? 0.2);
  const [maxTokens, setMaxTokens] = useState(settings.maxTokens ?? 1024);
  const [topP, setTopP] = useState(settings.topP ?? 0.95);
  const [systemPrompt, setSystemPrompt] = useState(settings.systemPrompt || '');

  if (!isOpen) return null;

  const handleProviderChange = (pId: string) => {
    setProvider(pId);
    const selected = PROVIDERS.find(p => p.id === pId);
    if (selected) {
      setModel(selected.defaultModel);
    }
  };

  const handleSave = () => {
    onSaveSettings({
      provider,
      model,
      temperature,
      maxTokens,
      topP,
      systemPrompt
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-bgOverlay backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
      <div className="w-full max-w-lg bg-bgDialog border border-borderColor rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-borderMuted flex items-center justify-between bg-bgHeader">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-accentSubtle rounded-lg text-accentText">
              <Sliders size={18} />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-textPrimary">AI Intelligence Settings</h3>
              <p className="text-[10px] text-textMuted">Configure LLM Provider, Temperature & Context</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-textMuted hover:text-textPrimary hover:bg-bgHover rounded-lg transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Form Body */}
        <div className="p-5 space-y-4 text-xs text-textSecondary max-h-[75vh] overflow-y-auto">
          {/* Provider Selector */}
          <div>
            <label className="text-textMuted font-medium mb-1.5 flex items-center gap-1.5">
              <Cpu size={14} className="text-accentText" /> LLM Provider
            </label>
            <select
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full px-3 py-2 bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent"
            >
              {PROVIDERS.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Model Name */}
          <div>
            <label className="block text-textMuted font-medium mb-1.5">Model Identifier</label>
            <input
              type="text"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder="e.g. gemini-2.0-flash, gpt-4o"
              className="w-full px-3 py-2 bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent font-mono text-xs"
            />
          </div>

          {/* Temperature & Max Tokens Sliders */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="flex justify-between mb-1">
                <label className="text-textMuted font-medium">Temperature</label>
                <span className="font-mono text-accentText">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-accent cursor-pointer"
              />
              <span className="text-[9px] text-textMuted">Lower = deterministic, Higher = creative</span>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <label className="text-textMuted font-medium">Max Tokens</label>
                <span className="font-mono text-accentText">{maxTokens}</span>
              </div>
              <input
                type="range"
                min="256"
                max="4096"
                step="128"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full accent-accent cursor-pointer"
              />
              <span className="text-[9px] text-textMuted">Maximum response completion budget</span>
            </div>
          </div>

          {/* System Prompt Customization */}
          <div>
            <label className="text-textMuted font-medium mb-1.5 flex items-center gap-1.5">
              <Sparkles size={14} className="text-amber-500" /> Workspace System Prompt Override
            </label>
            <textarea
              rows={3}
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Enter custom instructions or role behavior for this workspace RAG pipeline..."
              className="w-full px-3 py-2 bg-bgInput border border-borderColor rounded-xl text-textPrimary focus:outline-none focus:border-accent font-mono text-xs leading-relaxed"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-borderMuted bg-bgHeader flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-bgTertiary hover:bg-bgHover text-textMuted hover:text-textPrimary rounded-xl text-xs font-medium transition-colors border border-borderMuted"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-1.5 px-4 py-2 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold shadow-lg shadow-accent/20 transition-colors"
          >
            <Save size={14} /> Save AI Settings
          </button>
        </div>
      </div>
    </div>
  );
};
