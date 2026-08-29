export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB

export const SUPPORTED_EXTENSIONS = new Set([
  'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx',
  'txt', 'csv', 'json', 'html', 'css', 'js', 'ts', 'java', 'cpp',
  'zip', 'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg', 'md'
]);

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

export function validateDocumentFile(
  file: File,
  existingFilenames: string[] = []
): ValidationResult {
  if (!file) {
    return { valid: false, error: 'No file selected.' };
  }

  // Size validation
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return { valid: false, error: `File exceeds 50 MB limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).` };
  }

  // Extension validation
  const ext = file.name.split('.').pop()?.toLowerCase() || '';
  if (!ext || !SUPPORTED_EXTENSIONS.has(ext)) {
    return { valid: false, error: `Unsupported file type (.${ext || 'unknown'}).` };
  }

  // Duplicate check
  if (existingFilenames.includes(file.name)) {
    return { valid: false, error: `Duplicate upload: "${file.name}" already exists.` };
  }

  return { valid: true };
}

export function formatHumanReadableError(error: any): string {
  if (!error) return 'An unknown error occurred.';
  const msg = typeof error === 'string' ? error : error.message || String(error);

  if (msg.includes('Network Error') || msg.includes('Failed to fetch') || msg.includes('NetworkError')) {
    return 'Network connection lost. Please check your internet connection.';
  }
  if (msg.includes('413') || msg.toLowerCase().includes('payload too large') || msg.toLowerCase().includes('too large')) {
    return 'File exceeds 50 MB server limit.';
  }
  if (msg.includes('401') || msg.includes('403') || msg.toLowerCase().includes('unauthorized') || msg.toLowerCase().includes('permission')) {
    return 'Permission denied. You do not have access to upload documents here.';
  }
  if (msg.includes('507') || msg.toLowerCase().includes('insufficient storage') || msg.toLowerCase().includes('storage unavailable')) {
    return 'Storage limit exceeded or storage unavailable.';
  }

  return msg;
}
