from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from uuid import UUID

class ContextRanker:
    @staticmethod
    def rank_chunks(
        chunks: List[Dict[str, Any]],
        active_workspace_id: Optional[UUID] = None,
        active_project_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Ranks chunks by combining similarity score with workspace, project, and recency boosts.
        
        Priority ordering:
        High Relevance -> Recent -> Same Project -> Same Workspace -> Org Knowledge -> General Knowledge
        """
        if not chunks:
            return []

        now = datetime.now(timezone.utc)
        ranked = []

        for chunk in chunks:
            # Base score (normalized relevance score between 0.0 and 1.0, default 0.0)
            score = float(chunk.get("score") or 0.0)
            
            # Boost calculations
            boost = 0.0
            
            # 1. Project boost (Same Project is highly prioritized)
            chunk_proj_id = chunk.get("project_id")
            if active_project_id and chunk_proj_id and str(chunk_proj_id) == str(active_project_id):
                boost += 0.35
                
            # 2. Workspace boost (Same Workspace is next prioritized)
            chunk_ws_id = chunk.get("workspace_id")
            if active_workspace_id and chunk_ws_id and str(chunk_ws_id) == str(active_workspace_id):
                boost += 0.20
                
            # 3. Recency boost (Recent documents get a boost)
            created_at = chunk.get("created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    elif isinstance(created_at, datetime):
                        dt = created_at
                    else:
                        dt = None
                        
                    if dt:
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        delta_days = (now - dt).days
                        if delta_days <= 7:
                            boost += 0.15
                        elif delta_days <= 30:
                            boost += 0.08
                except Exception:
                    pass # Ignore formatting errors

            # 4. Source-type priority boost (Original documents & team evidence prioritized)
            src_type = (chunk.get("source_type") or "").lower()
            if src_type == "document":
                boost += 0.25
            elif src_type == "conversation":
                boost += 0.15
            elif src_type in ("task", "project", "decision"):
                boost += 0.10
                    
            # Compute final ranking score
            ranking_score = score + boost
            
            # Store calculated priorities for visibility/debugging
            chunk_copy = chunk.copy()
            chunk_copy["ranking_score"] = round(ranking_score, 4)
            chunk_copy["boost_score"] = round(boost, 4)
            ranked.append(chunk_copy)
            
        # Sort by ranking score descending
        ranked.sort(key=lambda x: x.get("ranking_score", 0.0), reverse=True)
        return ranked
