from typing import Dict, List, Optional, Set

from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import ExecutionScenario, ScenarioGenerationResult
from trace_vizualizer.domain.verification import VerificationFinding, VerificationResult


class DataRaceChecker:

    def check(
        self,
        scenario_generation_result: ScenarioGenerationResult,
    ) -> VerificationResult:
        program_model = scenario_generation_result.program_model_snapshot

        for scenario in scenario_generation_result.scenarios:
            race_info = self._find_race_in_scenario(scenario, program_model)
            if race_info is not None:
                return VerificationResult(
                    deadlock_detected=False,
                    data_race_detected=True,
                    findings=[
                        VerificationFinding(
                            property_name="data_race",
                            violated=True,
                            message=race_info["message"],
                            scenario_id=scenario.scenario_id,
                        )
                    ],
                    counterexample=scenario,
                )

        return VerificationResult(
            deadlock_detected=False,
            data_race_detected=False,
            findings=[
                VerificationFinding(
                    property_name="data_race",
                    violated=False,
                    message="No data race was detected in the explored scenarios.",
                    scenario_id=None,
                )
            ],
            counterexample=None,
        )

    def _find_race_in_scenario(
        self,
        scenario: ExecutionScenario,
        program_model: ProgramModel,
    ) -> Optional[dict]:
        thread_sequences = {
            sequence.thread_id: sequence.events
            for sequence in program_model.thread_event_sequences
        }

        # Reconstruim lock-urile ținute de fiecare thread la fiecare acces read/write.
        held_locks_by_step: List[dict] = []
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
                held_locks_by_step.append(
                    {
                        "scenario_step": step,
                        "thread_id": thread_id,
                        "event_kind": matching_event.kind,
                        "resource_id": matching_event.resource_id,
                        "original_resource": matching_event.original_resource,
                        "held_locks": set(thread_held_locks.get(thread_id, set())),
                    }
                )

        for i in range(len(held_locks_by_step)):
            for j in range(i + 1, len(held_locks_by_step)):
                left = held_locks_by_step[i]
                right = held_locks_by_step[j]

                if left["resource_id"] != right["resource_id"]:
                    continue

                if left["thread_id"] == right["thread_id"]:
                    continue

                if not self._is_conflicting_access(left["event_kind"], right["event_kind"]):
                    continue

                common_locks = left["held_locks"].intersection(right["held_locks"])
                if common_locks:
                    continue

                return {
                    "message": (
                        f"Potential data race detected on resource "
                        f"'{left['original_resource']}' between "
                        f"{left['thread_id']} ({left['event_kind']}) and "
                        f"{right['thread_id']} ({right['event_kind']})."
                    ),
                    "left": left,
                    "right": right,
                }

        return None

    def _is_conflicting_access(self, left_kind: str, right_kind: str) -> bool:
        if left_kind == "write" and right_kind in {"read", "write"}:
            return True
        if right_kind == "write" and left_kind in {"read", "write"}:
            return True
        return False