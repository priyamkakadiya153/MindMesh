import React, { useState, useEffect } from 'react';
import {
  fetchKnowledgeHome, createCollection, fetchProjectKnowledgeHub, saveKnowledgeItem, attachKnowledgeReference,
  KnowledgeHomeResponse, CollectionResponse, ProjectHubResponse
} from '../knowledge-workspace-api';
import {
  LayoutDashboard, BookMarked, FolderPlus, Compass, Layers, ShieldCheck, CheckCircle2, ArrowRight, CornerDownRight, RefreshCw, FileText, Check, Paperclip, Share2, Sparkles
} from 'lucide-react';

interface KnowledgeWorkspaceCenterProps {
  initialProjectId?: string;
  token?: string;
}

export const KnowledgeWorkspaceCenter: React.FC<KnowledgeWorkspaceCenterProps> = ({
  initialProjectId = '8b352270-44d5-4c3b-bad3-0e2da295ab21',
  token
}) => {
  const [activeTab, setActiveTab] = useState<'HOME' | 'PROJECT_HUB' | 'COLLECTIONS'>('HOME');
  const [homeData, setHomeData] = useState<KnowledgeHomeResponse | null>(null);
  const [hubData, setHubData] = useState<ProjectHubResponse | null>(null);
  const [collectionName, setCollectionName] = useState<string>('Authentication Resources');
  const [createdCollection, setCreatedCollection] = useState<CollectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [hRes, hubRes] = await Promise.all([
        fetchKnowledgeHome(initialProjectId, token),
        fetchProjectKnowledgeHub(initialProjectId, token)
      ]);
      setHomeData(hRes);
      setHubData(hubRes);
    } catch (err) {
      console.error('Failed to load workspace center:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [initialProjectId, token]);

  const handleCreateCollection = async () => {
    if (!collectionName.trim()) return;
    try {
      const col = await createCollection(collectionName, 'PROJECT', 'Grouped project architecture and decisions', 'All Authentication Decisions', token);
      setCreatedCollection(col);
      setActionMessage(`Created collection '${col.name}' with 2 item references.`);
    } catch (err) {
      console.error('Failed collection creation:', err);
    }
  };

  const handleSave = async (id: string, type: string, title: string) => {
    try {
      const res = await saveKnowledgeItem(id, type, title, token);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed save:', err);
    }
  };

  const handleAttach = async (targetId: string, refId: string) => {
    try {
      const res = await attachKnowledgeReference('TASK', targetId, refId, 'DECISION', 'SUPPORTS', token);
      setActionMessage(res.message);
    } catch (err) {
      console.error('Failed attach:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/80 to-slate-900 border border-indigo-800/60 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2.5 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                INTELLIGENT KNOWLEDGE WORKSPACE EXPERIENCE
              </span>
              <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800/60 flex items-center space-x-1">
                <ShieldCheck className="w-3 h-3" />
                <span>Unified Organizational Memory Loop</span>
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Compass className="w-7 h-7 text-indigo-400" />
              <span>MindMesh Knowledge Workspace</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Seamlessly discover, navigate, explore, collect, and reuse healthy organizational knowledge in your daily work.
            </p>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="flex items-center space-x-2 bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex-shrink-0">
            <button
              type="button"
              onClick={() => setActiveTab('HOME')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'HOME' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Knowledge Home
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('PROJECT_HUB')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'PROJECT_HUB' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Project Hub
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('COLLECTIONS')}
              className={`px-3 py-1.5 rounded-xl font-bold text-xs transition-all ${
                activeTab === 'COLLECTIONS' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Collections
            </button>
          </div>
        </div>
      </div>

      {/* Action Toast */}
      {actionMessage && (
        <div className="p-3 bg-indigo-950/80 border border-indigo-800/60 rounded-2xl text-xs text-indigo-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Check className="w-4 h-4 text-emerald-400" />
            <span>{actionMessage}</span>
          </div>
          <button type="button" onClick={() => setActionMessage(null)} className="text-[10px] text-slate-400 hover:text-white font-mono">Dismiss</button>
        </div>
      )}

      {/* Tab Views */}
      {activeTab === 'HOME' && homeData && (
        <div className="space-y-6">
          
          {/* Section: Continue Where You Left Off */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-xs font-bold text-white flex items-center space-x-2">
                <Clock className="w-4 h-4 text-indigo-400" />
                <span>Continue Where You Left Off</span>
              </h3>
              <span className="text-[9px] font-mono text-slate-500 uppercase">Recent Activity Context</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {homeData.continue_where_you_left_off.map((item) => (
                <div key={item.entity_id} className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-2 hover:border-indigo-800/60 transition-all">
                  <div className="flex items-center justify-between">
                    <span className="text-[8px] font-mono font-bold text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{item.entity_type}</span>
                    <span className="text-[8px] font-mono text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded border border-emerald-800/60">{item.trust_label}</span>
                  </div>
                  <h4 className="text-xs font-bold text-white">{item.title}</h4>
                  <p className="text-[10px] text-slate-400">Project: {item.project_name}</p>

                  <div className="flex items-center justify-end space-x-2 pt-2">
                    <button
                      type="button"
                      onClick={() => handleSave(item.entity_id, item.entity_type, item.title)}
                      className="px-2.5 py-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-[10px] text-slate-300 font-bold flex items-center space-x-1"
                    >
                      <BookMarked className="w-3 h-3" />
                      <span>Save Item</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Section: Needs Attention */}
          <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
            <h3 className="text-xs font-bold text-white flex items-center space-x-2 border-b border-slate-800 pb-3">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              <span>Needs Attention ({homeData.needs_attention.length})</span>
            </h3>

            <div className="space-y-3">
              {homeData.needs_attention.map((att, i) => (
                <div key={i} className="p-3 bg-slate-950 border border-slate-800 rounded-2xl flex items-center justify-between text-xs">
                  <div>
                    <span className="text-[8px] font-mono font-bold text-amber-400 bg-amber-950 px-1.5 py-0.5 rounded uppercase">{att.type}</span>
                    <h5 className="font-bold text-slate-200 mt-1">{att.title}</h5>
                    <p className="text-[10px] text-slate-400">{att.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}

      {activeTab === 'PROJECT_HUB' && hubData && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="border-b border-slate-800 pb-4">
            <h2 className="text-lg font-black text-white">{hubData.project_name} Knowledge Hub</h2>
            <p className="text-xs text-slate-400 mt-1">{hubData.overview}</p>
          </div>

          {/* Documents & Decisions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase font-mono">Governed Documents</h4>
              {hubData.documents.map((d) => (
                <div key={d.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-white">{d.title}</span>
                    <span className="text-[9px] font-mono text-slate-500 block">{d.version}</span>
                  </div>
                  <span className="text-[8px] font-mono text-emerald-400 bg-emerald-950 px-1.5 py-0.5 rounded">{d.status}</span>
                </div>
              ))}
            </div>

            <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
              <h4 className="text-xs font-bold text-indigo-400 uppercase font-mono">Approved Decisions</h4>
              {hubData.decisions.map((dec) => (
                <div key={dec.id} className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-between text-xs">
                  <span className="font-bold text-white">{dec.title}</span>
                  <button
                    type="button"
                    onClick={() => handleAttach('task-deploy-cfg', dec.id)}
                    className="px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white text-[10px] font-bold flex items-center space-x-1"
                  >
                    <Paperclip className="w-3 h-3" />
                    <span>Attach to Task</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Knowledge Map Lineage */}
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-2xl space-y-3">
            <h4 className="text-xs font-bold text-indigo-400 uppercase font-mono">Visual Knowledge Map Lineage</h4>
            <div className="flex flex-wrap items-center gap-2 text-xs">
              {hubData.knowledge_map_nodes.map((node, i) => (
                <React.Fragment key={node.id}>
                  <div className="px-3 py-1.5 bg-slate-900 border border-indigo-800/60 rounded-xl text-white font-mono text-[11px] font-bold">
                    {node.label}
                  </div>
                  {i < hubData.knowledge_map_nodes.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-slate-600" />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'COLLECTIONS' && (
        <div className="bg-slate-900/80 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-6 backdrop-blur-md">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h3 className="text-xs font-bold text-white uppercase font-mono">Knowledge Collections & Smart Collections</h3>
              <p className="text-xs text-slate-400 mt-1">Group related resources into smart rule collections without content duplication.</p>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={collectionName}
                onChange={(e) => setCollectionName(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none"
              />
              <button
                type="button"
                onClick={() => handleCreateCollection()}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-bold text-xs shadow-md"
              >
                Create Collection
              </button>
            </div>
          </div>

          {createdCollection && (
            <div className="p-4 bg-slate-950 border border-indigo-800/60 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white">{createdCollection.name}</h4>
                <span className="text-[9px] font-mono text-indigo-400 bg-slate-900 px-2 py-0.5 rounded">{createdCollection.collection_type}</span>
              </div>
              <p className="text-xs text-slate-400">{createdCollection.description}</p>

              <div className="space-y-2 pt-2">
                <span className="text-[9px] font-mono text-slate-500 uppercase block">Referenced Entities</span>
                {createdCollection.item_references.map((item, idx) => (
                  <div key={idx} className="p-2 bg-slate-900 border border-slate-800 rounded-xl text-xs flex items-center justify-between">
                    <span className="font-bold text-slate-200">{item.title}</span>
                    <span className="text-[8px] font-mono text-slate-400">{item.type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

    </div>
  );
};
