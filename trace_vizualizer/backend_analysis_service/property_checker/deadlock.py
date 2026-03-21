from trace_vizualizer.backend_analysis_service.scenario_generator.transition_system import TransitionSystem
from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import ScenarioGenerationResult, ExecutionScenario
from trace_vizualizer.domain.verification import VerificationResult, VerificationFinding


class DeadlockChecker:
    def __init__(self):
        self.transition_system=TransitionSystem()
    def check(self,scenario_generation_result:ScenarioGenerationResult)->VerificationResult:
        program_model=scenario_generation_result.program_model_snapshot
        for scenario in scenario_generation_result.scenarios:
            if self._is_deadlock_scenario(scenario,program_model):
                return VerificationResult(
                    deadlock_detected=True,
                    findings=[
                        VerificationFinding(
                            property_name="deadlock",
                            violated=True,
                            message="A potential deadlock was detected during scenario exploration.",
                            scenario_id=scenario.scenario_id,
                        )
                    ],
                    counterexample=scenario,
                )
        return VerificationResult(
            deadlock_detected=False,
            findings=[
                VerificationFinding(
                    property_name="deadlock",
                    violated=False,
                    message="No deadlock state was detected",
                    scenario_id=None,
                )
            ],
            counterexample=None,
        )
    def _is_deadlock_scenario(self,scenario:ExecutionScenario,program_model:ProgramModel):
        final_state=scenario.final_state
        enabled=self.transition_system.get_enabled_transitions(final_state,program_model)
        if enabled:
            return False
        waiting_threads=[
            thread_id for thread_id, waited_lock in final_state.waiting_for.items() if waited_lock is not None
        ]
        if not waiting_threads:
            return False
        unfinished_threads=[
            sequence.thread_id for sequence in program_model.thread_event_sequences if final_state.program_counters.get(sequence.thread_id,0)<len(sequence.events)
        ]
        if not unfinished_threads:
            return False
        return True