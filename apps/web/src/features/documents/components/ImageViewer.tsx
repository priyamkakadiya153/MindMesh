import React, { useState } from 'react';

interface ImageViewerProps {
  url: string;
}

export const ImageViewer: React.FC<ImageViewerProps> = ({ url }) => {
  const [zoom, setZoom] = useState(1);

  const zoomIn = () => setZoom((z) => Math.min(3, z + 0.25));
  const zoomOut = () => setZoom((z) => Math.max(0.5, z - 0.25));
  const resetZoom = () => setZoom(1);

  return (
    <div className="relative w-full h-[500px] flex items-center justify-center rounded-xl overflow-hidden border border-borderColor bg-bgCard backdrop-blur-xl">
      <div className="absolute top-4 right-4 z-10 flex gap-2 bg-bgHeader border border-borderColor p-1.5 rounded-xl">
        <button
          onClick={zoomIn}
          className="p-1.5 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover transition"
          title="Zoom In"
        >
          +
        </button>
        <button
          onClick={zoomOut}
          className="p-1.5 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover transition"
          title="Zoom Out"
        >
          -
        </button>
        <button
          onClick={resetZoom}
          className="p-1.5 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover transition text-xs font-semibold"
          title="Reset Zoom"
        >
          100%
        </button>
      </div>

      <div 
        className="transition-transform duration-200 ease-out"
        style={{ transform: `scale(${zoom})` }}
      >
        <img
          src={url}
          alt="Document Preview"
          className="max-w-full max-h-[420px] object-contain rounded-lg shadow-2xl"
        />
      </div>
    </div>
  );
};
export default ImageViewer;
