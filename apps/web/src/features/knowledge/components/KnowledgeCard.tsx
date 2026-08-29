import React from 'react';
import { useNavigate } from 'react-router-dom';
import { KnowledgeItem } from '../hub-api';
import {
  CheckCircle2, FileText, MessageSquare, Briefcase, ArrowUpRight,
  Sparkles, Clock, Network, Layers
} from 'lucide-react';

interface KnowledgeCardProps {
  item: KnowledgeItem;
  onAskMindMesh?: (prompt: string) => void;
}

export const KnowledgeCard: React.FC<KnowledgeCardProps> = ({ item, onAskMindMesh }) => {
  const navigate = useNavigate();

  const getTypeIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'DECISION':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400" />;
      case 'TASK':
        return <CheckCircle2 className="w-4 h-4 text-amber-400" />;
      case 'DOCUMENT':
      case 'FILE':
        return <FileText className="w-4 h-4 text-blue-400" />;
      case 'CONVERSATION':
      case 'MESSAGE':
        return <MessageSquare className="w-4 h-4 text-indigo-400" />;
      case 'PROJECT':
        return <Briefcase className="w-4 h-4 text-purple-400" />;
      default:
        return <Layers className="w-4 h-4 text-slate-400" />;
    }
  };

  const handleOpenSource = () => {
    if (item.deep_link) {
      if (item.deep_link.startsWith('/')) {
        navigate(item.deep_link);
      } else if (item.deep_link.startsWith('file_preview:')) {
        const fileId = item.deep_link.replace('file_preview:', '');
        navigate(`/files?preview=${fileId}`);
      }
    }
  };

  const handleAskHandoff = (e: React.MouseEvent) => {
    e.stopPropagation();
    const promptText = `What is the context around ${item.type.toLowerCase()} "${item.title}"?`;
    if (onAskMindMesh) {
      onAskMindMesh(promptText);
    } else {
      navigate('/ask', { state: { initialPrompt: promptText } });
    }
  };

  return (
    <div
      onClick={handleOpenSource}
      className="p-4 bg-slate-900/70 border border-slate-800/80 hover:border-indigo-500/50 hover:bg-slate-800/60 rounded-2xl cursor-pointer transition-all space-y-3 group shadow-md"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-slate-800 border border-slate-700/60">
            {getTypeIcon(item.type)}
          </div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-300 px-2 py-0.5 bg-slate-800 rounded border border-slate-700/60">
            {item.type}
          </span>
        </div>

        <div className="flex items-center space-x-1 text-[10px] text-slate-500 font-mono">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>{item.timestamp ? item.timestamp.slice(0, 10) : ''}</span>
        </div>
      </div>

      <div>
        <h4 className="text-sm font-bold text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
          {item.title}
        </h4>
        <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
          {item.description}
        </p>
      </div>

      <div className="flex items-center justify-between pt-1 text-[11px]">
        <span className="text-slate-500 truncate max-w-[200px]">
          Source: <span className="text-slate-300 capitalize">{item.source_type}</span>
        </span>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handleAskHandoff}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-indigo-600/30 text-indigo-300 hover:text-indigo-200 border border-slate-700/60 transition-all font-medium"
          >
            <Sparkles className="w-3 h-3" />
            <span>Ask</span>
          </button>

          <button
            type="button"
            onClick={handleOpenSource}
            className="p-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
