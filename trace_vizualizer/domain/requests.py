from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    source_code:str=Field(...,description="Java source code submitted for analysis.")
    check_deadlock: bool=Field(default=False, description="Enable deadlock detection.")
    check_data_race: bool=Field(default=False, description="Enable data race detection.")
    check_starvation: bool=Field(default=False, description="Enable starvation detection.")
    check_mutual_exclusion:bool=Field(
        default=False,
        description="Enable mutual exclusion verification"
    )
    max_depth:int=Field(
        default=10,
        ge=1,
        le=1000,
        description="Maximum exploration depth for scenario generation",
    )