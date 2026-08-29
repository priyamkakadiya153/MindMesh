import { useEffect, useState, useCallback } from 'react';
import * as api from './api';
import { Document, Folder } from './types';

export function useDocumentsList(
  token: string,
  orgId: string,
  workspaceId?: string,
  projectId?: string,
  folderId?: string,
  viewCategory: 'all' | 'recent' | 'favorites' | 'trash' = 'all',
  searchQuery?: string,
  fileType?: string
) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDocs = useCallback(async () => {
    if (!token || !orgId) return;
    try {
      setLoading(true);
      setError(null);
      let data: Document[] = [];
      if (viewCategory === 'recent') {
        data = await api.getRecentDocuments(token, orgId);
      } else if (viewCategory === 'favorites') {
        data = await api.getFavoriteDocuments(token, orgId);
      } else if (viewCategory === 'trash') {
        data = await api.getDocuments(token, orgId, workspaceId, projectId, folderId, searchQuery, fileType, true);
      } else {
        data = await api.getDocuments(token, orgId, workspaceId, projectId, folderId, searchQuery, fileType, false);
      }
      setDocuments(data);
    } catch (e: any) {
      setError(e.message || 'Failed to fetch documents');
    } finally {
      setLoading(false);
    }
  }, [token, orgId, workspaceId, projectId, folderId, viewCategory, searchQuery, fileType]);

  useEffect(() => {
    fetchDocs();
  }, [fetchDocs]);

  return { documents, loading, error, refetch: fetchDocs };
}

export function useFoldersList(token: string, orgId: string, workspaceId: string, parentId?: string) {
  const [folders, setFolders] = useState<Folder[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchFolders = useCallback(async () => {
    if (!token || !orgId || !workspaceId) return;
    try {
      setLoading(true);
      const data = await api.getFolders(token, orgId, workspaceId, parentId);
      setFolders(data);
    } catch (e) {
      console.error("Failed to load folders:", e);
    } finally {
      setLoading(false);
    }
  }, [token, orgId, workspaceId, parentId]);

  useEffect(() => {
    fetchFolders();
  }, [fetchFolders]);

  return { folders, loading, refetch: fetchFolders };
}

export function useDocumentDetails(token: string, orgId: string, docId: string | null) {
  const [document, setDocument] = useState<Document | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDoc = useCallback(async () => {
    if (!docId || !token || !orgId) return;
    try {
      setLoading(true);
      const data = await api.getDocument(token, orgId, docId);
      setDocument(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token, orgId, docId]);

  useEffect(() => {
    if (docId) {
      fetchDoc();
    } else {
      setDocument(null);
    }
  }, [docId, fetchDoc]);

  return { document, loading, error, refetch: fetchDoc };
}

