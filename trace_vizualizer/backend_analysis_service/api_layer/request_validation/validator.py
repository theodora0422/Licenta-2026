from trace_vizualizer.domain.requests import AnalysisRequest


class RequestValidationException(Exception):
    def __init__(self,message:str,details:list[str] | None = None):
        self.message=message
        self.details=details or []
        super().__init__(message)

def validate_analysis_request(request:AnalysisRequest)->None:
    errors:list[str]=[]
    if not request.source_code.strip():
        errors.append("Source code must not be empty.")
    at_least_one_property=any([
        request.check_deadlock,
        request.check_data_race,
        request.check_starvation,
        request.check_mutual_exclusion,
    ])
    if not at_least_one_property:
        errors.append("At least one analysis property must be selected")
    if request.max_depth<1:
        errors.append("max_depth must be at least 1")

    if errors:
        raise RequestValidationException(
            message="Invalid analysis request",
            details=errors
        )