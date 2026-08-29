import React from 'react';
import { Document } from '../types';
import DocumentCard from './DocumentCard';

interface DocumentGridProps {
  documents: Document[];
  selectedIds: string[];
  onToggleSelect: (id: string) => void;
  onSelectDoc: (id: string) => void;
  onRename?: (doc: Document) => void;
  onDelete?: (doc: Document) => void;
  onRestore?: (doc: Document) => void;
  onDownload?: (doc: Document) => void;
  isTrashView?: boolean;
}

export const DocumentGrid: React.FC<DocumentGridProps> = ({
  documents,
  selectedIds,
  onToggleSelect,
  onSelectDoc,
  onRename,
  onDelete,
  onRestore,
  onDownload,
  isTrashView = false
}) => {
  return (
    <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,200px),1fr))] gap-4">
      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          doc={doc}
          isSelected={selectedIds.includes(doc.id)}
          onSelect={() => onToggleSelect(doc.id)}
          onClick={() => onSelectDoc(doc.id)}
          onRename={onRename}
          onDelete={onDelete}
          onRestore={onRestore}
          onDownload={onDownload}
          isTrashView={isTrashView}
        />
      ))}
    </div>
  );
};
export default DocumentGrid;
