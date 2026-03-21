from typing import Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel

from trace_vizualizer.domain.concurrency import SourceLocation


EventKind = Literal["acquire", "release", "read", "write"]


class AbstractEvent(BaseModel):
    event_id: str
    thread_id: str
    kind: EventKind
    resource_id: str
    original_resource: str
    source_location: SourceLocation
    expression: Optional[str] = None


class ThreadEventSequence(BaseModel):
    thread_id: str
    thread_name: Optional[str] = None
    events: List[AbstractEvent]


class InitialState(BaseModel):
    program_counters: Dict[str, int]
    lock_owners: Dict[str, Optional[str]]
    held_locks: Dict[str, List[str]]
    waiting_for: Dict[str, Optional[str]]


class ProgramModel(BaseModel):
    thread_event_sequences: List[ThreadEventSequence]
    initial_state: InitialState
    thread_count: int
    event_count: int
    lock_ids: List[str]
    shared_resource_ids: List[str]


class PendingEvent(BaseModel):
    thread_id: str
    thread_name: Optional[str] = None
    kind: EventKind
    resource_id: str
    original_resource: str
    source_location: SourceLocation
    expression: Optional[str] = None
    order_line: int
    order_column: int
    phase_priority: int