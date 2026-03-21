from typing import Dict, List, Optional
from pydantic import BaseModel


class SourceLocation(BaseModel):
    start_line: int
    start_column: int
    end_line: int
    end_column: int


class ThreadInfo(BaseModel):
    identifier: str
    kind: str
    name: Optional[str] = None
    source_location: SourceLocation


class SynchronizationOperation(BaseModel):
    kind: str
    resource: str
    source_location: SourceLocation
    expression: Optional[str] = None


class SharedAccessOperation(BaseModel):
    kind: str
    resource: str
    expression: str
    source_location: SourceLocation


class ConcurrencyIR(BaseModel):
    threads: List[ThreadInfo]
    synchronization_operations: List[SynchronizationOperation]
    shared_access_operations: List[SharedAccessOperation]


class CanonicalThread(BaseModel):
    canonical_id: str
    original_identifier: str
    original_name: Optional[str] = None
    kind: str
    source_location: SourceLocation


class CanonicalSynchronizationOperation(BaseModel):
    kind: str
    canonical_resource_id: str
    original_resource: str
    source_location: SourceLocation
    expression: Optional[str] = None


class CanonicalSharedAccessOperation(BaseModel):
    kind: str
    canonical_resource_id: str
    original_resource: str
    expression: str
    source_location: SourceLocation


class CanonicalConcurrencyIR(BaseModel):
    threads: List[CanonicalThread]
    synchronization_operations: List[CanonicalSynchronizationOperation]
    shared_access_operations: List[CanonicalSharedAccessOperation]
    thread_mapping: Dict[str, str]
    synchronization_resource_mapping: Dict[str, str]
    shared_resource_mapping: Dict[str, str]