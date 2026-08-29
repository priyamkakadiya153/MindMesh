import React, { useState, useEffect } from 'react';
import {
  fetchFrameworksAndControls, testComplianceControl, collectComplianceEvidence, remediateFinding, acceptResidualRisk, fetchAuditReadiness,
  FrameworksAndControlsResponse, TestControlResponse, EvidenceCollectResponse, RemediateFindingResponse, AcceptRiskResponse, AuditReadinessResponse
} from '../compliance-intelligence-api';
import {
  ShieldCheck, CheckCircle2, AlertTriangle, FileText, Play, RefreshCw, Lock, Award, Package, Activity, Search, ShieldAlert
} from 'lucide-react';

interface ComplianceAssuranceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ComplianceAssuranceCenter: React.FC<ComplianceAssuranceCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'FRAMEWORKS' | 'TESTING' | 'EVIDENCE' | 'REMEDIATION' | 'RISKS' | 'READINESS'>('FRAMEWORKS');
  const [frameworksData, setFrameworksData] = useState<FrameworksAndControlsResponse | null>(null);

  // Control Test state
  const [selectedControlId, setSelectedControlId] = useState<string>('ctrl-sec-01');
  const [simulateFailureCheck, setSimulateFailureCheck] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<TestControlResponse | null>(null);

  // Evidence state
  const [evidencePayloadInput, setEvidencePayloadInput] = useState<string>('Audit Event Log: SOC2 Type II Multi-Factor Authorization Check for Production AI Model');
  const [evidenceResult, setEvidenceResult] = useState<EvidenceCollectResponse | null>(null);

  // Remediation state
  const [findingTitleInput, setFindingTitleInput] = useState<string>('Production AI Model Authorization Bypass');
  const [verificationPassedCheck, setVerificationPassedCheck] = useState<boolean>(true);
  const [remediationResult, setRemediationResult] = useState<RemediateFindingResponse | null>(null);

  // Risk state
  const [riskTitleInput, setRiskTitleInput] = useState<string>('Residual Risk: External AI Access to Non-Confidential Specs');
  const [riskAcceptanceResult, setRiskAcceptanceResult] = useState<AcceptRiskResponse | null>(null);

  // Readiness state
  const [missingEvidenceCheck, setMissingEvidenceCheck] = useState<boolean>(false);
  const [readinessResult, setReadinessResult] = useState<AuditReadinessResponse | null>(null);

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadFrameworks = async () => {
    setIsLoading(true);
    try {
      const data = await fetchFrameworksAndControls(token);
      setFrameworksData(data);
    } catch (err) {
      console.error('Failed to load frameworks & controls:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadReadiness = async () => {
    try {
      const data = await fetchAuditReadiness(missingEvidenceCheck, token);
      setReadinessResult(data);
    } catch (err) {
      console.error('Failed to load audit readiness:', err);
    }
  };

  useEffect(() => {
    loadFrameworks();
  }, [token]);

  useEffect(() => {
    loadReadiness();
  }, [missingEvidenceCheck, token]);

  const handleTestControl = async () => {
    setIsLoading(true);
    try {
      const res = await testComplianceControl(selectedControlId, 'AUTOMATED', simulateFailureCheck, token);
      setTestResult(res);
      setActionMessage(`Control test executed for '${res.control_id}': Result is ${res.result}.`);
    } catch (err) {
      console.error('Control test failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCollectEvidence = async () => {
    setIsLoading(true);
    try {
      const res = await collectComplianceEvidence(selectedControlId, 'LOG', evidencePayloadInput, token);
      setEvidenceResult(res);
      setActionMessage(`Evidence '${res.evidence_id}' collected (Hash: ${res.sha256_checksum.slice(0, 10)}...).`);
    } catch (err) {
      console.error('Collect evidence failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemediateFinding = async () => {
    setIsLoading(true);
    try {
      const res = await remediateFinding(remediationResult?.finding_id || null, findingTitleInput, 'HIGH', verificationPassedCheck, token);
      setRemediationResult(res);
      setActionMessage(`Finding '${res.finding_id}' status: ${res.status}.`);
    } catch (err) {
      console.error('Remediate finding failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAcceptRisk = async () => {
    setIsLoading(true);
    try {
      const res = await acceptResidualRisk(riskTitleInput, 'Security', 80, 24, token);
      setRiskAcceptanceResult(res);
      setActionMessage(`Risk '${res.risk_id}' accepted temporarily (Expires in 24 hours).`);
    } catch (err) {
      console.error('Accept risk failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-teal-950/80 to-slate-900 border border-teal-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-teal-400 px-2.5 py-0.5 bg-teal-950 rounded border border-teal-800/60">
                CONTINUOUS COMPLIANCE & RISK ENGINE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Evidence Provenance & Continuous Assurance</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Award className="w-7 h-7 text-teal-400" />
              <span>MindMesh Continuous Assurance & Audit Operations</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Continuously measures compliance, collects SHA-256 evidence, tests control effectiveness, coordinates finding remediation, and manages audit readiness packages.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Status</span>
              <span className="text-lg font-black text-emerald-400">{readinessResult?.overall_status || 'UNKNOWN'}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Readiness</span>
              <span className="text-lg font-black text-teal-400">{readinessResult?.readiness_score || 'ASSESSING'}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('FRAMEWORKS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'FRAMEWORKS' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Frameworks & Controls
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('TESTING')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'TESTING' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Control Testing
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('EVIDENCE')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'EVIDENCE' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Evidence Vault & Provenance
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('REMEDIATION')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'REMEDIATION' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Finding Remediation
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('RISKS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'RISKS' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Risk Register
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('READINESS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'READINESS' ? 'bg-teal-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Audit Readiness Package
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-teal-950/80 border border-teal-800/60 rounded-2xl text-xs text-teal-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-teal-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'FRAMEWORKS' && frameworksData && (
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="text-sm font-bold text-white">{frameworksData.frameworks[0].name} (v{frameworksData.frameworks[0].version})</h3>
                <p className="text-xs text-slate-400 font-mono mt-0.5">Status: {frameworksData.frameworks[0].status}</p>
              </div>
              <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">ACTIVE FRAMEWORK</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {frameworksData.controls.map(ctrl => (
                <div key={ctrl.control_id} className="bg-slate-950 border border-slate-800 p-4 rounded-2xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-teal-400 font-mono text-xs">{ctrl.control_id}</span>
                    <span className="text-[9px] font-mono text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{ctrl.status}</span>
                  </div>
                  <h4 className="text-xs font-bold text-white">{ctrl.name}</h4>
                  <p className="text-[11px] text-slate-400">{ctrl.description}</p>
                  <div className="text-[10px] font-mono text-slate-500 pt-1">
                    • Policy Mapped: {ctrl.mapped_policy_id} (Owner: {ctrl.owner})
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'TESTING' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Automated Control Testing Engine</h3>
            <p className="text-xs text-slate-400 mt-1">Runs design and operating effectiveness tests against controls.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Target Control:</label>
              <select
                value={selectedControlId}
                onChange={(e) => setSelectedControlId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              >
                <option value="ctrl-sec-01">ctrl-sec-01 (Production AI Access Control)</option>
                <option value="ctrl-ops-01">ctrl-ops-01 (Production Workflow Guardrail)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="simFailCheck"
                checked={simulateFailureCheck}
                onChange={(e) => setSimulateFailureCheck(e.target.checked)}
                className="rounded bg-slate-950 border-slate-800 text-teal-600"
              />
              <label htmlFor="simFailCheck" className="text-slate-400">Simulate control test failure & gap detection</label>
            </div>

            <button
              type="button"
              onClick={handleTestControl}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <Play className="w-4 h-4" />
              <span>Run Automated Control Test</span>
            </button>
          </div>

          {testResult && (
            <div className={`p-4 rounded-2xl space-y-2 text-xs border ${
              testResult.result === 'FAIL' ? 'bg-red-950/40 border-red-800/60 text-red-200' : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200'
            }`}>
              <span className="font-bold font-mono block uppercase">Test Result: {testResult.result} ({testResult.test_id})</span>
              <p>• Operating Effectiveness: {testResult.operating_effectiveness}</p>
              {testResult.gap_detected && (
                <p className="text-red-400 font-bold mt-1">• Gap Detected: {testResult.gap_detected.description}</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'EVIDENCE' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Evidence Vault, Checksum & Provenance</h3>
            <p className="text-xs text-slate-400 mt-1">Collects evidence, attaches source provenance, computes SHA-256 hash checksum, and tracks freshness.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Evidence Payload Content:</label>
              <textarea
                value={evidencePayloadInput}
                onChange={(e) => setEvidencePayloadInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={handleCollectEvidence}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span>Collect Evidence & Compute Hash</span>
            </button>
          </div>

          {evidenceResult && (
            <div className="p-4 bg-slate-950 border border-teal-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-teal-400 font-mono block uppercase">Evidence Collected: {evidenceResult.evidence_id}</span>
              <p className="text-slate-300">• Source: {evidenceResult.source}</p>
              <p className="text-slate-300 font-mono">• SHA-256 Checksum: {evidenceResult.sha256_checksum}</p>
              <p className="text-emerald-400 font-mono font-bold">• Freshness Status: {evidenceResult.freshness}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'REMEDIATION' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Finding Remediation & Reopening Engine</h3>
            <p className="text-xs text-slate-400 mt-1">Tracks findings, executes remediation workflows, and reopens findings automatically if verification fails.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Finding Title:</label>
              <input
                type="text"
                value={findingTitleInput}
                onChange={(e) => setFindingTitleInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="verifPassedCheck"
                checked={verificationPassedCheck}
                onChange={(e) => setVerificationPassedCheck(e.target.checked)}
                className="rounded bg-slate-950 border-slate-800 text-teal-600"
              />
              <label htmlFor="verifPassedCheck" className="text-slate-400">Remediation verification evidence passed</label>
            </div>

            <button
              type="button"
              onClick={handleRemediateFinding}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Submit Remediation & Verify</span>
            </button>
          </div>

          {remediationResult && (
            <div className={`p-4 rounded-2xl space-y-2 text-xs border ${
              remediationResult.status.includes('REOPENED') ? 'bg-red-950/40 border-red-800/60 text-red-200' : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200'
            }`}>
              <span className="font-bold font-mono block uppercase">Finding Status: {remediationResult.status} ({remediationResult.finding_id})</span>
              {remediationResult.reopened_reason ? (
                <p className="text-red-400 font-bold">• Reopened Reason: {remediationResult.reopened_reason}</p>
              ) : (
                <p className="text-emerald-400 font-bold">• Remediation Completed & Verified!</p>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'RISKS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Enterprise Risk Register & Temporary Acceptance</h3>
            <p className="text-xs text-slate-400 mt-1">Registers inherent vs residual risk and manages temporary risk acceptance with explicit expiration timestamps.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Risk Title:</label>
              <input
                type="text"
                value={riskTitleInput}
                onChange={(e) => setRiskTitleInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>

            <button
              type="button"
              onClick={handleAcceptRisk}
              disabled={isLoading}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <Lock className="w-4 h-4" />
              <span>Grant 24-Hour Temporary Risk Acceptance</span>
            </button>
          </div>

          {riskAcceptanceResult && (
            <div className="p-4 bg-slate-950 border border-amber-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-amber-400 font-mono block uppercase">Risk Registered: {riskAcceptanceResult.risk_id}</span>
              <p className="text-slate-300">• Inherent Score: {riskAcceptanceResult.inherent_score} | Residual Score: {riskAcceptanceResult.residual_score}</p>
              <p className="text-slate-300">• Granted To: {riskAcceptanceResult.acceptance_record.accepted_by}</p>
              <p className="text-amber-400 font-mono font-bold">• Expires At: {new Date(riskAcceptanceResult.acceptance_record.expires_at).toLocaleString()}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'READINESS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Audit Readiness Package Generator & Unknown State Protection</h3>
            <p className="text-xs text-slate-400 mt-1">Generates structured audit evidence packages. If evidence is missing, state is explicitly UNKNOWN (never false compliant).</p>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <input
              type="checkbox"
              id="missingEvidenceCheck"
              checked={missingEvidenceCheck}
              onChange={(e) => setMissingEvidenceCheck(e.target.checked)}
              className="rounded bg-slate-950 border-slate-800 text-teal-600"
            />
            <label htmlFor="missingEvidenceCheck" className="text-slate-400">Simulate missing/expired control evidence</label>
          </div>

          {readinessResult && (
            <div className={`p-4 rounded-2xl space-y-3 text-xs border ${
              readinessResult.overall_status === 'UNKNOWN' ? 'bg-amber-950/40 border-amber-800/60 text-amber-200' : 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200'
            }`}>
              <span className="font-bold font-mono block uppercase">Overall Audit Readiness: {readinessResult.overall_status}</span>
              {readinessResult.readiness_warning && (
                <p className="text-amber-400 font-bold">• Warning: {readinessResult.readiness_warning}</p>
              )}
              {readinessResult.audit_package && (
                <div className="p-3 bg-slate-950 border border-emerald-800/60 rounded-xl space-y-1 text-slate-200">
                  <span className="font-bold text-emerald-400 font-mono">Audit Package Generated: {readinessResult.audit_package.package_id}</span>
                  <p>• Framework: {readinessResult.audit_package.framework}</p>
                  <p>• Evidence Items Included: {readinessResult.audit_package.evidence_items_included} ({readinessResult.audit_package.control_coverage})</p>
                  <p className="font-mono text-slate-400">• Package SHA-256: {readinessResult.audit_package.package_sha256}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

    </div>
  );
};
