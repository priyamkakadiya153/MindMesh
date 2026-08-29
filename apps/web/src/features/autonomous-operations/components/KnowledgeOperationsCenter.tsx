import React, { useState, useEffect } from 'react';
import {
  fetchOperationsHealth, fetchDetectedIssues, fetchKnowledgeDigest, fetchAutomationRules,
  createAutomationRule, toggleAutomationRule, triggerReprocessEntity, triggerMaintenanceReindex,
  OperationsHealthResponse, DetectedIssuesResponse, KnowledgeDigestResponse, AutomationRule
} from '../autonomous-operations-api';
import {
  Activity, ShieldAlert, Zap, RefreshCw, AlertTriangle, FileText, CheckCircle2, Info, Layers, Bell, ArrowRight, CornerDownRight, Play, Pause
} from 'lucide-react';

interface KnowledgeOperationsCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const KnowledgeOperationsCenter: React.FC<KnowledgeOperationsCenterProps> = ({
  initialProjectId = 'proj-auth-id',
  token
}) => {
  const [health, setHealth] = useState<OperationsHealthResponse | null>(null);
  const [issuesData, setIssuesData] = useState<DetectedIssuesResponse | null>(null);
  const [digest, setDigest] = useState<KnowledgeDigestResponse | null>(null);
  const [rules, setRules] = useState<AutomationRule[]>([]);
  const [newRuleName, setNewRuleName] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadAllData = async () => {
    setIsLoading(true);
    try {
      const [hRes, iRes, dRes, rRes] = await Promise.all([
        fetchOperationsHealth(token).catch(() => null),
        fetchDetectedIssues(initialProjectId, token).catch(() => null),
        fetchKnowledgeDigest(token).catch(() => null),
        fetchAutomationRules(token).catch(() => [])
      ]);
      if (hRes) setHealth(hRes);
      if (iRes) setIssuesData(iRes);
      if (dRes) setDigest(dRes);
      if (rRes) setRules(rRes);
    } catch (err) {
      console.error('Failed to load Knowledge Operations data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, [initialProjectId, token]);

  const handleToggleRule = async (ruleId: string, currentEnabled: bool) => {
    try {
      await toggleAutomationRule(ruleId, !currentEnabled, token);
      loadAllData();
    } catch (err) {
      console.error('Failed to toggle rule:', err);
    }
  };

  const handleCreateRule = async () => {
    if (!newRuleName.strip && !newRuleName) return;
    try {
      await createAutomationRule(newRuleName, 'DECISION_CHANGED', 'Authentication Project', 'NOTIFY_FOLLOWER', token);
      setNewRuleName('');
      loadAllData();
    } catch (err) {
      console.error('Failed to create rule:', err);
    }
  };

  const handleReindex = async () => {
    try {
      await triggerMaintenanceReindex(token);
      loadAllData();
    } catch (err) {
      console.error('Failed maintenance reindex:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Flagship Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                AUTONOMOUS KNOWLEDGE OPERATIONS
              </span>
              {health && (
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                  <Activity className="w-3 h-3" />
                  <span>Operations {health.overall_status}</span>
                </span>
              )}
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Zap className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Operations Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Continuous memory monitoring, automated risk detection, knowledge freshness auditing, and user-configured safe policy automation.
            </p>
          </div>

          <button
            type="button"
            onClick={handleReindex}
            className="px-4 py-2 rounded-2xl bg-slate-800 hover:bg-slate-700 text-indigo-400 font-bold text-xs shadow-md transition-all flex items-center space-x-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Maintenance Reindex</span>
          </button>
        </div>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Detected Issues & Project Risk Signals */}
        <div className="md:col-span-2 space-y-5">
          
          {/* Detected Knowledge Issues */}
          {issuesData && (
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>Detected Knowledge Issues ({issuesData.total_issues})</span>
                </h3>
                <span className="text-[9px] font-mono text-slate-500">Continuous Monitoring</span>
              </div>

              <div className="space-y-3">
                {issuesData.issues.map((issue) => (
                  <div
                    key={issue.id}
                    className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded uppercase ${
                        issue.severity === 'CRITICAL'
                          ? 'bg-rose-950 text-rose-400 border border-rose-800/60'
                          : issue.severity === 'IMPORTANT'
                          ? 'bg-amber-950 text-amber-400 border border-amber-800/60'
                          : 'bg-indigo-950 text-indigo-400'
                      }`}>
                        {issue.severity}: {issue.issue_type}
                      </span>
                    </div>

                    <h4 className="font-bold text-xs text-white">{issue.title}</h4>
                    <p className="text-[11px] text-slate-300">{issue.description}</p>
                    
                    <div className="flex items-center justify-between pt-1 border-t border-slate-800/80 text-[10px] font-mono">
                      <span className="text-slate-500">Affected: {issue.affected_entity}</span>
                      <button
                        type="button"
                        className="text-indigo-400 hover:text-white font-bold bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                      >
                        {issue.suggested_action}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Project Risk Synthesis */}
          {issuesData && issuesData.project_risks.length > 0 && (
            <div className="bg-slate-900/80 border border-rose-900/40 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <h4 className="text-xs font-bold text-white">Project Release Risk Signals</h4>
              </div>

              {issuesData.project_risks.map((risk) => (
                <div key={risk.risk_id} className="p-3 bg-slate-950 rounded-xl border border-slate-800 space-y-1.5 text-xs">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono font-bold text-rose-400 bg-rose-950 px-2 py-0.5 rounded uppercase">
                      {risk.severity}: {risk.project_name}
                    </span>
                  </div>
                  <h5 className="font-bold text-slate-100 text-[11px]">{risk.title}</h5>
                  <p className="text-[10px] text-slate-400">{risk.recommendation}</p>
                </div>
              ))}
            </div>
          )}

        </div>

        {/* Right Col: User-Configured Policy Automations & Daily Digest */}
        <div className="space-y-4">
          
          {/* Automation Policy Rules */}
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <h4 className="text-xs font-bold text-white flex items-center space-x-2">
                <Zap className="w-4 h-4 text-indigo-400" />
                <span>Safe Automation Policies ({rules.length})</span>
              </h4>
            </div>

            <div className="space-y-2 font-mono text-xs">
              {rules.map((rule) => (
                <div key={rule.rule_id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-slate-200">{rule.rule_name}</span>
                    <button
                      type="button"
                      onClick={() => handleToggleRule(rule.rule_id, rule.is_enabled)}
                      className={`px-2 py-0.5 rounded text-[9px] font-bold transition-all ${
                        rule.is_enabled ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {rule.is_enabled ? 'ENABLED' : 'PAUSED'}
                    </button>
                  </div>
                  <span className="text-[9px] text-slate-500 block">{rule.trigger_event} → {rule.action_name}</span>
                </div>
              ))}
            </div>

            {/* Create Rule Input */}
            <div className="flex items-center space-x-1.5 pt-2 border-t border-slate-800">
              <input
                type="text"
                value={newRuleName}
                onChange={(e) => setNewRuleName(e.target.value)}
                placeholder="New rule name (e.g. 'Decision Changed Notification')"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-[11px] text-white focus:outline-none"
              />
              <button
                type="button"
                onClick={handleCreateRule}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex-shrink-0"
              >
                Add Rule
              </button>
            </div>
          </div>

          {/* Daily Digest Preview */}
          {digest && (
            <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
              <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                <h4 className="text-xs font-bold text-white">Daily Memory Digest ({digest.digest_date})</h4>
              </div>

              <div className="space-y-2 text-xs">
                {digest.important_changes.map((ch, idx) => (
                  <div key={idx} className="p-2 bg-slate-950 border border-slate-800 rounded-xl space-y-0.5">
                    <h5 className="font-bold text-slate-200 text-[11px]">{ch.title}</h5>
                    <p className="text-[10px] text-slate-400">{ch.summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
};
