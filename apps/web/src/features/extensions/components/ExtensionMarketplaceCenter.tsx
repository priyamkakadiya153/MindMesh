import React, { useState, useEffect } from 'react';
import {
  fetchMarketplaceExtensions, installExtension, syncKnowledgeConnector, buildCustomAgent, revokeExtensionPermissions,
  ExtensionDefinition, InstallResponse, ConnectorSyncResponse, CustomAgentResponse, RevokePermissionResponse
} from '../extension-marketplace-api';
import {
  Store, Package, ShieldCheck, Download, RefreshCw, PlusCircle, AlertOctagon, Activity, Search, ExternalLink, CheckCircle2, Lock
} from 'lucide-react';

interface ExtensionMarketplaceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const ExtensionMarketplaceCenter: React.FC<ExtensionMarketplaceCenterProps> = ({
  initialProjectId,
  token
}) => {
  const [activeTab, setActiveTab] = useState<'MARKETPLACE' | 'INSTALLED' | 'CONNECTORS' | 'AGENT_BUILDER' | 'ADMIN_AUDIT'>('MARKETPLACE');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [extensions, setExtensions] = useState<ExtensionDefinition[]>([]);

  const [installedMap, setInstalledMap] = useState<Record<string, InstallResponse>>({});
  const [syncRes, setSyncRes] = useState<ConnectorSyncResponse | null>(null);
  const [customAgentRes, setCustomAgentRes] = useState<CustomAgentResponse | null>(null);
  const [revokeRes, setRevokeRes] = useState<RevokePermissionResponse | null>(null);

  // Agent Builder state
  const [agentNameInput, setAgentNameInput] = useState<string>('Release Risk Analyst');
  const [agentRoleInput, setAgentRoleInput] = useState<string>('Evaluates SOC2 compliance & deployment risk before release');
  const [agentInstructionInput, setAgentInstructionInput] = useState<string>('Inspect Project Alpha specs and flag any unresolved security dependencies.');

  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadMarketplace = async () => {
    setIsLoading(true);
    try {
      const data = await fetchMarketplaceExtensions(searchQuery, categoryFilter, token);
      setExtensions(data);
    } catch (err) {
      console.error('Failed to load marketplace extensions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadMarketplace();
  }, [searchQuery, categoryFilter, token]);

  const handleInstallExtension = async (extId: string) => {
    setIsLoading(true);
    try {
      const res = await installExtension(extId, token);
      setInstalledMap(prev => ({ ...prev, [extId]: res }));
      setActionMessage(`Extension '${extId}' installed & permissions granted (Status: ${res.status}).`);
    } catch (err) {
      console.error('Install extension failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncConnector = async (connectorId: string, syncMode: string) => {
    setIsLoading(true);
    try {
      const res = await syncKnowledgeConnector(connectorId, syncMode, token);
      setSyncRes(res);
      setActionMessage(`Connector '${connectorId}' sync completed (${syncMode}): ${res.items_processed} items processed, ${res.duplicates_prevented} duplicates prevented.`);
    } catch (err) {
      console.error('Sync connector failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBuildCustomAgent = async () => {
    setIsLoading(true);
    try {
      const res = await buildCustomAgent(agentNameInput, agentRoleInput, ['RISK_ASSESSMENT', 'COMPLIANCE_AUDIT'], agentInstructionInput, 'WORKSPACE', token);
      setCustomAgentRes(res);
      setActionMessage(`Custom Agent '${res.name}' published to workspace (${res.status}).`);
    } catch (err) {
      console.error('Build custom agent failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevokePermission = async (extId: string) => {
    setIsLoading(true);
    try {
      const res = await revokeExtensionPermissions(extId, 'Admin Emergency Security Disablement', token);
      setRevokeRes(res);
      setActionMessage(`Permissions revoked for '${extId}' (Status: ${res.status}).`);
    } catch (err) {
      console.error('Revoke permission failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-sky-950/80 to-slate-900 border border-sky-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-sky-400 px-2.5 py-0.5 bg-sky-950 rounded border border-sky-800/60">
                EXTENSION PLATFORM & MARKETPLACE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Permission-Scoped Plugin Ecosystem</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Store className="w-7 h-7 text-sky-400" />
              <span>MindMesh Knowledge Marketplace & Extensibility</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Safely extend MindMesh with third-party agents, tools, knowledge connectors, and custom actions under explicit permission review.
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-slate-950 p-3 rounded-2xl border border-slate-800 flex-shrink-0">
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Available Extensions</span>
              <span className="text-lg font-black text-sky-400">{extensions.length}</span>
            </div>
            <div className="h-8 w-px bg-slate-800" />
            <div className="text-center">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">Installed</span>
              <span className="text-lg font-black text-emerald-400">{Object.keys(installedMap).length}</span>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('MARKETPLACE')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'MARKETPLACE' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Marketplace Catalog
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('CONNECTORS')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'CONNECTORS' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Knowledge Connectors
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('AGENT_BUILDER')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'AGENT_BUILDER' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Custom Agent Builder
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('ADMIN_AUDIT')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
              activeTab === 'ADMIN_AUDIT' ? 'bg-sky-600 text-white' : 'text-slate-400 hover:text-white'
            }`}
          >
            Admin & Permissions
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-sky-950/80 border border-sky-800/60 rounded-2xl text-xs text-sky-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-sky-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Content */}
      {activeTab === 'MARKETPLACE' && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/80 p-4 rounded-2xl border border-slate-800">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search extensions..."
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
                <option value="Engineering">Engineering</option>
                <option value="Security">Security</option>
                <option value="Knowledge">Knowledge</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {extensions.map(ext => {
              const isInstalled = !!installedMap[ext.extension_id];
              return (
                <div key={ext.extension_id} className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl space-y-3 backdrop-blur-md flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-mono font-bold text-sky-400 bg-sky-950 px-2 py-0.5 rounded border border-sky-800/60 uppercase">{ext.type}</span>
                      <span className="text-[9px] font-mono text-emerald-400 font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 uppercase">{ext.trust_level}</span>
                    </div>
                    <h3 className="text-sm font-bold text-white mt-1">{ext.name}</h3>
                    <p className="text-xs text-slate-400">{ext.description}</p>
                    <div className="text-[10px] font-mono text-slate-500 pt-1">
                      • Publisher: {ext.publisher} (v{ext.version})
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800/60 flex items-center justify-between">
                    <span className="text-[9px] font-mono text-slate-400">Permissions: {ext.permissions_requested.length}</span>
                    {isInstalled ? (
                      <span className="text-xs font-mono font-bold text-emerald-400 flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Installed</span>
                      </span>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleInstallExtension(ext.extension_id)}
                        disabled={isLoading}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 rounded-xl text-white font-bold text-xs flex items-center space-x-1"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Install</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {activeTab === 'CONNECTORS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Knowledge Connector Synchronization & Lineage</h3>
            <p className="text-xs text-slate-400 mt-1">Bidirectional sync with external systems preserving source data lineage.</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              type="button"
              onClick={() => handleSyncConnector('ext-jira-connector-01', 'INCREMENTAL')}
              disabled={isLoading}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Trigger Incremental Jira Sync</span>
            </button>
          </div>

          {syncRes && (
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3 text-xs">
              <span className="font-bold text-sky-400 font-mono block uppercase">Sync Status: {syncRes.sync_status} ({syncRes.sync_mode})</span>
              <p className="text-slate-300">• Items Processed: {syncRes.items_processed} | Duplicates Prevented: {syncRes.duplicates_prevented}</p>
              <p className="text-slate-300">• Data Lineage Source: {syncRes.data_lineage.source}</p>

              {syncRes.conflicts_detected.length > 0 && (
                <div className="pt-2 space-y-2">
                  <span className="font-bold text-amber-400 font-mono block uppercase">Sync Conflicts Detected & Resolved</span>
                  {syncRes.conflicts_detected.map(c => (
                    <div key={c.conflict_id} className="p-2.5 bg-amber-950/30 border border-amber-800/60 rounded-xl text-slate-200">
                      <p>• External ({c.external_id}): {c.external_value}</p>
                      <p>• MindMesh ({c.mindmesh_id}): {c.mindmesh_value}</p>
                      <p className="text-emerald-400 font-bold mt-1">• Resolution Policy: {c.resolution}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {activeTab === 'AGENT_BUILDER' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Custom Agent Builder Pipeline</h3>
            <p className="text-xs text-slate-400 mt-1">Define role, capabilities, instructions, permissions, and publish scope safely.</p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-300 font-bold block mb-1">Agent Name:</label>
              <input
                type="text"
                value={agentNameInput}
                onChange={(e) => setAgentNameInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-300 font-bold block mb-1">Agent Role:</label>
              <input
                type="text"
                value={agentRoleInput}
                onChange={(e) => setAgentRoleInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <div>
              <label className="text-slate-300 font-bold block mb-1">System Instructions:</label>
              <textarea
                value={agentInstructionInput}
                onChange={(e) => setAgentInstructionInput(e.target.value)}
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-white focus:outline-none"
              />
            </div>
            <button
              type="button"
              onClick={handleBuildCustomAgent}
              disabled={isLoading}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 rounded-xl text-white font-bold text-xs flex items-center space-x-2"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Publish Custom Agent</span>
            </button>
          </div>

          {customAgentRes && (
            <div className="p-4 bg-slate-950 border border-emerald-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-emerald-400 font-mono block uppercase">Custom Agent Created: {customAgentRes.agent_id}</span>
              <p className="text-slate-300">• Name: {customAgentRes.name} ({customAgentRes.visibility})</p>
              <p className="text-slate-300">• Permissions Assigned: {customAgentRes.permissions_assigned.join(', ')}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'ADMIN_AUDIT' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Admin Governance & Emergency Disablement</h3>
            <p className="text-xs text-slate-400 mt-1">Revoke extension permissions immediately on security circuit breaker triggers.</p>
          </div>

          <button
            type="button"
            onClick={() => handleRevokePermission('ext-jira-connector-01')}
            disabled={isLoading}
            className="px-4 py-2 bg-red-950/80 hover:bg-red-900/80 border border-red-800/60 text-red-200 font-bold text-xs rounded-xl"
          >
            Emergency Revoke Jira Connector Permissions
          </button>

          {revokeRes && (
            <div className="p-4 bg-red-950/30 border border-red-800/60 rounded-2xl space-y-2 text-xs">
              <span className="font-bold text-red-400 font-mono block uppercase">Revocation Record: {revokeRes.extension_id}</span>
              <p className="text-slate-300">• Status: {revokeRes.status}</p>
              <p className="text-slate-300">• Execution Requests Blocked: {revokeRes.execution_requests_blocked ? 'YES' : 'NO'}</p>
              <p className="text-slate-400">• Reason: {revokeRes.reason}</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
