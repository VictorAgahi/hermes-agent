import json
import time
import uuid
from typing import Optional
from redis.asyncio import Redis

try:
    import uuid_utils
    def generate_uuid() -> str:
        return str(uuid_utils.uuid7())
except ImportError:
    def generate_uuid() -> str:
        return str(uuid.uuid4())

class HermesBusClient:
    """Client haute performance pour l'injection d'événements dans Redis Streams."""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def publish(
        self,
        stream: str,
        event_type: str,
        idempotency_key: str,
        protobuf_payload: bytes,
        target_worker: str,
        trace_id: Optional[str] = None
    ) -> str:
        """
        Injecte un événement selon le format d'enveloppe hybride officiel Hermes.
        Retourne l'event_id.
        """
        event_id = generate_uuid()
        current_trace_id = trace_id or event_id

        meta_header = {
            "event_id": event_id,
            "trace_id": current_trace_id,
            "event_type": event_type,
            "idempotency_key": idempotency_key,
            "origin_service": "hermes-core",
            "target_worker": target_worker,
            "retry_count": 0,
            "created_at_ms": int(time.time() * 1000)
        }

        await self.redis.xadd(
            name=stream,
            fields={
                "meta": json.dumps(meta_header),
                "data": protobuf_payload
            },
            maxlen=1000,
            approximate=True
        )

        return event_id
