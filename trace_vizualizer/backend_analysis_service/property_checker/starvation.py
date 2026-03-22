from collections import Counter

from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import ExecutionScenario, ScenarioGenerationResult
from trace_vizualizer.domain.verification import VerificationFinding, VerificationResult


class StarvationChecker:
    def check(
        self,
        scenario_generation_result: ScenarioGenerationResult,
    ) -> VerificationResult:
        program_model = scenario_generation_result.program_model_snapshot

        for scenario in scenario_generation_result.scenarios:
            starvation_info = self._find_starvation_in_scenario(scenario, program_model)
            if starvation_info is not None:
                return VerificationResult(
                    starvation_detected=True,
                    findings=[
                        VerificationFinding(
                            property_name="starvation",
                            violated=True,
                            message=starvation_info["message"],
                            scenario_id=scenario.scenario_id,
                        )
                    ],
                    counterexample=scenario,
                )

        return VerificationResult(
            starvation_detected=False,
            findings=[
                VerificationFinding(
                    property_name="starvation",
                    violated=False,
                    message="No starvation indicator was detected in the explored scenarios.",
                    scenario_id=None,
                )
            ],
            counterexample=None,
        )

    def _find_starvation_in_scenario(
        self,
        scenario: ExecutionScenario,
        program_model: ProgramModel,
    ) -> dict | None:
        step_counts = Counter(step.thread_id for step in scenario.steps)

        unfinished_threads = []
        for sequence in program_model.thread_event_sequences:
            executed_steps = step_counts.get(sequence.thread_id, 0)
            total_steps = len(sequence.events)

            if executed_steps < total_steps:
                unfinished_threads.append(
                    {
                        "thread_id": sequence.thread_id,
                        "executed_steps": executed_steps,
                        "remaining_steps": total_steps - executed_steps,
                        "total_steps": total_steps,
                    }
                )

        if not unfinished_threads:
            return None

        if not scenario.steps:
            return None

        max_progress = max(step_counts.values(), default=0)

        for candidate in unfinished_threads:
            thread_id = candidate["thread_id"]
            executed_steps = candidate["executed_steps"]

            if executed_steps == 0 and max_progress >= 1:
                return {
                    "message": (
                        f"Potential starvation detected: thread '{thread_id}' made no progress "
                        f"while other threads continued execution."
                    ),
                    "thread_id": thread_id,
                }

            if executed_steps < max_progress and candidate["remaining_steps"] > 0:
                progress_gap = max_progress - executed_steps
                if progress_gap >= 2:
                    return {
                        "message": (
                            f"Potential starvation detected: thread '{thread_id}' progressed "
                            f"significantly less than other threads and remained unfinished."
                        ),
                        "thread_id": thread_id,
                    }

        return None