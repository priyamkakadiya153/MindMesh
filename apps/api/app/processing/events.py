# Processing event hooks trigger targets
import logging

logger = logging.getLogger(__name__)

def on_stage_changed(document_id, stage, status):
    logger.info(f"Document {document_id} transitioned stage to {stage} status: {status}")
