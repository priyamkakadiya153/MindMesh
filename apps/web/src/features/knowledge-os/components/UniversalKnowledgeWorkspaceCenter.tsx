import React, { useState, useEffect } from 'react';
import {
  executeUniversalSearch, fetchEntityDetail, createContextPack, fetchActivityFeed, executeUniversalCommand,
  fetchPersonalWorkspace, fetchProjectWorkspace, UniversalSearchResultItem, EntityDetailResponse,
  PersonalWorkspaceResponse, ProjectWorkspaceResponse, ActivityEventItem
} from '../knowledge-os-api';
import {
  Search, Command, Layout, Network, GitBranch, Bookmark, Layers, Sparkles, Folder, FileText, CheckSquare, AlertOctagon, Bot, ChevronRight, Share2, Tag
} from 'lucide-react';

interface UniversalKnowledgeWorkspaceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const UniversalKnowledgeWorkspaceCenter: React.FC<UniversalKnowledgeWorkspaceCenterProps> = ({
  initialProjectId = 'bfb4530e-bc5d-4c1f-aaf3-217a55bcaba4',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'WORKSPACE' | 'SEARCH' | 'ENTITY' | 'PERSONAL'>('WORKSPACE');
  const [searchQuery, setSearchQuery] = useState<string>('OAuth migration');
  const [searchResults, setSearchResults] = useState<UniversalSearchResultItem[]>([]);
  const [selectedEntity, setSelectedEntity] = useState<EntityDetailResponse | null>(null);
  const [personalWorkspace, setPersonalWorkspace] = useState<PersonalWorkspaceResponse | null>(null);
  const [projectWorkspace, setProjectWorkspace] = useState<ProjectWorkspaceResponse | null>(null);
  const [activityFeed, setActivityFeed] = useState<ActivityEventItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [commandInput, setCommandInput] = useState<string>('');
  const [actionStatus, setActionStatus] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [pRes, prjRes, actRes] = await Promise.all([
        fetchPersonalWorkspace(token),
        fetchProjectWorkspace(initialProjectId, token),
        fetchActivityFeed(token)
      ]);
      setPersonalWorkspace(pRes);
      setProjectWorkspace(prjRes);
      setActivityFeed(actRes);

      // Load initial entity detail
      const entRes = await fetchEntityDetail('Decision', 'dec-102', token);
      setSelectedEntity(entRes);
    } catch (err) {
      console.error('Failed to load knowledge operating system:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    try {
      const res = await executeUniversalSearch(searchQuery, undefined, token);
      setSearchResults(res.results);
      setActiveTab('SEARCH');
    } catch (err) {
      console.error('Failed search:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCommand = async () => {
    if (!commandInput.trim()) return;
    try {
      const res = await executeUniversalCommand(commandInput, 'proj-auth-101', token);
      setActionStatus(`Executed Command: ${res.result_type}`);
      setCommandInput('');
    } catch (err) {
      console.error('Failed command:', err);
    }
  };

  const handleSaveContextPack = async () => {
    try {
      const pack = await createContextPack('OAuth Migration Context Pack', [
        { type: 'Project', id: 'proj-auth-101', label: 'Authentication Migration' },
        { type: 'Decision', id: 'dec-102', label: 'OAuth 2.0 Strategy' }
      ], token);
      setActionStatus(`Created Context Pack '${pack.pack_title}'`);
      loadData();
    } catch (err) {
      console.error('Failed to create context pack:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Bar with Command Search */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                KNOWLEDGE OPERATING SYSTEM & UNIVERSAL WORKSPACE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60">
                Connected Environment
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Layout className="w-7 h-7 text-indigo-400" />
              <span>Universal Knowledge Workspace</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Move naturally between files, conversations, knowledge, projects, tasks, decisions, memory, AI insights, and actions.
            </p>
          </div>

          {/* Search / Command Input Bar */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-grow max-w-md">
            <Search className="w-4 h-4 text-slate-400 ml-2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search OAuth migration, decisions, tasks..."
              className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full px-2"
            />
            <button
              type="button"
              onClick={handleSearch}
              className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-lg"
            >
              Search
            </button>
          </div>
        </div>

        {/* Breadcrumb Context Bar */}
        <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/60 text-xs font-mono text-slate-400 overflow-x-auto">
          <span className="text-indigo-400 font-bold">Breadcrumb:</span>
          <span>Workspace</span>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span>Authentication Migration</span>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span className="text-emerald-400 font-bold">Decision #dec-102 (OAuth 2.0)</span>
          <ChevronRight className="w-3 h-3 text-slate-600" />
          <span>Task #task-201</span>
        </div>

        {/* Command Bar Shortcut */}
        <div className="flex items-center space-x-2 bg-slate-950/80 p-2 rounded-2xl border border-slate-800 text-xs">
          <Command className="w-4 h-4 text-indigo-400 ml-1" />
          <input
            type="text"
            value={commandInput}
            onChange={(e) => setCommandInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
            placeholder="Universal Command Bar: type 'Create Task', 'Ask MindMesh'..."
            className="bg-transparent text-xs text-white placeholder-slate-500 focus:outline-none w-full px-2"
          />
          <button type="button" onClick={handleCommand} className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 font-bold text-[10px]">
            Run
          </button>
        </div>
      </div>

      {actionStatus && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200">
          {actionStatus}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center space-x-2 bg-slate-900 p-2 rounded-2xl border border-slate-800">
        <button
          type="button"
          onClick={() => setActiveTab('WORKSPACE')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'WORKSPACE' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          Project Workspace
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('SEARCH')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'SEARCH' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          Universal Search
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('ENTITY')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'ENTITY' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          Entity Explorer
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('PERSONAL')}
          className={`px-4 py-2 rounded-xl font-bold text-xs transition-all ${
            activeTab === 'PERSONAL' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
          }`}
        >
          Personal Workspace
        </button>
      </div>

      {/* Workspace Views */}
      {activeTab === 'WORKSPACE' && projectWorkspace && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* Main Content Area */}
          <div className="md:col-span-2 space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-xs font-bold text-white uppercase font-mono">{projectWorkspace.project_name} Overview</h3>
                <span className="text-[9px] font-mono text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 font-bold">{projectWorkspace.provenance_label}</span>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-center">
                  <span className="text-[9px] font-mono text-slate-400 block uppercase">Status</span>
                  <span className="text-sm font-bold text-emerald-400">{projectWorkspace.overview.status}</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-center">
                  <span className="text-[9px] font-mono text-slate-400 block uppercase">Progress</span>
                  <span className="text-sm font-bold text-indigo-400">{projectWorkspace.overview.progress_percent}%</span>
                </div>
                <div className="bg-slate-950 p-3 rounded-2xl border border-slate-800 text-center">
                  <span className="text-[9px] font-mono text-slate-400 block uppercase">Sprint</span>
                  <span className="text-xs font-bold text-slate-200">{projectWorkspace.overview.current_sprint}</span>
                </div>
              </div>

              <div className="p-4 bg-slate-950 rounded-2xl space-y-2">
                <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase block">Lineage Summary</span>
                <p className="text-xs text-slate-300">{projectWorkspace.lineage_summary}</p>
              </div>
            </div>

            {/* Unified Activity Feed */}
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono">Unified Project Activity</h3>
              <div className="space-y-2">
                {activityFeed.map(act => (
                  <div key={act.event_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl text-xs flex items-center justify-between">
                    <div>
                      <span className="font-bold text-white">{act.entity_name}</span>
                      <span className="text-slate-400 ml-2">({act.entity_type})</span>
                      <span className="text-slate-400 ml-2">by {act.actor}</span>
                    </div>
                    <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded uppercase font-bold">{act.action}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Side Context & AI Panel */}
          <div className="space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
              <h3 className="text-xs font-bold text-white uppercase font-mono flex items-center space-x-2">
                <Bookmark className="w-4 h-4 text-indigo-400" />
                <span>Saved Context Packs</span>
              </h3>

              <button
                type="button"
                onClick={handleSaveContextPack}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 rounded-2xl text-white font-bold text-xs shadow-lg"
              >
                + Create Context Pack
              </button>

              {personalWorkspace?.saved_context_packs.map(cp => (
                <div key={cp.pack_id} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 text-xs">
                  <span className="font-bold text-white block">{cp.pack_title}</span>
                  <div className="flex flex-wrap gap-1">
                    {cp.chips.map((ch, idx) => (
                      <span key={idx} className="text-[9px] font-mono bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800/60">
                        {ch.type}: {ch.label}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      {/* Universal Search View */}
      {activeTab === 'SEARCH' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
          <h3 className="text-xs font-bold text-white uppercase font-mono">Cross-Entity Universal Search Results</h3>
          <div className="space-y-3">
            {searchResults.map(res => (
              <div key={res.entity_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-mono text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded uppercase font-bold">{res.entity_type}</span>
                  <span className="text-[9px] font-mono text-slate-500">{res.project_name}</span>
                </div>
                <h4 className="font-bold text-white text-sm">{res.title}</h4>
                <p className="text-slate-300">{res.snippet}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entity Explorer View */}
      {activeTab === 'ENTITY' && selectedEntity && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">Universal Entity Detail</h3>
            <h4 className="text-lg font-black text-white mt-1">{selectedEntity.identity.name}</h4>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-indigo-400 block uppercase font-mono">Entity Relationships</span>
              {selectedEntity.relationships.map((rel, i) => (
                <p key={i} className="text-slate-300">• <strong className="text-indigo-300">{rel.relation_type}:</strong> {rel.label} ({rel.target_type})</p>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-emerald-400 block uppercase font-mono">Lineage Chain</span>
              {selectedEntity.lineage.map((lin, i) => (
                <p key={i} className="text-slate-300">{lin.step}. <strong className="text-emerald-300">{lin.type}:</strong> {lin.label}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Personal Workspace View */}
      {activeTab === 'PERSONAL' && personalWorkspace && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-3">
            <h3 className="text-xs font-bold text-white uppercase font-mono">My Personal Workspace ({personalWorkspace.user_name})</h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-indigo-400 block uppercase font-mono">My Assigned Tasks</span>
              {personalWorkspace.my_tasks.map(t => (
                <p key={t.task_id} className="text-slate-300">• {t.title} ({t.status})</p>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2">
              <span className="font-bold text-amber-400 block uppercase font-mono">My Approved Decisions</span>
              {personalWorkspace.my_decisions.map(d => (
                <p key={d.decision_id} className="text-slate-300">• {d.title} ({d.status})</p>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
