import React, { useState, useEffect } from 'react';
import {
  checkAuthorization, checkAIPolicy, revokeMemberAccess, scanSecrets, fetchSecurityAuditTimeline, fetchSecurityStatus,
  SecurityAuditItem, SecurityStatusResponse, AIPolicyCheckResponse
} from '../security-governance-api';
import {
  Lock, Shield, UserX, Key, EyeOff, ShieldAlert, CheckCircle, AlertTriangle, FileLock, Terminal, Server, Layers
} from 'lucide-react';

interface ZeroTrustSecurityCenterProps {
  initialOrgId?: string;
  initialWorkspaceId?: string;
  token?: string;
}

export const ZeroTrustSecurityCenter: React.FC<ZeroTrustSecurityCenterProps> = ({
  initialOrgId = '7bae4f27-6499-4bcb-9380-caea3a9f8132',
  initialWorkspaceId = '6d25a626-a2c5-47ec-9107-88fdf97ee095',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'DASHBOARD' | 'AI_BOUNDARY' | 'REVOCATION' | 'AUDIT'>('DASHBOARD');
  const [secStatus, setSecStatus] = useState<SecurityStatusResponse | null>(null);
  const [auditTimeline, setAuditTimeline] = useState<SecurityAuditItem[]>([]);
  const [aiCheckResult, setAiCheckResult] = useState<AIPolicyCheckResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [secretScanResult, setSecretScanResult] = useState<any | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [statusRes, timelineRes] = await Promise.all([
        fetchSecurityStatus(token),
        fetchSecurityAuditTimeline(token)
      ]);
      setSecStatus(statusRes);
      setAuditTimeline(timelineRes);
    } catch (err) {
      console.error('Failed to load zero trust security center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialOrgId, initialWorkspaceId, token]);

  const handleTestAIPolicy = async (provider: string) => {
    try {
      const sampleContext = [
        { type: 'Document', title: 'Public OAuth Architecture Spec', visibility: 'workspace' },
        { type: 'DirectMessage', title: 'Private DM with Security Officer', visibility: 'private_dm' }
      ];
      const res = await checkAIPolicy(provider, sampleContext, token);
      setAiCheckResult(res);
      setActionMessage(`AI Policy Checked for provider '${provider}'. Enforced DM Privacy: ${res.dm_privacy_enforced}`);
    } catch (err) {
      console.error('Failed AI policy check:', err);
    }
  };

  const handleRevokeMember = async () => {
    try {
      const dummyTargetId = '4daae1ef-24ca-4f78-8e36-19953ab330d7';
      const res = await revokeMemberAccess(dummyTargetId, initialWorkspaceId, token);
      setActionMessage(`Member '${dummyTargetId}' access revoked across REST, WebSockets, Vector DB, and Search.`);
      loadData();
    } catch (err) {
      console.error('Failed member revocation:', err);
    }
  };

  const handleScanSecrets = async () => {
    try {
      const res = await scanSecrets(token);
      setSecretScanResult(res);
      setActionMessage(`Secret Scan completed. Status: ${res.bundle_status}`);
    } catch (err) {
      console.error('Failed secret scan:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-rose-950/80 to-slate-900 border border-rose-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-rose-400 px-2.5 py-0.5 bg-rose-950 rounded border border-rose-800/60">
                ZERO-TRUST SECURITY, PRIVACY & DATA GOVERNANCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <Lock className="w-3 h-3" />
                <span>Server-Side Policy Enforcement</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Shield className="w-7 h-7 text-rose-400" />
              <span>Zero-Trust Security Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Ensures trusted information, AI, files, conversations, knowledge, and actions are NEVER exposed outside authorized boundaries.
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('DASHBOARD')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'DASHBOARD' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Dashboard
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('AI_BOUNDARY')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'AI_BOUNDARY' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              AI Data Policy
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('REVOCATION')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'REVOCATION' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Revocation
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('AUDIT')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'AUDIT' ? 'bg-rose-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Security Audit
            </button>
          </div>
        </div>

        {/* Security Status Counters Bar */}
        {secStatus && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-800/60">
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Tenant Isolation</span>
              <span className="text-xs font-black text-emerald-400">{secStatus.organization_isolation}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">DM Privacy</span>
              <span className="text-xs font-black text-indigo-400">{secStatus.dm_privacy}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">AI Data Boundary</span>
              <span className="text-xs font-black text-amber-400">{secStatus.ai_data_boundary}</span>
            </div>
            <div className="bg-slate-950/80 p-2.5 rounded-2xl border border-slate-800 text-center">
              <span className="text-[9px] font-mono text-slate-400 uppercase block">Secret Scanning</span>
              <span className="text-xs font-black text-rose-400">{secStatus.secret_scanning}</span>
            </div>
          </div>
        )}
      </div>

      {actionMessage && (
        <div className="p-3 bg-rose-950/80 border border-rose-800/60 rounded-2xl text-xs text-rose-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'DASHBOARD' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Server-Side Security Policies & Secret Scan</h3>
              <p className="text-xs text-slate-400 mt-1">Evaluates authorization boundaries across Organization, Workspace, and Resource levels.</p>
            </div>
            <button
              type="button"
              onClick={handleScanSecrets}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <Key className="w-4 h-4" />
              <span>Scan System Secrets</span>
            </button>
          </div>

          {secretScanResult && (
            <div className="p-4 bg-slate-950 border border-rose-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-emerald-400 block font-mono">Secret Scan Status: {secretScanResult.bundle_status}</span>
              <p className="text-slate-300">• <strong className="text-slate-100">Secrets Scanned:</strong> {secretScanResult.secrets_scanned}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Exposed API Keys:</strong> {secretScanResult.exposed_api_keys}</p>
              <p className="text-slate-300">• <strong className="text-slate-100">Exposed DB Passwords:</strong> {secretScanResult.exposed_db_passwords}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'AI_BOUNDARY' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">AI Provider Data Boundary & Context Minimization</h3>
            <p className="text-xs text-slate-400 mt-1">Enforces policy checks and strips private DM context before sending data to AI providers.</p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={() => handleTestAIPolicy('Gemini 1.5 Pro')}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs"
            >
              Test Gemini Policy
            </button>
            <button
              type="button"
              onClick={() => handleTestAIPolicy('external_untrusted')}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-slate-300 font-bold text-xs"
            >
              Test Untrusted Provider Policy
            </button>
          </div>

          {aiCheckResult && (
            <div className="p-5 bg-slate-950 border border-slate-800 rounded-3xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-white text-sm">Provider: {aiCheckResult.provider}</span>
                <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                  aiCheckResult.policy_status === 'ALLOWED' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-red-950 text-red-400 border-red-800/60'
                }`}>{aiCheckResult.policy_status}</span>
              </div>

              <div className="p-3 bg-slate-900 rounded-2xl space-y-1">
                <p className="text-slate-300">• <strong className="text-indigo-400">Original Context Items:</strong> {aiCheckResult.original_items_count}</p>
                <p className="text-slate-300">• <strong className="text-indigo-400">Sanitized Context Items:</strong> {aiCheckResult.sanitized_items_count}</p>
                <p className="text-slate-300">• <strong className="text-indigo-400">DM Privacy Enforced:</strong> {aiCheckResult.dm_privacy_enforced ? 'YES (Private DM Excluded)' : 'NO'}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'REVOCATION' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Immediate Member Access Revocation Engine</h3>
              <p className="text-xs text-slate-400 mt-1">Revokes access immediately across REST APIs, WebSockets, Vector DBs, Search Indexes, and AI Context.</p>
            </div>
            <button
              type="button"
              onClick={handleRevokeMember}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 rounded-2xl text-white font-bold text-xs shadow-lg flex items-center space-x-1.5"
            >
              <UserX className="w-4 h-4" />
              <span>Simulate Member Revocation</span>
            </button>
          </div>
        </div>
      )}

      {activeTab === 'AUDIT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono">Immutable Security Event Timeline</h3>
          <div className="space-y-2">
            {auditTimeline.map(aud => (
              <div key={aud.event_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-white">{aud.event_type}</span>
                  <span className="text-slate-400 ml-2">by {aud.actor}</span>
                  <p className="text-[10px] text-slate-400 mt-0.5">{aud.details}</p>
                </div>
                <span className="text-[9px] font-mono text-slate-500">{aud.timestamp}</span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
