from typing import Optional, List

from pydantic import BaseModel


class SourceLocation(BaseModel):
    start_line:int
    start_column:int
    end_line:int
    end_column:int

class ThreadInfo(BaseModel):
    identifier:str
    kind:str
    name:Optional[str]=None
    source_location:SourceLocation

class SynchronizationOperation(BaseModel):
    kind:str
    resource:str
    source_location:SourceLocation

class ConcurrencyExtractionResult(BaseModel):
    threads:List[ThreadInfo]
    synchronization_operations:List[SynchronizationOperation]