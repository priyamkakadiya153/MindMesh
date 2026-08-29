import React from 'react';
import { FileText, Download, Share2, Shield, Clock, CheckCircle2, X } from 'lucide-react';
import { Modal } from '../foundation/feedback/OverlayComponents';
import { Button } from '../foundation/buttons/Button';
import { Badge } from '../foundation/feedback/Badge';

export interface DemoDoc {
  id: string;
  name: string;
  type: 'pdf' | 'markdown' | 'code' | 'notes';
  size: string;
  updatedAt: string;
  author: string;
  content: string;
  citations: number;
}

export interface DemoDocPreviewModalProps {
  doc: DemoDoc | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DemoDocPreviewModal: React.FC<DemoDocPreviewModalProps> = ({
  doc,
  isOpen,
  onClose,
}) => {
  if (!doc) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={doc.name}
      description={`Document Details • ${doc.size} • Updated ${doc.updatedAt}`}
      maxWidth="lg"
    >
      <div className="space-y-4 text-xs">
        {/* Document Metadata Bar */}
        <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-ds-lg bg-slate-900 border border-slate-800">
          <div className="flex items-center gap-3">
            <Badge variant="primary" className="uppercase font-mono text-[10px]">
              {doc.type}
            </Badge>
            <span className="text-slate-300 font-medium">Author: {doc.author}</span>
          </div>
          <div className="flex items-center gap-2 text-indigo-400 font-semibold text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Indexed in Knowledge Vector Index</span>
          </div>
        </div>

        {/* Realistic Content Preview Canvas */}
        <div className="p-4 rounded-ds-xl bg-slate-950 border border-slate-800 font-mono text-slate-200 max-h-72 overflow-y-auto space-y-2 leading-relaxed">
          {doc.type === 'code' ? (
            <pre className="text-emerald-300 text-[11px] whitespace-pre-wrap">{doc.content}</pre>
          ) : (
            <div className="whitespace-pre-wrap font-sans text-slate-300 text-xs">
              {doc.content}
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Download className="w-3.5 h-3.5" />}
              onClick={() => alert(`Simulated download for ${doc.name}`)}
            >
              Download File
            </Button>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Share2 className="w-3.5 h-3.5" />}
              onClick={() => alert(`Copied citation link for ${doc.name}`)}
            >
              Share Citation
            </Button>
          </div>
          <Button variant="primary" size="sm" onClick={onClose}>
            Close Preview
          </Button>
        </div>
      </div>
    </Modal>
  );
};
