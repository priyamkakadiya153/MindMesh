import React, { useState, useEffect } from 'react';
import {
  fetchRelatedKnowledge, fetchKnowledgePath, bookmarkKnowledge, followEntity, fetchSavedKnowledge,
  CategorizedRelatedKnowledgeResponse, KnowledgePathResponse, BookmarkItem, RelatedItem
} from '../discovery-navigation-api';
import {
  Compass, Bookmark, Bell, ArrowRight, ChevronRight, Layers, Sparkles, ShieldCheck, AlertCircle, Info, ExternalLink, MessageSquare, FileText, CheckSquare
} from 'lucide-react';

interface KnowledgeDiscoveryCenterProps {
  initialEntityId?: string;
  initialEntityType?: string;
  projectId?: string;
  token?: string;
}

export const KnowledgeDiscoveryCenter: React.FC<KnowledgeDiscoveryCenterProps> = ({
  initialEntityId = 'doc-auth-arch-id',
  initialEntityType = 'DOCUMENT',
  projectId = 'proj-auth-id',
  token
}) => {
  const [entityId, setEntityId] = useState<string>(initialEntityId);
  const [entityType, setEntityType] = useState<string>(initialEntityType);
  const [relatedData, setRelatedData] = useState<CategorizedRelatedKnowledgeResponse | null>(null);
  const [pathData, setPathData] = useState<KnowledgePathResponse | null>(null);
  const [savedItems, setSavedItems] = useState<BookmarkItem[]>([]);
  const [activeCategoryTab, setActiveCategoryTab] = useState<'ALL' | 'DIRECT' | 'SUPPORTING' | 'AFFECTED' | 'HISTORICAL' | 'SUGGESTED'>('ALL');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const loadDiscovery = async () => {
    setIsLoading(true);
    try {
      const [rRes, pRes, sRes] = await Promise.all([
        fetchRelatedKnowledge(entityId, entityType, token).catch(() => null),
        fetchKnowledgePath(projectId, entityId, token).catch(() => null),
        fetchSavedKnowledge(token).catch(() => [])
      ]);
      if (rRes) setRelatedData(rRes);
      if (pRes) setPathData(pRes);
      if (sRes) setSavedItems(sRes);
    } catch (err) {
      console.error('Failed to load discovery data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDiscovery();
  }, [entityId, entityType, projectId, token]);

  const handleBookmark = async (item: RelatedItem) => {
    try {
      await bookmarkKnowledge(item.id, item.entity_type, item.title, item.governance_status, token);
      const updated = await fetchSavedKnowledge(token);
      setSavedItems(updated);
    } catch (err) {
      console.error('Failed to bookmark:', err);
    }
  };

  const handleFollow = async (id: string) => {
    try {
      await followEntity(id, token);
      alert('Following entity for proactive updates!');
    } catch (err) {
      console.error('Failed to follow:', err);
    }
  };

  return (
    <div className="w-full max-w-6xl mx-auto p-4 md:p-6 space-y-6 text-slate-100 font-sans select-none">
      
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl space-y-4 backdrop-blur-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-indigo-400 px-2 py-0.5 bg-indigo-950 rounded border border-indigo-800/60">
                KNOWLEDGE DISCOVERY & NAVIGATION
              </span>
              <span className="text-[10px] font-mono font-bold text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                Saved Items: {savedItems.length}
              </span>
            </div>
            <h1 className="text-2xl font-black text-white mt-1.5 flex items-center space-x-2">
              <Compass className="w-7 h-7 text-indigo-400" />
              <span>Knowledge Discovery Center</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xl">
              Discover what you didn't know to search for through guided paths, governance trust badges, and contextual explanations.
            </p>
          </div>
        </div>

        {/* Knowledge Breadcrumbs Path */}
        {pathData && (
          <div className="flex items-center space-x-2 pt-2 border-t border-slate-800/80 text-xs font-mono text-slate-400 overflow-x-auto">
            <span className="text-slate-500 font-bold">Path:</span>
            {pathData.breadcrumbs.map((b, idx) => (
              <React.Fragment key={idx}>
                <span
                  onClick={() => setEntityId(b.entity_id)}
                  className="cursor-pointer hover:text-white font-bold text-indigo-400 bg-slate-950 px-2 py-1 rounded border border-slate-800"
                >
                  {b.label}
                </span>
                {idx < pathData.breadcrumbs.length - 1 && <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>

      {/* Discovery Results Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Left 2 Cols: Categorized Related Knowledge */}
        <div className="md:col-span-2 space-y-4">
          
          {/* Category Filter Pills */}
          <div className="flex flex-wrap gap-2">
            {(['ALL', 'DIRECT', 'SUPPORTING', 'AFFECTED', 'HISTORICAL', 'SUGGESTED'] as const).map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setActiveCategoryTab(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold font-mono transition-all ${
                  activeCategoryTab === cat
                    ? 'bg-indigo-600 text-white shadow-md'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          {!relatedData ? (
            <div className="py-16 text-center space-y-2 bg-slate-900/40 border border-slate-800/60 rounded-3xl">
              <Compass className="w-8 h-8 text-slate-600 mx-auto" />
              <h4 className="text-xs font-bold text-slate-400">Loading discovery results...</h4>
            </div>
          ) : (
            <div className="space-y-4">
              
              {/* Directly Related */}
              {(activeCategoryTab === 'ALL' || activeCategoryTab === 'DIRECT') && relatedData.categories.directly_related.map((item) => (
                <div key={item.id} className="p-5 bg-slate-900/80 border border-indigo-800/60 rounded-3xl space-y-3 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] font-mono font-bold text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded uppercase">
                        {item.relationship}
                      </span>
                      <span className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${
                        item.governance_status === 'CURRENT' ? 'bg-emerald-950 text-emerald-400 border-emerald-800/60' : 'bg-slate-800 text-slate-300'
                      }`}>
                        {item.governance_status}
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        type="button"
                        onClick={() => handleBookmark(item)}
                        className="p-1 text-slate-400 hover:text-amber-400"
                        title="Bookmark Knowledge"
                      >
                        <Bookmark className="w-4 h-4" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleFollow(item.id)}
                        className="p-1 text-slate-400 hover:text-indigo-400"
                        title="Follow Entity"
                      >
                        <Bell className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-slate-100">{item.title}</h3>
                    <p className="text-xs text-slate-300 mt-1">{item.explanation}</p>
                  </div>
                </div>
              ))}

              {/* Supporting & Affected */}
              {(activeCategoryTab === 'ALL' || activeCategoryTab === 'SUPPORTING') && relatedData.categories.supporting.map((item) => (
                <div key={item.id} className="p-5 bg-slate-900/60 border border-slate-800 rounded-3xl space-y-2">
                  <span className="text-[9px] font-mono font-bold text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded uppercase">
                    {item.relationship}
                  </span>
                  <h4 className="font-bold text-xs text-white">{item.title}</h4>
                  <p className="text-[11px] text-slate-400">{item.explanation}</p>
                </div>
              ))}

              {/* Historical */}
              {(activeCategoryTab === 'ALL' || activeCategoryTab === 'HISTORICAL') && relatedData.categories.historical.map((item) => (
                <div key={item.id} className="p-5 bg-slate-900/40 border border-amber-900/40 rounded-3xl space-y-2 opacity-80">
                  <span className="text-[9px] font-mono font-bold text-amber-400 bg-amber-950 px-2 py-0.5 rounded uppercase">
                    {item.governance_status}: {item.relationship}
                  </span>
                  <h4 className="font-bold text-xs text-slate-300">{item.title}</h4>
                  <p className="text-[11px] text-slate-500">{item.explanation}</p>
                </div>
              ))}

            </div>
          )}
        </div>

        {/* Right Col: Saved Knowledge Collection Panel */}
        <div className="space-y-4">
          <div className="bg-slate-900/80 border border-slate-800 p-5 rounded-3xl shadow-xl space-y-3 backdrop-blur-md">
            <div className="flex items-center space-x-2 border-b border-slate-800 pb-2">
              <Bookmark className="w-4 h-4 text-amber-400" />
              <h4 className="text-xs font-bold text-white">Saved Knowledge Collection</h4>
            </div>

            {savedItems.length === 0 ? (
              <p className="text-[11px] text-slate-500 text-center py-4">No bookmarked knowledge items yet.</p>
            ) : (
              <div className="space-y-2">
                {savedItems.map((b) => (
                  <div key={b.id} className="p-2.5 bg-slate-950 border border-slate-800 rounded-xl space-y-1 text-xs">
                    <div className="flex items-center justify-between">
                      <span className={`text-[8px] font-mono font-bold px-1.5 py-0.2 rounded uppercase ${
                        b.governance_status === 'SUPERSEDED' ? 'bg-amber-950 text-amber-400' : 'bg-emerald-950 text-emerald-400'
                      }`}>
                        {b.governance_status}
                      </span>
                    </div>
                    <h5 className="font-bold text-slate-200 text-[11px]">{b.title}</h5>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>

    </div>
  );
};
