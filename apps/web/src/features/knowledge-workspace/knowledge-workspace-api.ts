const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ContinueNavigationItem {
  entity_id: string;
  entity_type: string;
  title: string;
  project_name: string;
  trust_label: string;
  last_accessed_at: string;
}

export interface NeedsAttentionItem {
  type: string;
  title: string;
  reason: string;
}

export interface KnowledgeHomeResponse {
  continue_where_you_left_off: ContinueNavigationItem[];
  recently_updated: Array<{ entity_id: string; title: string; update_summary: string; updated_at: string }>;
  needs_attention: NeedsAttentionItem[];
  saved_count: number;
  followed_projects: string[];
}

export interface CollectionItemReference {
  entity_id: string;
  type: string;
  title: string;
}

export interface CollectionResponse {
  collection_id: string;
  name: string;
  collection_type: string;
  description: string;
  smart_rule?: string;
  owner_id: string;
  item_references: CollectionItemReference[];
  created_at: string;
}

export interface ProjectHubResponse {
  project_id: string;
  project_name: string;
  description: string;
  overview: string;
  documents: Array<{ id: string; title: string; status: string; version: string }>;
  decisions: Array<{ id: string; title: string; status: string }>;
  tasks: Array<{ id: string; title: string; status: string }>;
  research_briefs: Array<{ id: string; topic: string; findings_count: number }>;
  knowledge_map_nodes: Array<{ id: string; label: string; type: string }>;
  knowledge_map_edges: Array<{ source: string; target: string; relation: string }>;
}

export async function fetchKnowledgeHome(
  projectId?: string,
  token?: string
): Promise<KnowledgeHomeResponse> {
  const url = projectId ? `${API_BASE_URL}/workspace-experience/home?project_id=${projectId}` : `${API_BASE_URL}/workspace-experience/home`;
  const res = await fetch(url, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch knowledge home');
  return res.json();
}

export async function createCollection(
  name: str,
  collectionType: string = 'PERSONAL',
  description?: string,
  smartRule?: string,
  token?: string
): Promise<CollectionResponse> {
  const res = await fetch(`${API_BASE_URL}/workspace-experience/collections`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ name, collection_type: collectionType, description, smart_rule: smartRule })
  });
  if (!res.ok) throw new Error('Failed to create collection');
  return res.json();
}

export async function fetchProjectKnowledgeHub(
  projectId: string,
  token?: string
): Promise<ProjectHubResponse> {
  const res = await fetch(`${API_BASE_URL}/workspace-experience/project-hub/${projectId}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch project hub');
  return res.json();
}

export async function saveKnowledgeItem(
  entityId: string,
  entityType: string,
  title: string,
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/workspace-experience/save-item`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ entity_id: entityId, entity_type: entityType, title })
  });
  if (!res.ok) throw new Error('Failed to save item');
  return res.json();
}

export async function attachKnowledgeReference(
  targetType: string,
  targetId: string,
  referencedEntityId: string,
  referencedEntityType: string,
  relationshipType: string = 'SUPPORTS',
  token?: string
): Promise<{ success: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/workspace-experience/attach-item`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      target_type: targetType,
      target_id: targetId,
      referenced_entity_id: referencedEntityId,
      referenced_entity_type: referencedEntityType,
      relationship_type: relationshipType
    })
  });
  if (!res.ok) throw new Error('Failed to attach reference');
  return res.json();
}
