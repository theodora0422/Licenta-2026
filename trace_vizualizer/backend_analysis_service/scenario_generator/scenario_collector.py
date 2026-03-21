from typing import List

from trace_vizualizer.domain.model import AbstractEvent
from trace_vizualizer.domain.scenario import (
    ExecutionScenario,
    ExplorationState,
    ScenarioStepRecord,
)


class ScenarioCollector:

    def build_scenario(
        self,
        scenario_id: str,
        executed_trace: List[tuple[str, AbstractEvent]],
        final_state: ExplorationState,
    ) -> ExecutionScenario:
        steps = [
            ScenarioStepRecord(
                step_index=index + 1,
                thread_id=thread_id,
                event_id=event.event_id,
                event_kind=event.kind,
                resource_id=event.resource_id,
                original_resource=event.original_resource,
                source_line=event.source_location.start_line,
                expression=event.expression,
            )
            for index, (thread_id, event) in enumerate(executed_trace)
        ]

        return ExecutionScenario(
            scenario_id=scenario_id,
            steps=steps,
            final_state=final_state,
        )