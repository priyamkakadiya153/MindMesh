import React from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Briefcase,
  MessageSquare,
  Users,
  CheckCircle,
  Clock,
  ShieldCheck,
  Sparkles,
  Cpu,
} from 'lucide-react';
import { GraphNode, GraphEdge, NodeType } from './graph-dataset';

export interface InteractiveGraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNodeId: string;
  hoveredNodeId: string | null;
  onSelectNode: (id: string) => void;
  onHoverNode: (id: string | null) => void;
}

const NODE_ICON_MAP: Record<NodeType, React.ReactNode> = {
  document: <FileText className="w-4 h-4 text-indigo-400" />,
  project: <Briefcase className="w-4 h-4 text-blue-400" />,
  conversation: <MessageSquare className="w-4 h-4 text-cyan-400" />,
  person: <Users className="w-4 h-4 text-purple-400" />,
  task: <CheckCircle className="w-4 h-4 text-emerald-400" />,
  meeting: <Clock className="w-4 h-4 text-amber-400" />,
  decision: <ShieldCheck className="w-4 h-4 text-rose-400" />,
  'ai-agent': <Sparkles className="w-4 h-4 text-indigo-300" />,
};

export const InteractiveGraphCanvas: React.FC<InteractiveGraphCanvasProps> = ({
  nodes,
  edges,
  selectedNodeId,
  hoveredNodeId,
  onSelectNode,
  onHoverNode,
}) => {
  const activeNodeId = hoveredNodeId || selectedNodeId;
  const activeNode = nodes.find((n) => n.id === activeNodeId);
  const connectedIds = activeNode ? [activeNode.id, ...activeNode.connectedIds] : [];

  return (
    <div className="relative w-full h-[480px] sm:h-[540px] rounded-ds-2xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800/90 shadow-ds-hero overflow-hidden select-none">
      {/* Dynamic Ambient Background Glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-600/10 blur-3xl pointer-events-none" />

      {/* SVG Connecting Edges Layer */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {edges.map((edge) => {
          const fromNode = nodes.find((n) => n.id === edge.from);
          const toNode = nodes.find((n) => n.id === edge.to);

          if (!fromNode || !toNode) return null;

          const isActiveEdge =
            connectedIds.includes(fromNode.id) && connectedIds.includes(toNode.id);

          return (
            <line
              key={`${edge.from}-${edge.to}`}
              x1={`${fromNode.x}%`}
              y1={`${fromNode.y}%`}
              x2={`${toNode.x}%`}
              y2={`${toNode.y}%`}
              stroke={isActiveEdge ? '#6366f1' : '#94a3b8'}
              strokeWidth={isActiveEdge ? 2.5 : 1}
              strokeDasharray={isActiveEdge ? '4 4' : 'none'}
              className="transition-all duration-300"
              style={{
                opacity: isActiveEdge ? 0.9 : 0.25,
              }}
            />
          );
        })}
      </svg>

      {/* Graph Nodes Layer */}
      {nodes.map((node) => {
        const isSelected = selectedNodeId === node.id;
        const isHovered = hoveredNodeId === node.id;
        const isConnected = connectedIds.includes(node.id);

        return (
          <motion.div
            key={node.id}
            onClick={() => onSelectNode(node.id)}
            onMouseEnter={() => onHoverNode(node.id)}
            onMouseLeave={() => onHoverNode(null)}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{
              opacity: isConnected ? 1 : 0.35,
              scale: isSelected ? 1.15 : isHovered ? 1.1 : 1,
            }}
            transition={{ duration: 0.2 }}
            style={{
              left: `${node.x}%`,
              top: `${node.y}%`,
            }}
            className={`
              absolute -translate-x-1/2 -translate-y-1/2 cursor-pointer z-10 group
            `.trim()}
          >
            {/* Glowing Pulse Ring for Selected / Active Node */}
            {(isSelected || isHovered) && (
              <div className="absolute inset-0 -m-2 rounded-full bg-indigo-500/30 animate-ping pointer-events-none" />
            )}

            {/* Node Container Card */}
            <div
              className={`
                flex items-center gap-2 px-3 py-2 rounded-ds-xl border transition-all duration-300 shadow-ds-medium backdrop-blur-md
                ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-400 shadow-ds-glow ring-2 ring-indigo-400'
                    : isConnected
                    ? 'bg-white dark:bg-slate-900/90 text-slate-900 dark:text-slate-100 border-indigo-200 dark:border-indigo-500/40 hover:border-indigo-400'
                    : 'bg-white/80 dark:bg-slate-900/60 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800'
                }
              `.trim()}
            >

              <div className="shrink-0">{NODE_ICON_MAP[node.type]}</div>
              <span className="text-xs font-bold whitespace-nowrap">{node.title}</span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
};
