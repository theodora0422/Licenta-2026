from fastapi import APIRouter

from trace_vizualizer.domain.requests import AnalysisRequest
from trace_vizualizer.domain.responses import AnalysisResponse, ScenarioStep, Finding

router=APIRouter()

@router.post("/analyze",response_model=AnalysisResponse)
async def analyze(request:AnalysisRequest)->AnalysisResponse:
    findings=[]
    scenario=[]
    explanation="No violations were detected"

    if request.check_deadlock:
        findings.append(
            Finding(
                type="deadlock",
                message="Potential deadlock detected between Thread-1 and Thread-2.",
                location="Example.java:23",
            )
        )
        scenario = [
            ScenarioStep(thread="Thread-1", action="acquire", resource="lockA"),
            ScenarioStep(thread="Thread-2", action="acquire", resource="lockB"),
            ScenarioStep(thread="Thread-1", action="wait", resource="lockB"),
            ScenarioStep(thread="Thread-2", action="wait", resource="lockA"),
        ]
        explanation = (
            "Two threads acquire two locks in opposite order, which may lead to a deadlock."
        )

    status = "violation_found" if findings else "ok"
    return AnalysisResponse(
        status=status,
        findings=findings,
        scenario=scenario,
        explanation=explanation,
    )
