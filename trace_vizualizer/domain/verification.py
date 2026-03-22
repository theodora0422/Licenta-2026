from typing import Optional, List

from pydantic import BaseModel

from trace_vizualizer.domain.scenario import ExecutionScenario


class VerificationFinding(BaseModel):
    property_name:str
    violated:bool
    message:str
    scenario_id:Optional[str]=None
class VerificationResult(BaseModel):
    deadlock_detected:bool=False
    data_race_detected:bool=False
    mutual_exclusion_violated:bool=False
    findings:List[VerificationFinding]
    counterexample:Optional[ExecutionScenario]=None