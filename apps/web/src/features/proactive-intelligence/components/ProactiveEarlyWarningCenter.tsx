import React, { useState, useEffect } from 'react';
import {
  fetchProactiveSignals, manageSignalStatus, runWhatIfScenario, fetchProactiveBriefing,
  ProactiveSignalsResponse, WhatIfResponse, BriefingResponse, ProactiveSignal
} from '../proactive-intelligence-api';
import {
  AlertTriangle, ShieldAlert, CheckCircle2, BellOff, ArrowRight, Activity, Zap, Play, Sun, Layers, HelpCircle
} from 'lucide-react';

interface ProactiveEarlyWarningCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ProactiveEarlyWarningCenter: React.FC<ProactiveEarlyWarningCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'EARLY_WARNING_FEED' | 'WHAT_IF_SIMULATOR' | 'MORNING_BRIEFING'>('EARLY_WARNING_FEED');
  const [signalsRes, setSignalsRes] = useState<ProactiveSignalsResponse | null>(null);
  const [briefingRes, setBriefingRes] = useState<BriefingResponse | null>(null);
  const [whatIfRes, setWhatIfRes] = useState<WhatIfResponse | null>(null);
  
  const [scenarioDelayDays, setScenarioDelayDays] = useState<number>(3);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const sig = await fetchProactiveSignals(initialProjectId, token);
      setSignalsRes(sig);
      const br = await fetchProactiveBriefing('MORNING', token);
      setBriefingRes(br);
    } catch (err) {
      console.error('Failed to load proactive center data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleManageSignal = async (signalId: string, action: 'ACKNOWLEDGE' | 'SNOOZE' | 'RESOLVE') => {
    try {
      await manageSignalStatus(signalId, action, undefined, token);
      setActionMessage(`Signal '${signalId}' status updated to ${action}D.`);
      loadData();
    } catch (err) {
      console.error('Signal management failed:', err);
    }
  };

  const handleRunWhatIf = async () => {
    setIsLoading(true);
    try {
      const res = await runWhatIfScenario('Dependency Delay Impact Analysis', { delay_days: scenarioDelayDays }, token);
      setWhatIfRes(res);
      setActionMessage(`What-If Simulation Completed: ${res.side_effect_guarantee}`);
    } catch (err) {
      console.error('What-If simulation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950/80 to-slate-900 border border-amber-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-amber-400 px-2.5 py-0.5 bg-amber-950 rounded border border-amber-800/60">
                PROACTIVE INTELLIGENCE & EARLY WARNING SYSTEM
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Zap className="w-3 h-3" />
                <span>Zero Alert Spam Policy</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <AlertTriangle className="w-7 h-7 text-amber-400" />
              <span>Early Warning & Predictive Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Surfaces upcoming risks, bottlenecks, knowledge decay, and decision pressures before they become problems.
            </p>
          </div>

          {signalsRes && (
            <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Active Signals</span>
                <span className="text-lg font-black text-amber-400">{signalsRes.total_active_signals}</span>
              </div>
              <div className="h-8 w-px bg-slate-800" />
              <div className="text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">System Status</span>
                <span className="text-xs font-mono font-bold text-emerald-400">HEALTHY</span>
              </div>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('EARLY_WARNING_FEED')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EARLY_WARNING_FEED' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Early Warning Feed
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('WHAT_IF_SIMULATOR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'WHAT_IF_SIMULATOR' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            What-If Simulator
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('MORNING_BRIEFING')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'MORNING_BRIEFING' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Morning Briefing
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-amber-950/80 border border-amber-800/60 rounded-2xl text-xs text-amber-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-amber-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'EARLY_WARNING_FEED' && signalsRes && (
        <div className="space-y-4">
          {signalsRes.detected_signals.map((sig: ProactiveSignal) => (
            <div key={sig.signal_id} className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                    sig.severity === 'HIGH' ? 'bg-red-950 text-red-400 border-red-800/60' :
                    sig.severity === 'MEDIUM' ? 'bg-amber-950 text-amber-400 border-amber-800/60' : 'bg-slate-950 text-slate-400 border-slate-800'
                  }`}>
                    {sig.severity} SEVERITY
                  </span>
                  <span className="text-[9px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 uppercase">{sig.signal_type}</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">Time Horizon: {sig.explanation.time_horizon}</span>
              </div>

              <div>
                <h3 className="text-base font-bold text-white">{sig.title}</h3>
                <p className="text-xs text-slate-300 mt-1">{sig.explanation.what}</p>
              </div>

              {/* Evidence Chain */}
              <div className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
                <span className="text-[10px] font-mono font-bold text-slate-400 uppercase">Supporting Evidence & Impact</span>
                <p className="text-slate-300">• <strong className="text-white">Why:</strong> {sig.explanation.why}</p>
                <p className="text-slate-300">• <strong className="text-white">Impact:</strong> {sig.explanation.impact}</p>
                <p className="text-slate-300">• <strong className="text-white">Recommended Action:</strong> {sig.explanation.what_can_be_done}</p>
              </div>

              {/* Signal Controls */}
              <div className="flex items-center space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => handleManageSignal(sig.signal_id, 'ACKNOWLEDGE')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold text-slate-200"
                >
                  Acknowledge
                </button>
                <button
                  type="button"
                  onClick={() => handleManageSignal(sig.signal_id, 'SNOOZE')}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-bold text-amber-300 flex items-center space-x-1"
                >
                  <BellOff className="w-3.5 h-3.5" />
                  <span>Snooze</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleManageSignal(sig.signal_id, 'RESOLVE')}
                  className="px-3 py-1.5 bg-emerald-950 hover:bg-emerald-900 border border-emerald-800/60 rounded-xl text-xs font-bold text-emerald-300 flex items-center space-x-1"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Mark Resolved</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {activeTab === 'WHAT_IF_SIMULATOR' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">What-If Scenario Simulator</h3>
            <p className="text-xs text-slate-400 mt-1">Simulate hypothetical schedule or dependency changes without mutating production data.</p>
          </div>

          <div className="space-y-4 text-xs">
            <div className="flex items-center space-x-3">
              <label className="text-slate-300 font-bold">Simulate Dependency Delay (Days):</label>
              <input
                type="number"
                min={1}
                max={30}
                value={scenarioDelayDays}
                onChange={(e) => setScenarioDelayDays(Number(e.target.value))}
                className="w-20 bg-slate-950 border border-slate-800 rounded-xl p-2 text-white font-mono focus:outline-none"
              />
              <button
                type="button"
                onClick={handleRunWhatIf}
                disabled={isLoading}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-500 rounded-xl text-white font-bold text-xs"
              >
                Run Simulation
              </button>
            </div>
          </div>

          {whatIfRes && (
            <div className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl space-y-3 text-xs">
              <span className="font-bold text-amber-400 block font-mono text-sm">Simulated Impact Report</span>
              <p className="text-slate-300">• Mode: {whatIfRes.mode}</p>
              <p className="text-slate-300">• Affected Tasks: <strong>{whatIfRes.simulated_outcomes.affected_tasks}</strong></p>
              <p className="text-slate-300">• Projected Milestone Delay: <strong>+{whatIfRes.simulated_outcomes.projected_milestone_delay_days} Days</strong></p>
              <p className="text-slate-300">• Risk Delta: <strong className="text-red-400">{whatIfRes.simulated_outcomes.risk_score_delta}</strong></p>
              <span className="text-[10px] font-mono text-emerald-400 block font-bold pt-1">{whatIfRes.side_effect_guarantee}</span>
            </div>
          )}
        </div>
      )}

      {activeTab === 'MORNING_BRIEFING' && briefingRes && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Personal Morning Briefing</h3>
              <p className="text-xs text-slate-400 mt-1">Generated at {new Date(briefingRes.generated_at).toLocaleTimeString()}</p>
            </div>
            <Sun className="w-6 h-6 text-amber-400" />
          </div>

          <div className="space-y-3 text-xs">
            <span className="font-bold text-white font-mono uppercase block">Key Focus Items</span>
            {briefingRes.summary_bullet_points.map((pt, idx) => (
              <div key={idx} className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200">
                • {pt}
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
