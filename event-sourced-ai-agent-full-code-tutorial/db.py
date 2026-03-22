import json
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///agent_events.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, nullable=False, index=True)
    seq = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False, index=True)
    actor = Column(String, nullable=False)
    payload = Column(Text, nullable=False)  # JSON string
    event_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(engine)


def append_event(run_id: str, seq: int, event_type: str, actor: str, payload: dict) -> AgentEvent:
    """Append an immutable event. Never call this to update existing events."""
    session = Session()
    try:
        event = AgentEvent(
            run_id=run_id,
            seq=seq,
            event_type=event_type,
            actor=actor,
            payload=json.dumps(payload),
        )
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    finally:
        session.close()


def get_run_events(run_id: str) -> list[dict]:
    """Return all events for a run in sequence order."""
    session = Session()
    try:
        rows = (
            session.query(AgentEvent)
            .filter_by(run_id=run_id)
            .order_by(AgentEvent.seq)
            .all()
        )
        return [
            {
                "id": r.id,
                "run_id": r.run_id,
                "seq": r.seq,
                "event_type": r.event_type,
                "actor": r.actor,
                "payload": json.loads(r.payload),
                "event_time": r.event_time.isoformat(),
            }
            for r in rows
        ]
    finally:
        session.close()


def get_all_runs() -> list[str]:
    """Return distinct run IDs ordered by first event time."""
    session = Session()
    try:
        rows = (
            session.query(AgentEvent.run_id)
            .distinct()
            .order_by(AgentEvent.event_time)
            .all()
        )
        return [r.run_id for r in rows]
    finally:
        session.close()
