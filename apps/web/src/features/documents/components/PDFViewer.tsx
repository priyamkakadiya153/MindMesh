import React from 'react';

interface PDFViewerProps {
  url: string;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({ url }) => {
  return (
    <div className="w-full h-[500px] rounded-xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-xl">
      <iframe
        src={url}
        className="w-full h-full border-0 bg-transparent"
        title="PDF Preview Viewer"
      />
    </div>
  );
};
export default PDFViewer;
