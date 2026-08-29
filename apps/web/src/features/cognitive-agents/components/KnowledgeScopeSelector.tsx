import React, { useState, useEffect } from 'react';
import {
  Layers,
  FolderKanban,
  FileText,
  MessageSquare,
  Sparkles,
  Search,
  Check,
  Info,
  Loader2
} from 'lucide-react';
import { CognitiveAgentScope, CognitiveAgentScopeType } from '../../../types/cognitive-agent';
import { useAuthStore } from '../../auth/auth-store';
import { fetchKnowledgeOptions } from '../api/cognitive-agent-api';

interface KnowledgeScopeSelectorProps {
  workspaceId?: string;
  scope: CognitiveAgentScope;
  onChange: (updatedScope: CognitiveAgentScope) => void;
}

export const KnowledgeScopeSelector: React.FC<KnowledgeScopeSelectorProps> = ({
  workspaceId,
  scope,
  onChange
}) => {
  const { token, currentOrg } = useAuthStore();

  const [options, setOptions] = useState<{
    projects: { id: string; name: string; description?: string }[];
    documents: { id: string; title: string; filename: string; mime_type: string }[];
    conversations: { id: string; title: string; conversation_type: string }[];
  }>({ projects: [], documents: [], conversations: [] });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    if (!token || !currentOrg?.id || !workspaceId) return;

    setLoading(true);
    setError(null);
    fetchKnowledgeOptions(token, currentOrg.id, workspaceId)
      .then(data => setOptions(data))
      .catch(err => setError(err.message || 'Failed to load workspace knowledge options.'))
      .finally(() => setLoading(false));
  }, [token, currentOrg?.id, workspaceId]);

  const scopeType = scope.scope_type || 'WORKSPACE';

  const handleScopeTypeChange = (newType: CognitiveAgentScopeType) => {
    onChange({
      ...scope,
      scope_type: newType,
      workspace_id: workspaceId
    });
  };

  const handleProjectSelect = (projId: string) => {
    onChange({
      ...scope,
      project_id: scope.project_id === projId ? undefined : projId
    });
  };

  const handleDocumentToggle = (docId: string) => {
    const currentDocs = scope.document_ids || [];
    const nextDocs = currentDocs.includes(docId)
      ? currentDocs.filter(id => id !== docId)
      : [...currentDocs, docId];

    onChange({
      ...scope,
      document_ids: nextDocs
    });
  };

  const handleConversationToggle = (convId: string) => {
    const currentConvs = scope.conversation_ids || [];
    const nextConvs = currentConvs.includes(convId)
      ? currentConvs.filter(id => id !== convId)
      : [...currentConvs, convId];

    onChange({
      ...scope,
      conversation_ids: nextConvs
    });
  };

  const filteredProjects = options.projects.filter(p =>
    p.name.toLowerCase().includes(searchFilter.toLowerCase())
  );
  const filteredDocuments = options.documents.filter(d =>
    (d.title || d.filename).toLowerCase().includes(searchFilter.toLowerCase())
  );
  const filteredConversations = options.conversations.filter(c =>
    c.title.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="space-y-4 font-outfit text-textPrimary">
      {/* Scope Description Banner */}
      <div className="p-3 bg-accentSubtle/50 border border-accent/20 rounded-xl text-xs flex items-start gap-2.5">
        <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold text-accentText">Knowledge Access Boundary</span>
          <p className="text-textSecondary text-[11px] mt-0.5">
            Configure which workspace resources this agent is permitted to analyze. The backend strictly enforces your user authorization + agent scope boundary.
          </p>
        </div>
      </div>

      {/* Scope Type Selection Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
        {[
          { type: 'WORKSPACE', label: 'Entire Workspace', icon: Layers, desc: 'All authorized workspace knowledge' },
          { type: 'PROJECT', label: 'Selected Projects', icon: FolderKanban, desc: 'Specific project & linked items' },
          { type: 'DOCUMENT', label: 'Selected Documents', icon: FileText, desc: 'Specific documents only' },
          { type: 'CONVERSATION', label: 'Selected Conversations', icon: MessageSquare, desc: 'Specific chat threads' },
          { type: 'SELECTED_KNOWLEDGE', label: 'Custom Combined', icon: Sparkles, desc: 'Explicit multi-type selection' },
        ].map((item) => {
          const IconComponent = item.icon;
          const isSelected = scopeType === item.type;
          return (
            <div
              key={item.type}
              onClick={() => handleScopeTypeChange(item.type as CognitiveAgentScopeType)}
              className={`p-3 rounded-xl border cursor-pointer transition-all flex flex-col justify-between space-y-2 ${
                isSelected
                  ? 'bg-accentSubtle border-accent text-accentText shadow-xs'
                  : 'bg-bgInput border-borderColor hover:border-accent/40 text-textSecondary'
              }`}
            >
              <div className="flex items-center justify-between">
                <IconComponent className={`w-4 h-4 ${isSelected ? 'text-accent' : 'text-textMuted'}`} />
                {isSelected && <Check className="w-3.5 h-3.5 text-accent" />}
              </div>
              <div>
                <span className="font-bold text-xs block text-textPrimary">{item.label}</span>
                <span className="text-[10px] text-textMuted leading-tight block mt-0.5">{item.desc}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Resource Search Filter (if non-workspace scope selected) */}
      {scopeType !== 'WORKSPACE' && (
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-textMuted absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchFilter}
            onChange={e => setSearchFilter(e.target.value)}
            placeholder="Search projects, documents, or conversations..."
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-bgInput border border-borderColor rounded-xl text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors"
          />
        </div>
      )}

      {/* Loading & Error States */}
      {loading && (
        <div className="p-4 text-center text-xs text-textMuted flex items-center justify-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-accent" />
          <span>Loading workspace knowledge options...</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs">
          {error}
        </div>
      )}

      {/* Scope Target Selectors */}
      {!loading && !error && scopeType !== 'WORKSPACE' && (
        <div className="space-y-3.5 max-h-48 overflow-y-auto pr-1">
          {/* Project Picker */}
          {(scopeType === 'PROJECT' || scopeType === 'SELECTED_KNOWLEDGE') && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-textMuted uppercase tracking-wider block">
                Projects ({filteredProjects.length})
              </span>
              {filteredProjects.length === 0 ? (
                <p className="text-xs text-textMuted italic">No accessible projects available in this workspace.</p>
              ) : (
                <div className="space-y-1">
                  {filteredProjects.map(p => {
                    const isPicked = scope.project_id === p.id;
                    return (
                      <div
                        key={p.id}
                        onClick={() => handleProjectSelect(p.id)}
                        className={`p-2 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                          isPicked
                            ? 'bg-accentSubtle border-accent/50 text-accentText font-semibold'
                            : 'bg-bgInput border-borderMuted text-textSecondary hover:bg-bgHover'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <FolderKanban className="w-3.5 h-3.5 text-accent shrink-0" />
                          <span className="truncate">{p.name}</span>
                        </div>
                        {isPicked && <Check className="w-3.5 h-3.5 text-accent" />}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Document Picker */}
          {(scopeType === 'DOCUMENT' || scopeType === 'SELECTED_KNOWLEDGE') && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-textMuted uppercase tracking-wider block">
                Documents ({filteredDocuments.length})
              </span>
              {filteredDocuments.length === 0 ? (
                <p className="text-xs text-textMuted italic">No accessible documents available in this workspace.</p>
              ) : (
                <div className="space-y-1">
                  {filteredDocuments.map(d => {
                    const isChecked = (scope.document_ids || []).includes(d.id);
                    return (
                      <div
                        key={d.id}
                        onClick={() => handleDocumentToggle(d.id)}
                        className={`p-2 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                          isChecked
                            ? 'bg-accentSubtle border-accent/50 text-accentText font-semibold'
                            : 'bg-bgInput border-borderMuted text-textSecondary hover:bg-bgHover'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <FileText className="w-3.5 h-3.5 text-accent shrink-0" />
                          <span className="truncate">{d.title || d.filename}</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="accent-accent"
                        />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Conversation Picker */}
          {(scopeType === 'CONVERSATION' || scopeType === 'SELECTED_KNOWLEDGE') && (
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-textMuted uppercase tracking-wider block">
                Conversations ({filteredConversations.length})
              </span>
              {filteredConversations.length === 0 ? (
                <p className="text-xs text-textMuted italic">No accessible conversations available in this workspace.</p>
              ) : (
                <div className="space-y-1">
                  {filteredConversations.map(c => {
                    const isChecked = (scope.conversation_ids || []).includes(c.id);
                    return (
                      <div
                        key={c.id}
                        onClick={() => handleConversationToggle(c.id)}
                        className={`p-2 rounded-lg border text-xs cursor-pointer flex items-center justify-between transition-colors ${
                          isChecked
                            ? 'bg-accentSubtle border-accent/50 text-accentText font-semibold'
                            : 'bg-bgInput border-borderMuted text-textSecondary hover:bg-bgHover'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <MessageSquare className="w-3.5 h-3.5 text-accent shrink-0" />
                          <span className="truncate">{c.title}</span>
                        </div>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}}
                          className="accent-accent"
                        />
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Scope Preview Summary */}
      <div className="p-3 bg-bgInput rounded-xl border border-borderMuted text-xs flex items-center justify-between">
        <span className="text-textMuted font-medium">Selected Boundary:</span>
        <span className="font-semibold text-accentText">
          {scopeType === 'WORKSPACE' && 'Entire Workspace Knowledge'}
          {scopeType === 'PROJECT' && (scope.project_id ? '1 Project Selected' : '0 Projects Selected')}
          {scopeType === 'DOCUMENT' && `${(scope.document_ids || []).length} Documents Selected`}
          {scopeType === 'CONVERSATION' && `${(scope.conversation_ids || []).length} Conversations Selected`}
          {scopeType === 'SELECTED_KNOWLEDGE' && `${(scope.document_ids || []).length} Docs, ${(scope.conversation_ids || []).length} Convs, ${scope.project_id ? 1 : 0} Proj`}
        </span>
      </div>
    </div>
  );
};
