import { create } from 'zustand';
import { UploadQueueItem } from './types';

interface DocumentsState {
  currentFolder: string | null;
  currentDocumentId: string | null;
  selectedDocumentIds: string[];
  uploadQueue: UploadQueueItem[];
  previewOpen: boolean;
  viewCategory: 'all' | 'recent' | 'favorites' | 'trash';
  viewMode: 'grid' | 'list';
  filters: {
    search: string;
    fileType: string;
    status: string;
  };
  sorting: {
    field: 'name' | 'date' | 'size' | 'modified';
    order: 'asc' | 'desc';
  };
  
  setCurrentFolder: (folder: string | null) => void;
  setCurrentDocumentId: (id: string | null) => void;
  setSelectedDocumentIds: (ids: string[]) => void;
  toggleSelectDocumentId: (id: string) => void;
  addUploadQueueItem: (item: UploadQueueItem) => void;
  updateUploadProgress: (id: string, progress: number, status?: UploadQueueItem['status'], speed?: string, remainingTime?: string, error?: string) => void;
  clearUploadQueue: () => void;
  clearCompletedQueue: () => void;
  clearFailedQueue: () => void;
  removeUploadQueueItem: (id: string) => void;
  setPreviewOpen: (open: boolean) => void;
  setViewCategory: (cat: 'all' | 'recent' | 'favorites' | 'trash') => void;
  setViewMode: (mode: 'grid' | 'list') => void;
  setFilters: (filters: Partial<DocumentsState['filters']>) => void;
  setSorting: (sorting: Partial<DocumentsState['sorting']>) => void;
}

export const useDocumentsStore = create<DocumentsState>((set) => ({
  currentFolder: null,
  currentDocumentId: null,
  selectedDocumentIds: [],
  uploadQueue: [],
  previewOpen: false,
  viewCategory: 'all',
  viewMode: 'grid',
  filters: {
    search: '',
    fileType: 'all',
    status: 'all',
  },
  sorting: {
    field: 'date',
    order: 'desc',
  },

  setCurrentFolder: (folder) => set({ currentFolder: folder }),
  setCurrentDocumentId: (id) => set({ currentDocumentId: id }),
  setSelectedDocumentIds: (ids) => set({ selectedDocumentIds: ids }),
  toggleSelectDocumentId: (id) => set((state) => {
    const exists = state.selectedDocumentIds.includes(id);
    return {
      selectedDocumentIds: exists
        ? state.selectedDocumentIds.filter((item) => item !== id)
        : [...state.selectedDocumentIds, id]
    };
  }),
  addUploadQueueItem: (item) => set((state) => ({
    uploadQueue: [...state.uploadQueue, item]
  })),
  updateUploadProgress: (id, progress, status, speed, remainingTime, error) => set((state) => ({
    uploadQueue: state.uploadQueue.map((item) =>
      item.id === id ? { ...item, progress, ...(status && { status }), ...(speed && { speed }), ...(remainingTime && { remainingTime }), ...(error && { error }) } : item
    )
  })),
  clearUploadQueue: () => set({ uploadQueue: [] }),
  clearCompletedQueue: () => set((state) => ({
    uploadQueue: state.uploadQueue.filter((item) => item.status !== 'completed')
  })),
  clearFailedQueue: () => set((state) => ({
    uploadQueue: state.uploadQueue.filter((item) => item.status !== 'failed' && item.status !== 'cancelled')
  })),
  removeUploadQueueItem: (id) => set((state) => ({
    uploadQueue: state.uploadQueue.filter((item) => item.id !== id)
  })),
  setPreviewOpen: (open) => set({ previewOpen: open }),
  setViewCategory: (cat) => set({ viewCategory: cat }),
  setViewMode: (mode) => set({ viewMode: mode }),
  setFilters: (filters) => set((state) => ({
    filters: { ...state.filters, ...filters }
  })),
  setSorting: (sorting) => set((state) => ({
    sorting: { ...state.sorting, ...sorting }
  })),
}));

