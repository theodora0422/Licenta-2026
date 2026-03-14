from pydantic import BaseModel
from typing import List, Optional

class ASTDiagnostic(BaseModel):
    message: str
    line: Optional[int]=None
    column:Optional[int]=None
    severity:str="error"

class ParsingResult(BaseModel):
    ast_root_type:str
    diagnostics:List[ASTDiagnostic]
    has_syntax_errors:bool