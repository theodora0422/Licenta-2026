from typing import Optional, List

from pydantic import BaseModel


class SourceReference(BaseModel):
    line:int
    code_snippet:Optional[str]=None
    resource:Optional[str]=None
    thread:Optional[str]=None
    action:Optional[str]=None

class ExplanationModel(BaseModel):
    title:str
    summary:str
    detailed_steps:List[str]
    source_references:List[SourceReference]