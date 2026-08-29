import React, { useRef, useState } from 'react';

interface UploadCenterProps {
  onFilesSelected: (files: FileList) => void;
}

export const UploadCenter: React.FC<UploadCenterProps> = ({ onFilesSelected }) => {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFilesSelected(e.dataTransfer.files);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      onFilesSelected(e.target.files);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-2xl transition backdrop-blur-xl ${
        dragActive 
          ? 'border-accent bg-accentSubtle' 
          : 'border-borderColor bg-bgCard hover:border-borderHover'
      }`}
    >
      <input
        id="browse-trigger"
        ref={inputRef}
        type="file"
        multiple
        onChange={handleChange}
        className="hidden"
      />
      
      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accentSubtle text-accentText mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
        </svg>
      </div>

      <p className="text-sm font-semibold text-textPrimary mb-1 font-outfit">
        Drag and drop your files here
      </p>
      <p className="text-xs text-textMuted mb-4">
        Supports PDF, DOCX, XLSX, Markdown, HTML up to 50MB
      </p>
      
      <button
        type="button"
        onClick={onButtonClick}
        className="px-4 py-2 text-xs font-semibold rounded-lg bg-accent hover:bg-accentHover text-white transition active:scale-95 shadow-md shadow-accent/20"
      >
        Browse Files
      </button>
    </div>
  );
};
export default UploadCenter;
