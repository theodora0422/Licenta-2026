from typing import List, Set, Tuple

from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import (
    ExecutionScenario,
    ExplorationMetrics,
    ExplorationState,
    ScenarioGenerationResult,
    initial_state_to_exploration_state,
)
from trace_vizualizer.backend_analysis_service.scenario_generator.scenario_collector import ScenarioCollector
from trace_vizualizer.backend_analysis_service.scenario_generator.transition_system import TransitionSystem


class StateExplorer:
    def __init__(self) -> None:
        self.transition_system = TransitionSystem()
        self.scenario_collector = ScenarioCollector()

    def explore(
        self,
        program_model: ProgramModel,
        max_depth: int,
    ) -> ScenarioGenerationResult:
        initial_state = initial_state_to_exploration_state(program_model.initial_state)

        visited_states: Set[tuple] = set()
        scenarios: List[ExecutionScenario] = []

        metrics = ExplorationMetrics(
            visited_state_count=0,
            transition_count=0,
            generated_scenario_count=0,
            max_depth_reached=0,
        )

        self._dfs(
            state=initial_state,
            program_model=program_model,
            max_depth=max_depth,
            current_trace=[],
            visited_states=visited_states,
            scenarios=scenarios,
            metrics=metrics,
        )

        metrics.visited_state_count = len(visited_states)
        metrics.generated_scenario_count = len(scenarios)

        return ScenarioGenerationResult(
            scenarios=scenarios,
            metrics=metrics,
            initial_state=initial_state,
            program_model_snapshot=program_model,
        )

    def _dfs(
        self,
        state: ExplorationState,
        program_model: ProgramModel,
        max_depth: int,
        current_trace: List[tuple],
        visited_states: Set[tuple],
        scenarios: List[ExecutionScenario],
        metrics: ExplorationMetrics,
    ) -> None:
        state_key = state.state_key()
        if state_key in visited_states:
            return

        visited_states.add(state_key)
        metrics.max_depth_reached = max(metrics.max_depth_reached, len(current_trace))

        enabled_transitions = self.transition_system.get_enabled_transitions(state, program_model)

        if not enabled_transitions or len(current_trace) >= max_depth:
            scenario = self.scenario_collector.build_scenario(
                scenario_id=f"scenario_{len(scenarios) + 1}",
                executed_trace=current_trace,
                final_state=state,
            )
            scenarios.append(scenario)
            return

        for thread_id, event in enabled_transitions:
            next_state = self.transition_system.apply_transition(state, thread_id, event)
            metrics.transition_count += 1

            self._dfs(
                state=next_state,
                program_model=program_model,
                max_depth=max_depth,
                current_trace=current_trace + [(thread_id, event)],
                visited_states=set(visited_states),
                scenarios=scenarios,
                metrics=metrics,
            )