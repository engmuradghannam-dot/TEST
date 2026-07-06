"""Event Bus on Redis: Pub/Sub + Streams + Consumer Groups + Delayed Events.

- publish():            fire-and-forget pub/sub broadcast
- emit():               durable event via Redis Streams (XADD)
- consume():            consumer-group processing loop with ack + retry
- schedule():           delayed events via sorted set, promoted by pump_delayed()
"""
import json
import logging
import time
import uuid

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

STREAM = "nexus:events"
DELAYED_ZSET = "nexus:events:delayed"
CHANNEL_PREFIX = "nexus:pubsub:"


def _client() -> redis.Redis:
    return redis.Redis.from_url(
        getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )


class EventBus:
    def __init__(self, client: redis.Redis | None = None):
        self.r = client or _client()

    # ── Pub/Sub (ephemeral broadcast) ──────────────────────────────
    def publish(self, channel: str, payload: dict):
        self.r.publish(CHANNEL_PREFIX + channel, json.dumps(payload, default=str))

    def subscribe(self, channel: str):
        ps = self.r.pubsub(ignore_subscribe_messages=True)
        ps.subscribe(CHANNEL_PREFIX + channel)
        return ps

    # ── Streams (durable events) ───────────────────────────────────
    def emit(self, event_type: str, payload: dict, company_id: int | None = None) -> str:
        entry = {
            "id": uuid.uuid4().hex,
            "type": event_type,
            "company_id": str(company_id or ""),
            "payload": json.dumps(payload, default=str),
            "ts": str(time.time()),
        }
        msg_id = self.r.xadd(STREAM, entry, maxlen=100_000, approximate=True)
        logger.debug("event emitted type=%s id=%s", event_type, msg_id)
        return msg_id

    def ensure_group(self, group: str):
        try:
            self.r.xgroup_create(STREAM, group, id="0", mkstream=True)
        except redis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise

    def consume(self, group: str, consumer: str, handler,
                block_ms: int = 5000, batch: int = 32, max_deliveries: int = 5):
        """Blocking consumer loop. handler(event_dict) raising -> retried;
        after max_deliveries the event is dead-lettered."""
        self.ensure_group(group)
        while True:
            resp = self.r.xreadgroup(group, consumer, {STREAM: ">"},
                                     count=batch, block=block_ms)
            if not resp:
                self._reclaim_stale(group, consumer, handler, max_deliveries)
                continue
            for _, messages in resp:
                for msg_id, fields in messages:
                    self._process(group, msg_id, fields, handler, max_deliveries)

    def _process(self, group, msg_id, fields, handler, max_deliveries):
        try:
            event = {**fields, "payload": json.loads(fields.get("payload", "{}"))}
            handler(event)
            self.r.xack(STREAM, group, msg_id)
        except Exception as exc:  # noqa: BLE001
            logger.error("event %s handler failed: %s", msg_id, exc)

    def _reclaim_stale(self, group, consumer, handler, max_deliveries,
                       min_idle_ms: int = 60_000):
        pending = self.r.xpending_range(STREAM, group, "-", "+", count=32)
        for p in pending:
            if p["times_delivered"] >= max_deliveries:
                self.r.xadd(STREAM + ":dead", {"orig_id": p["message_id"]})
                self.r.xack(STREAM, group, p["message_id"])
                logger.error("event %s dead-lettered after %s deliveries",
                             p["message_id"], p["times_delivered"])
            elif p["time_since_delivered"] >= min_idle_ms:
                claimed = self.r.xclaim(STREAM, group, consumer,
                                        min_idle_ms, [p["message_id"]])
                for msg_id, fields in claimed:
                    self._process(group, msg_id, fields, handler, max_deliveries)

    # ── Delayed events ─────────────────────────────────────────────
    def schedule(self, event_type: str, payload: dict, delay_seconds: float,
                 company_id: int | None = None) -> str:
        eid = uuid.uuid4().hex
        body = json.dumps({"id": eid, "type": event_type,
                           "company_id": company_id, "payload": payload}, default=str)
        self.r.zadd(DELAYED_ZSET, {body: time.time() + delay_seconds})
        return eid

    def pump_delayed(self) -> int:
        """Promote due delayed events onto the stream. Call from Celery beat."""
        now = time.time()
        due = self.r.zrangebyscore(DELAYED_ZSET, "-inf", now, start=0, num=100)
        moved = 0
        for body in due:
            if self.r.zrem(DELAYED_ZSET, body):  # atomic claim
                ev = json.loads(body)
                self.emit(ev["type"], ev["payload"], ev.get("company_id"))
                moved += 1
        return moved


bus = EventBus()
