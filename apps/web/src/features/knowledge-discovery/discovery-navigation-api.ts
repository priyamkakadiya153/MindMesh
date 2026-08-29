const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface RelatedItem {
  id: string;
  title: string;
  entity_type: string;
  governance_status: string;
  relationship: string;
  explanation: string;
}

export interface CategorizedRelatedKnowledgeResponse {
  entity_id: string;
  entity_type: string;
  categories: {
    directly_related: RelatedItem[];
    supporting: RelatedItem[];
    affected: RelatedItem[];
    historical: RelatedItem[];
    suggested: RelatedItem[];
  };
}

export interface BreadcrumbItem {
  label: string;
  type: string;
  entity_id: string;
}

export interface KnowledgePathResponse {
  project_id: string;
  project_name: string;
  breadcrumbs: BreadcrumbItem[];
}

export interface BookmarkItem {
  id: string;
  entity_id: string;
  entity_type: string;
  title: string;
  governance_status: string;
  saved_at: string;
}

export async function fetchRelatedKnowledge(
  entityId: string,
  entityType: string = 'DOCUMENT',
  token?: string
): Promise<CategorizedRelatedKnowledgeResponse> {
  const params = new URLSearchParams({ entity_id: entityId, entity_type: entityType });
  const res = await fetch(`${API_BASE_URL}/knowledge/discovery/related?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch related knowledge');
  return res.json();
}

export async function fetchKnowledgePath(
  projectId: string,
  currentEntityId: string,
  token?: string
): Promise<KnowledgePathResponse> {
  const params = new URLSearchParams({ project_id: projectId, current_entity_id: currentEntityId });
  const res = await fetch(`${API_BASE_URL}/knowledge/discovery/path?${params.toString()}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge path');
  return res.json();
}

export async function bookmarkKnowledge(
  entityId: string,
  entityType: string,
  title: string,
  governanceStatus: string = 'CURRENT',
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/knowledge/discovery/bookmark`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      entity_id: entityId,
      entity_type: entityType,
      title: title,
      governance_status: governanceStatus
    })
  });
  if (!res.ok) throw new Error('Failed to bookmark knowledge');
  return res.json();
}

export async function followEntity(
  entityId: string,
  token?: string
): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/knowledge/discovery/follow`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId })
  });
  if (!res.ok) throw new Error('Failed to follow entity');
  return res.json();
}

export async function fetchSavedKnowledge(
  token?: string
): Promise<BookmarkItem[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge/discovery/saved`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch saved knowledge');
  return res.json();
}
