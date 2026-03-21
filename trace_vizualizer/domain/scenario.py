from typing import Dict, List, Optional
from pydantic import BaseModel

from trace_vizualizer.domain.model import AbstractEvent, InitialState, ProgramModel


class ExplorationState(BaseModel):
    program_counters: Dict[str, int]
    lock_owners: Dict[str, Optional[str]]
    held_locks: Dict[str, List[str]]
    waiting_for: Dict[str, Optional[str]]

    def state_key(self) -> tuple:
        return (
            tuple(sorted(self.program_counters.items())),
            tuple(sorted(self.lock_owners.items())),
            tuple(
                (thread_id, tuple(locks))
                for thread_id, locks in sorted(self.held_locks.items())
            ),
            tuple(sorted(self.waiting_for.items())),
        )


class ScenarioStepRecord(BaseModel):
    step_index: int
    thread_id: str
    event_id: str
    event_kind: str
    resource_id: str
    original_resource: str
    source_line: int
    expression: Optional[str] = None


class ExecutionScenario(BaseModel):
    scenario_id: str
    steps: List[ScenarioStepRecord]
    final_state: ExplorationState


class ExplorationMetrics(BaseModel):
    visited_state_count: int
    transition_count: int
    generated_scenario_count: int
    max_depth_reached: int


class ScenarioGenerationResult(BaseModel):
    scenarios: List[ExecutionScenario]
    metrics: ExplorationMetrics
    initial_state: ExplorationState
    program_model_snapshot: ProgramModel


def initial_state_to_exploration_state(initial_state: InitialState) -> ExplorationState:
    return ExplorationState(
        program_counters=dict(initial_state.program_counters),
        lock_owners=dict(initial_state.lock_owners),
        held_locks={k: list(v) for k, v in initial_state.held_locks.items()},
        waiting_for=dict(initial_state.waiting_for),
    )