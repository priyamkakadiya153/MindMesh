import React, { useState, useEffect } from 'react';
import {
  fetchGovernancePolicies, evaluateGovernancePolicy, requestPolicyException, simulatePolicyImpact, fetchGovernanceAudit,
  PolicyDefinition, PolicyEvaluationResponse, PolicyExceptionResponse, PolicySimulationResponse, GovernanceAuditResponse
} from '../governance-policies-api';
import {
  ShieldAlert, ShieldCheck, FileCheck, AlertTriangle, Lock, Play, RefreshCw, CheckCircle2, XCircle, Search, HelpCircle, Activity
} from 'lucide-react';

interface GovernanceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const GovernanceCenter: React.FC<GovernanceCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'POLICIES' | 'EVALUATOR' | 'EXCEPTIONS' | 'SIMULATOR' | 'AUDIT'>('POLICIES');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [policies, setPolicies] = useState<PolicyDefinition[]>([]);

  // Evaluator state
  const [evalActionInput, setEvalActionInput] = useState<string>('EXTERNAL_AI_PROCESSING');
  const [evalClassificationInput, setEvalClassificationInput] = useState<string>('Confidential');
  const [evalBypassAttempt, setEvalBypassAttempt] = useState<boolean>(false);
  const [evalResult, setEvalResult] = useState<PolicyEvaluationResponse | null>(null);

  // Exception state
  const [exceptionJustification, setExceptionJustification] = useState<string>('Temporary security exception for SOC2 release audit');
  const [exceptionResult, setExceptionResult] = useState<PolicyExceptionResponse | null>(null);

  // Simulator state
  const [proposedRuleInput, setProposedRuleInput] = useState<string>('Prohibit external AI model processing for all internal backend source code');
  const [simulationResult, setSimulationResult] = useState<PolicySimulationResponse | null>(null);

  // Audit state
  const [auditData, setAuditData] = useState<GovernanceAuditResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadPolicies = async () => {
    setIsLoading(true);
    try {
      const data = await fetchGovernancePolicies(searchQuery, categoryFilter, token);
      setPolicies(data);
    } catch (err) {
      console.error('Failed to load governance policies:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAudit = async () => {
    try {
      const data = await fetchGovernanceAudit(token);
      setAuditData(data);
    } catch (err) {
      console.error('Failed to load governance audit:', err);
    }
  };

  useEffect(() => {
    loadPolicies();
    loadAudit();
  }, [searchQuery, categoryFilter, token]);

  const handleEvaluatePolicy = async () => {
    setIsLoading(true);
    try {
      const res = await evaluateGovernancePolicy(
        evalActionInput,
        evalClassificationInput,
        'doc-confidential-spec-99',
        { attempting_bypass: evalBypassAttempt },
        token
      );
      setEvalResult(res);
      setActionMessage(`Policy Evaluation result: ${res.decision} (${res.reason}).`);
    } catch (err) {
      console.error('Policy evaluation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestException = async () => {
    setIsLoading(true);
    try {
      const res = await requestPolicyException('pol-ai-confidential-01', exceptionJustification, 24, token);
      setExceptionResult(res);
      setActionMessage(`Temporary Exception granted: ${res.exception_id} (Expires: ${new Date(res.expires_at).toLocaleTimeString()}).`);
    } catch (err) {
      console.error('Exception request failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulateImpact = async () => {
    setIsLoading(true);
    try {
      const res = await simulatePolicyImpact(proposedRuleInput, token);
      setSimulationResult(res);
      setActionMessage(`Policy Simulation complete: ${res.impact_warning}`);
    } catch (err) {
      console.error('Policy simulation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                ENTERPRISE GOVERNANCE ENGINE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Deterministic Precedence & Guardrails</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <ShieldAlert className="w-7 h-7 text-indigo-400" />
              <span>MindMesh Policy Control & Governance Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Centralized organizational rules governing users, AI models, agents, workflows, connectors, and data handling under strict context integrity.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Active Policies</span>
              <span className="text-lg font-black text-indigo-400">{policies.length}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Open Violations</span>
              <span className="text-lg font-black text-amber-400">{auditData?.compliance_indicators.open_violations_count || 0}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('POLICIES')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'POLICIES' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Active Governance Policies
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('EVALUATOR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EVALUATOR' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Pre-Action Evaluator
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('EXCEPTIONS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EXCEPTIONS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Temporary Exceptions
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('SIMULATOR')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'SIMULATOR' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Policy Simulation
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('AUDIT')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'AUDIT' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Audit & Compliance
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-indigo-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'POLICIES' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search policies..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white focus:outline-none"
              />
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-xs text-slate-400 font-mono">Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
              >
                <option value="">All Categories</option>
                <option value="AI">AI Governance</option>
                <option value="Workflow">Workflow Controls</option>
                <option value="Retention">Data Retention</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {policies.map(pol => (
              <div key={pol.policy_id} className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl space-y-3 backdrop-blur-md flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800/60 uppercase">{pol.category}</span>
                    <span className="text-[9px] font-mono text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{pol.status}</span>
                  </div>
                  <h3 className="text-sm font-bold text-white mt-1">{pol.name}</h3>
                  <p className="text-xs text-slate-400">{pol.description}</p>
                  <div className="text-[10px] font-mono text-slate-500 pt-1">
                    • Precedence Rank: #{pol.precedence} (Scope: {pol.scope})
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between">
                  <span className="text-[9px] font-mono text-amber-400 font-bold">Effect: {pol.effect}</span>
                  <span className="text-[9px] font-mono text-slate-500">v{pol.version}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'EVALUATOR' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Pre-Action Policy Evaluation Engine</h3>
            <p className="text-xs text-slate-400 mt-1">Evaluates proposed tool calls, agent execution, external AI processing, and data exports prior to execution.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Target Action:</label>
              <select
                value={evalActionInput}
                onChange={(e) => setEvalActionInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              >
                <option value="EXTERNAL_AI_PROCESSING">External AI Processing</option>
                <option value="DATA_EXPORT">Data Export</option>
                <option value="TOOL_CALL">High-Impact Tool Call</option>
              </select>
            </div>

            <div>
              <label className="text-slate-300 font-bold block mb-1">Data Classification:</label>
              <select
                value={evalClassificationInput}
                onChange={(e) => setEvalClassificationInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              >
                <option value="Confidential">Confidential</option>
                <option value="Restricted">Restricted</option>
                <option value="Internal">Internal</option>
                <option value="Public">Public</option>
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <input
              type="checkbox"
              id="bypassCheck"
              checked={evalBypassAttempt}
              onChange={(e) => setEvalBypassAttempt(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-indigo-600"
            />
            <label htmlFor="bypassCheck" className="text-slate-400">Simulate unauthorized policy bypass attempt</label>
          </div>

          <button
            type="button"
            onClick={handleEvaluatePolicy}
            disabled={isLoading}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
          >
            <Play className="w-4 h-4" />
            <span>Evaluate Pre-Action Policy</span>
          </button>

          {evalResult && (
            <div className={`p-4 rounded-2xl space-y-2 text-xs border ${
              evalResult.decision === 'DENIED' ? 'bg-red-950/40 border-red-800/60 text-red-200' :
              evalResult.decision === 'APPROVAL_REQUIRED' ? 'bg-amber-950/40 border-amber-800/60 text-amber-200' :
              'bg-emerald-950/40 border-emerald-800/60 text-emerald-200'
            }`}>
              <span className="font-bold font-mono block uppercase">Decision: {evalResult.decision} ({evalResult.result_code})</span>
              <p>• Reason: {evalResult.reason}</p>
              <p>• Matched Policies: {evalResult.matched_policies.join(', ') || 'None'}</p>
              <p>• Required Controls: {evalResult.required_controls.join(', ') || 'None'}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'EXCEPTIONS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Temporary Policy Exception Manager</h3>
            <p className="text-xs text-slate-400 mt-1">Grants temporary, narrowly-scoped policy exceptions with explicit expiration timestamps.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Justification:</label>
              <input
                type="text"
                value={exceptionJustification}
                onChange={(e) => setExceptionJustification(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleRequestException}
              disabled={isLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <FileCheck className="w-4 h-4" />
              <span>Grant 24-Hour Exception</span>
            </button>
          </div>

          {exceptionResult && (
            <div className="p-4 bg-slate-950 border border-emerald-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-emerald-400 font-mono block uppercase">Exception Granted: {exceptionResult.exception_id}</span>
              <p className="text-slate-300">• Granted To: {exceptionResult.granted_to}</p>
              <p className="text-slate-300">• Expires At: {new Date(exceptionResult.expires_at).toLocaleString()}</p>
              <p className="text-amber-400 font-mono font-bold">• Scope: Temporary & Non-Propagating</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'SIMULATOR' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Policy Simulation & Impact Analysis Engine</h3>
            <p className="text-xs text-slate-400 mt-1">Simulates proposed policy rules in dry-run monitor mode without altering production state.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Proposed Rule Definition:</label>
              <textarea
                value={proposedRuleInput}
                onChange={(e) => setProposedRuleInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleSimulateImpact}
              disabled={isLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Simulate Policy Impact</span>
            </button>
          </div>

          {simulationResult && (
            <div className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-amber-400 font-mono block uppercase">Simulation Result: {simulationResult.mode}</span>
              <p className="text-slate-200 font-bold">• {simulationResult.impact_warning}</p>
              <p className="text-slate-300">• Affected Workflows: {simulationResult.affected_entities.active_workflows_blocked} | Agents: {simulationResult.affected_entities.agents_affected}</p>
              <p className="text-emerald-400 font-bold">• Estimated Impact: {simulationResult.estimated_compliance_shift}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'AUDIT' && auditData && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Governance Audit & Compliance Indicators</h3>
            <p className="text-xs text-slate-400 mt-1">Complete audit trail of policy evaluations, violations, and exceptions.</p>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
            <span className="font-bold text-indigo-400 font-mono block uppercase">Compliance Indicators: {auditData.compliance_indicators.compliance_status}</span>
            {auditData.violations.map(v => (
              <div key={v.violation_id} className="p-3 bg-red-950/30 border border-red-800/60 rounded-xl text-slate-200 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-red-400 font-mono">Violation: {v.violation_id}</span>
                  <span className="text-[9px] font-mono text-red-400 font-bold bg-red-950 px-2 py-0.5 rounded border border-red-800/60">{v.severity}</span>
                </div>
                <p>• Actor: {v.actor} ({v.action}) on {v.resource}</p>
                <p className="text-amber-400 font-mono font-bold">• Response Action: {v.response_action}</p>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
