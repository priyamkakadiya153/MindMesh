import React, { useState, useEffect } from 'react';

interface MarkdownViewerProps {
  url: string;
}

export const MarkdownViewer: React.FC<MarkdownViewerProps> = ({ url }) => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'preview' | 'source'>('preview');

  useEffect(() => {
    fetch(url)
      .then((res) => res.text())
      .then((text) => {
        setContent(text);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [url]);

  if (loading) {
    return (
      <div className="w-full h-[300px] flex items-center justify-center text-textMuted animate-pulse">
        Loading document preview content...
      </div>
    );
  }

  return (
    <div className="w-full rounded-xl border border-borderColor bg-bgCard backdrop-blur-xl flex flex-col h-[500px]">
      <div className="flex justify-between items-center p-3 border-b border-borderMuted bg-bgHeader">
        <span className="text-xs font-semibold text-textMuted">Markdown Viewer</span>
        <div className="flex bg-bgInput p-0.5 rounded-lg border border-borderMuted">
          <button
            onClick={() => setViewMode('preview')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              viewMode === 'preview' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            Preview
          </button>
          <button
            onClick={() => setViewMode('source')}
            className={`px-3 py-1 rounded-md text-xs font-medium transition ${
              viewMode === 'source' ? 'bg-accent text-white' : 'text-textMuted hover:text-textPrimary'
            }`}
          >
            Source
          </button>
        </div>
      </div>

      <div className="flex-1 p-5 overflow-y-auto text-sm text-textSecondary">
        {viewMode === 'source' ? (
          <pre className="font-mono text-xs whitespace-pre-wrap bg-bgInput p-4 rounded-lg border border-borderMuted text-textSecondary">
            {content}
          </pre>
        ) : (
          <div className="prose max-w-none">
            {/* Basic markdown paragraph converter fallback */}
            {content.split('\n\n').map((para, idx) => {
              if (para.startsWith('#')) {
                const level = para.split(' ')[0].length;
                const text = para.replace(/^#+\s+/, '');
                if (level === 1) return <h1 key={idx} className="text-xl font-bold text-textPrimary mb-3 mt-4">{text}</h1>;
                if (level === 2) return <h2 key={idx} className="text-lg font-bold text-textPrimary mb-2 mt-3">{text}</h2>;
                return <h3 key={idx} className="text-md font-semibold text-textPrimary mb-2 mt-2">{text}</h3>;
              }
              return <p key={idx} className="mb-4 leading-relaxed text-textSecondary">{para}</p>;
            })}
          </div>
        )}
      </div>
    </div>
  );
};
export default MarkdownViewer;
