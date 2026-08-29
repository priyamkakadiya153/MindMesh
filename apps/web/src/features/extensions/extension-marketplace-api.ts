const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface ExtensionDefinition {
  extension_id: string;
  name: string;
  description: string;
  type: string;
  version: string;
  publisher: string;
  publisher_verified: boolean;
  category: string;
  capabilities: string[];
  permissions_requested: string[];
  trust_level: string;
  status: string;
}

export interface InstallResponse {
  extension_id: string;
  status: string;
  installation_time: string;
  installed_by: string;
  permissions_granted: string[];
  security_validation: {
    manifest_valid: boolean;
    signature_verified: boolean;
    minimum_permission_verified: boolean;
  };
}

export interface ConnectorSyncResponse {
  connector_id: string;
  sync_mode: string;
  sync_status: string;
  items_processed: number;
  created_count: number;
  updated_count: number;
  duplicates_prevented: number;
  conflicts_detected: Array<{
    conflict_id: string;
    external_id: string;
    mindmesh_id: string;
    external_value: string;
    mindmesh_value: string;
    resolution: string;
    status: string;
  }>;
  data_lineage: {
    source: string;
    external_workspace: string;
    last_sync_timestamp: string;
  };
}

export interface CustomAgentResponse {
  agent_id: string;
  name: string;
  role: string;
  capabilities: string[];
  visibility: string;
  status: string;
  creator: string;
  created_at: string;
  instruction_version: number;
  permissions_assigned: string[];
}

export interface RevokePermissionResponse {
  extension_id: string;
  status: string;
  revoked_by: string;
  revocation_timestamp: string;
  reason: string;
  permissions_active: string[];
  execution_requests_blocked: boolean;
}

export async function fetchMarketplaceExtensions(
  query?: string,
  category?: string,
  token?: string
): Promise<ExtensionDefinition[]> {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (category) params.append('category', category);

  const res = await fetch(`${API_BASE_URL}/extensions/marketplace?${params.toString()}`, {
    method: 'GET',
    headers: getAuthHeaders(token)
  });
  if (!res.ok) throw new Error('Failed to fetch marketplace extensions');
  return res.json();
}

export async function installExtension(
  extensionId: string,
  token?: string
): Promise<InstallResponse> {
  const res = await fetch(`${API_BASE_URL}/extensions/install`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ extension_id: extensionId })
  });
  if (!res.ok) throw new Error('Failed to install extension');
  return res.json();
}

export async function syncKnowledgeConnector(
  connectorId: string,
  syncMode: string = 'INCREMENTAL',
  token?: string
): Promise<ConnectorSyncResponse> {
  const res = await fetch(`${API_BASE_URL}/extensions/connectors/sync`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ connector_id: connectorId, sync_mode: syncMode })
  });
  if (!res.ok) throw new Error('Failed to sync connector');
  return res.json();
}

export async function buildCustomAgent(
  name: string,
  role: str,
  capabilities: string[],
  instructions: string,
  visibility: string = 'WORKSPACE',
  token?: string
): Promise<CustomAgentResponse> {
  const res = await fetch(`${API_BASE_URL}/extensions/agents/builder`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ name, role, capabilities, instructions, visibility })
  });
  if (!res.ok) throw new Error('Failed to build custom agent');
  return res.json();
}

export async function revokeExtensionPermissions(
  extensionId: string,
  reason: string,
  token?: string
): Promise<RevokePermissionResponse> {
  const res = await fetch(`${API_BASE_URL}/extensions/permissions/revoke`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ extension_id: extensionId, reason })
  });
  if (!res.ok) throw new Error('Failed to revoke extension permissions');
  return res.json();
}
