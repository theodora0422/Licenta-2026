from pydantic import BaseModel
from typing import List,Optional

from trace_vizualizer.domain.explanation import ExplanationModel
from trace_vizualizer.domain.parsing import ParsingResult
from trace_vizualizer.domain.visualization import VisualizationModel


class Finding(BaseModel):
    type:str
    message:str
    location:Optional[str]=None

class ScenarioStep(BaseModel):
    thread:str
    action:str
    resource:Optional[str]=None

class AnalysisResponse(BaseModel):
    status:str
    findings:List[Finding]
    scenario:List[ScenarioStep]
    explanation:str
    parsing:Optional[ParsingResult]=None
    structured_explanation:Optional[ExplanationModel]=None
    visualization:Optional[VisualizationModel]=None