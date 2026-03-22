from typing import Optional, List

from pydantic import BaseModel

from trace_vizualizer.domain.scenario import ExecutionScenario


class AggregatedFinding(BaseModel):
    property_name:str
    violated:bool
    message:str
    scenario_id:Optional[str]=None

class UnifiedVerificationResult(BaseModel):
    overall_status:str
    selected_property:Optional[str]=None
    selected_message:Optional[str]=None
    selected_counterexample:Optional[ExecutionScenario]=None
    findings:List[AggregatedFinding]
    violated_properties:List[str]
    checked_properties:List[str]