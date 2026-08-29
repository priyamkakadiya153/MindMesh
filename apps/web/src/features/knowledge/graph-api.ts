const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface GraphNode {
  id: string;
  organization_id: string;
  workspace_id?: string;
  project_id?: string;
  node_type: string;
  source_type: string;
  source_id: string;
  title: string;
  metadata?: Record<string, any>;
  deep_link?: string;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relation_type: str;
  evidence_type: 'EXPLICIT_FK' | 'AI_DERIVED' | 'TIMELINE_LINEAGE' | 'SEMANTIC_INFERENCE' | string;
  confidence: number;
  source_reference?: Record<string, any>;
}

export interface GraphRelationshipsResponse {
  center_node?: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface PathDiscoveryResponse {
  path_nodes: GraphNode[];
  hop_count: number;
  explanation: string;
}

export interface RelationshipSuggestion {
  edge_id: string;
  source_title: string;
  target_title: string;
  relation_type: string;
  confidence: number;
  reason: string;
}

export async function searchGraphNodes(
  query: string,
  token?: string
): Promise<GraphNode[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/search?q=${encodeURIComponent(query)}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to search graph nodes');
  return res.json();
}

export async function fetchNodeRelationships(
  nodeId: string,
  depth: number = 1,
  token?: string
): Promise<GraphRelationshipsResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/${nodeId}/related?depth=${depth}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch node relationships');
  return res.json();
}

export async function findRelationshipPath(
  sourceId: string,
  targetId: string,
  token?: string
): Promise<PathDiscoveryResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/path?source_id=${sourceId}&target_id=${targetId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to find relationship path');
  return res.json();
}

export async function fetchRelationshipSuggestions(
  token?: string
): Promise<RelationshipSuggestion[]> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/suggestions`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch relationship suggestions');
  return res.json();
}

export async function acceptRelationshipSuggestion(
  edgeId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/suggestions/accept?edge_id=${edgeId}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to accept relationship suggestion');
}

export async function rejectRelationshipSuggestion(
  edgeId: string,
  token?: string
): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/suggestions/reject?edge_id=${edgeId}`, {
    method: 'POST',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to reject relationship suggestion');
}
