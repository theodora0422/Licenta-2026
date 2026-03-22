from typing import Dict, List, Optional, Set

from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import ExecutionScenario, ScenarioGenerationResult
from trace_vizualizer.domain.verification import VerificationFinding, VerificationResult


class MutualExclusionChecker:
    def check(
        self,
        scenario_generation_result: ScenarioGenerationResult,
    ) -> VerificationResult:
        program_model = scenario_generation_result.program_model_snapshot

        for scenario in scenario_generation_result.scenarios:
            violation_info = self._find_violation_in_scenario(scenario, program_model)
            if violation_info is not None:
                return VerificationResult(
                    deadlock_detected=False,
                    data_race_detected=False,
                    mutual_exclusion_violated=True,
                    findings=[
                        VerificationFinding(
                            property_name="mutual_exclusion",
                            violated=True,
                            message=violation_info["message"],
                            scenario_id=scenario.scenario_id,
                        )
                    ],
                    counterexample=scenario,
                )

        return VerificationResult(
            deadlock_detected=False,
            data_race_detected=False,
            mutual_exclusion_violated=False,
            findings=[
                VerificationFinding(
                    property_name="mutual_exclusion",
                    violated=False,
                    message="No mutual exclusion violation was detected in the explored scenarios.",
                    scenario_id=None,
                )
            ],
            counterexample=None,
        )

    def _find_violation_in_scenario(
        self,
        scenario: ExecutionScenario,
        program_model: ProgramModel,
    ) -> Optional[dict]:
        thread_sequences = {
            sequence.thread_id: sequence.events
            for sequence in program_model.thread_event_sequences
        }

        accesses: List[dict] = []
        thread_held_locks: Dict[str, Set[str]] = {
            sequence.thread_id: set()
            for sequence in program_model.thread_event_sequences
        }

        for step in scenario.steps:
            thread_id = step.thread_id
            event_list = thread_sequences.get(thread_id, [])
            matching_event = next(
                (event for event in event_list if event.event_id == step.event_id),
                None,
            )

            if matching_event is None:
                continue

            if matching_event.kind == "acquire":
                thread_held_locks.setdefault(thread_id, set()).add(matching_event.resource_id)

            elif matching_event.kind == "release":
                thread_held_locks.setdefault(thread_id, set()).discard(matching_event.resource_id)

            elif matching_event.kind in {"read", "write"}:
                accesses.append(
                    {
                        "scenario_step": step,
                        "thread_id": thread_id,
                        "event_kind": matching_event.kind,
                        "resource_id": matching_event.resource_id,
                        "original_resource": matching_event.original_resource,
                        "held_locks": set(thread_held_locks.get(thread_id, set())),
                    }
                )

        for i in range(len(accesses)):
            for j in range(i + 1, len(accesses)):
                left = accesses[i]
                right = accesses[j]

                if left["resource_id"] != right["resource_id"]:
                    continue

                if left["thread_id"] == right["thread_id"]:
                    continue

                if not self._is_critical_conflict(left["event_kind"], right["event_kind"]):
                    continue

                common_locks = left["held_locks"].intersection(right["held_locks"])
                if common_locks:
                    continue

                return {
                    "message": (
                        f"Mutual exclusion violation detected on resource "
                        f"'{left['original_resource']}' between "
                        f"{left['thread_id']} ({left['event_kind']}) and "
                        f"{right['thread_id']} ({right['event_kind']})."
                    ),
                    "left": left,
                    "right": right,
                }

        return None

    def _is_critical_conflict(self, left_kind: str, right_kind: str) -> bool:
        if left_kind == "write" and right_kind in {"read", "write"}:
            return True
        if right_kind == "write" and left_kind in {"read", "write"}:
            return True
        return False