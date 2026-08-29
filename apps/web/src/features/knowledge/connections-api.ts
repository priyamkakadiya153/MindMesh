const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface OverviewItem {
  entity_id: string;
  entity_type: string;
  title: string;
  status?: string;
  project_id?: string;
  reason?: string;
  action?: string;
  entity_name?: string;
  actor_email?: string;
  created_at?: string;
  human_relation: string;
}

export interface ImportantConnection {
  edge_id: string;
  source_id: string;
  source_type: string;
  source_title: string;
  target_id: string;
  target_type: string;
  target_title: string;
  relation_type: string;
  human_relation: string;
  evidence_type: string;
  confidence: number;
}

export interface ConnectionsOverviewResponse {
  has_connections: boolean;
  blocked_work: OverviewItem[];
  recent_decisions: OverviewItem[];
  recent_changes: OverviewItem[];
  important_connections: ImportantConnection[];
}

export interface RelatedItem {
  id: string;
  node_id?: string;
  type: string;
  title: string;
  relation: string;
  confidence: number;
  evidence_type: string;
  deep_link?: string;
}

export interface ProvenanceChainStep {
  type: string;
  id: string;
  title: string;
}

export interface EntityProvenanceInspectorResponse {
  entity_id: string;
  entity_type: string;
  title: string;
  status?: string;
  owner?: string;
  created_at?: string;
  deep_link?: string;
  metadata?: Record<string, any>;
  has_verified_connections?: boolean;
  why_exists?: string;
  connected_project?: RelatedItem;
  supporting_evidence: RelatedItem[];
  related_decisions: RelatedItem[];
  resulting_tasks: RelatedItem[];
  dependencies_and_blockers: RelatedItem[];
  current_impact: RelatedItem[];
  provenance_trail: RelatedItem[];
  provenance_chain: ProvenanceChainStep[];
  grouped_entities: Record<string, RelatedItem[]>;
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
  relation_type: string;
  evidence_type: string;
  confidence: number;
  source_reference?: Record<string, any>;
}

export interface GraphNeighborhoodResponse {
  center_node?: GraphNode;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export async function fetchConnectionsOverview(
  workspaceId?: string,
  token?: string
): Promise<ConnectionsOverviewResponse> {
  const url = workspaceId && workspaceId !== 'all'
    ? `${API_BASE_URL}/knowledge/graph/overview?workspace_id=${workspaceId}`
    : `${API_BASE_URL}/knowledge/graph/overview`;
  
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) throw new Error('Failed to fetch connections overview');
  return res.json();
}

export async function fetchEntityProvenance(
  entityType: string,
  entityId: string,
  token?: string
): Promise<EntityProvenanceInspectorResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/inspector/${entityType}/${entityId}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch entity provenance');
  return res.json();
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

export async function fetchNodeNeighborhood(
  nodeId: string,
  depth: number = 1,
  token?: string
): Promise<GraphNeighborhoodResponse> {
  const res = await fetch(`${API_BASE_URL}/knowledge/graph/${nodeId}/related?depth=${depth}`, {
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch node neighborhood');
  return res.json();
}
