from trace_vizualizer.domain.requests import AnalysisRequest
from trace_vizualizer.domain.responses import AnalysisResponse, Finding, ScenarioStep


class AnalysisCoordinator:
    def run_analysis(self,request:AnalysisRequest)->AnalysisResponse:
        findings=[]
        scenario=[]
        explanation="No concurrency violation detected in the mock analysis"
        status="ok"

        if request.check_deadlock:
            findings=[
                Finding(
                    type="deadlock",
                    message="Potential deadlock detected between Thread 1 and Thread 2",
                    location="Example.java:23"
                )
            ]
            scenario=[
                ScenarioStep(thread="Thread-1", action="acquire", resource="lockA"),
                ScenarioStep(thread="Thread-2", action="acquire", resource="lockB"),
                ScenarioStep(thread="Thread-1", action="wait", resource="lockB"),
                ScenarioStep(thread="Thread-2", action="wait", resource="lockA"),
            ]
            explanation = (
                "Two threads acquire different locks and then wait for each other, "
                "which may lead to a circular wait condition."
            )
            status = "violation_found"
        return AnalysisResponse(
            status=status,
            findings=findings,
            scenario=scenario,
            explanation=explanation,
        )