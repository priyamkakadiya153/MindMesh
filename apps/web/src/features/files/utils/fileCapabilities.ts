export type PreviewType =
  | 'pdf'
  | 'image'
  | 'text'
  | 'code'
  | 'embroidery'
  | 'audio'
  | 'video'
  | 'archive'
  | 'document'
  | 'generic';

export interface FileCapabilities {
  canPreview: boolean;
  previewType: PreviewType;
  canDownload: boolean;
  canExtractText: boolean;
  categoryLabel: string;
  iconType: 'pdf' | 'image' | 'text' | 'code' | 'embroidery' | 'audio' | 'video' | 'archive' | 'document' | 'generic';
}

export function detectFileType(filename: string = '', mimeType: string = ''): FileCapabilities {
  const cleanName = filename.trim();
  const ext = cleanName.split('.').pop()?.toLowerCase() || '';
  const mime = mimeType.trim().toLowerCase();

  // 1. Embroidery Formats (Tajima DST, PES, JEF, EXP, VP3, XXX, PEC, HUS, SEW)
  const embroideryExtensions = ['dst', 'pes', 'jef', 'exp', 'vp3', 'xxx', 'pec', 'hus', 'sew'];
  if (embroideryExtensions.includes(ext) || mime.includes('embroidery') || mime.includes('tajima')) {
    return {
      canPreview: true,
      previewType: 'embroidery',
      canDownload: true,
      canExtractText: false,
      categoryLabel: 'Embroidery Design',
      iconType: 'embroidery'
    };
  }

  // 2. PDF Documents
  if (ext === 'pdf' || mime.includes('pdf')) {
    return {
      canPreview: true,
      previewType: 'pdf',
      canDownload: true,
      canExtractText: true,
      categoryLabel: 'PDF Document',
      iconType: 'pdf'
    };
  }

  // 3. Images
  const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'bmp', 'ico', 'tif', 'tiff'];
  if (imageExtensions.includes(ext) || mime.startsWith('image/')) {
    return {
      canPreview: true,
      previewType: 'image',
      canDownload: true,
      canExtractText: false,
      categoryLabel: 'Image',
      iconType: 'image'
    };
  }

  // 4. Code & Text Files
  const codeExtensions = [
    'js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cpp', 'c', 'h', 'cs', 'go', 'rs',
    'json', 'xml', 'html', 'css', 'scss', 'sql', 'sh', 'yaml', 'yml', 'toml', 'ini', 'env'
  ];
  if (codeExtensions.includes(ext) || mime.includes('json') || mime.includes('javascript') || mime.includes('typescript') || mime.includes('python')) {
    return {
      canPreview: true,
      previewType: 'code',
      canDownload: true,
      canExtractText: true,
      categoryLabel: 'Code File',
      iconType: 'code'
    };
  }

  const textExtensions = ['txt', 'md', 'csv', 'log', 'rtf', 'tsv'];
  if (textExtensions.includes(ext) || mime.startsWith('text/')) {
    return {
      canPreview: true,
      previewType: 'text',
      canDownload: true,
      canExtractText: true,
      categoryLabel: 'Text Document',
      iconType: 'text'
    };
  }

  // 5. Audio Files
  const audioExtensions = ['mp3', 'wav', 'ogg', 'aac', 'flac', 'm4a'];
  if (audioExtensions.includes(ext) || mime.startsWith('audio/')) {
    return {
      canPreview: true,
      previewType: 'audio',
      canDownload: true,
      canExtractText: false,
      categoryLabel: 'Audio File',
      iconType: 'audio'
    };
  }

  // 6. Video Files
  const videoExtensions = ['mp4', 'webm', 'ogv', 'mov', 'avi', 'mkv'];
  if (videoExtensions.includes(ext) || mime.startsWith('video/')) {
    return {
      canPreview: true,
      previewType: 'video',
      canDownload: true,
      canExtractText: false,
      categoryLabel: 'Video File',
      iconType: 'video'
    };
  }

  // 7. Archives
  const archiveExtensions = ['zip', 'rar', '7z', 'tar', 'gz', 'tgz'];
  if (archiveExtensions.includes(ext) || mime.includes('zip') || mime.includes('tar') || mime.includes('compressed')) {
    return {
      canPreview: true,
      previewType: 'generic',
      canDownload: true,
      canExtractText: false,
      categoryLabel: 'Archive File',
      iconType: 'archive'
    };
  }

  // 8. Office Documents (DOC, DOCX, XLS, XLSX, PPT, PPTX)
  const docExtensions = ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'];
  if (docExtensions.includes(ext) || mime.includes('word') || mime.includes('spreadsheet') || mime.includes('officedocument')) {
    return {
      canPreview: true,
      previewType: 'generic',
      canDownload: true,
      canExtractText: true,
      categoryLabel: 'Office Document',
      iconType: 'document'
    };
  }

  // 9. Generic / Proprietary Binary File Fallback
  return {
    canPreview: true, // Universal preview card
    previewType: 'generic',
    canDownload: true,
    canExtractText: false,
    categoryLabel: ext.toUpperCase() ? `${ext.toUpperCase()} File` : 'Binary File',
    iconType: 'generic'
  };
}
