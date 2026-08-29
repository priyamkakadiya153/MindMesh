const API_BASE_URL = '/api/v1';

function getAuthHeaders(token?: string) {
  const authToken = token || localStorage.getItem('token') || '';
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${authToken}`
  };
}

export interface EvidenceItem {
  id: string;
  source_type: 'DOCUMENT' | 'MESSAGE' | 'TASK' | 'DECISION' | 'PROJECT' | 'TIMELINE_EVENT' | string;
  source_id: string;
  title: string;
  excerpt: string;
  location?: string;
  status: 'AVAILABLE' | 'UPDATED' | 'DELETED' | 'INACCESSIBLE' | 'SUPERSEDED' | string;
  confidence_level: 'STRONG_EVIDENCE' | 'MODERATE_EVIDENCE' | 'LIMITED_EVIDENCE' | string;
  created_at?: string;
  updated_at?: string;
  deep_link?: string;
}

export interface ConflictItem {
  id: string;
  conflict_type: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH';
  title: string;
  summary: string;
  sources: string[];
}

export interface EvidenceVerifyResponse {
  trust_rating: 'STRONG_EVIDENCE' | 'MODERATE_EVIDENCE' | 'LIMITED_EVIDENCE' | 'CONFLICTING_EVIDENCE' | 'SOURCE_UNAVAILABLE' | string;
  evidence_count: number;
  verified_items: EvidenceItem[];
  conflicts: ConflictItem[];
}

export async function verifyEvidence(
  query: str,
  rawEvidence: Record<string, any>,
  token?: string
): Promise<EvidenceVerifyResponse> {
  const res = await fetch(`${API_BASE_URL}/evidence/verify`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ query, raw_evidence: rawEvidence })
  });
  if (!res.ok) throw new Error('Failed to verify evidence citations');
  return res.json();
}
