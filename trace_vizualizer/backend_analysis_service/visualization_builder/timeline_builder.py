from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import TimelineItem


class TimelineBuilder:
    # construieste timeline ul scenariului; pentru starvation si deadlock aauga pasi derivati din starea finala, de tip wait,
    # ca sa fie mai clar cine nu a progresat
    def build(
        self,
        counterexample: ExecutionScenario | None,
        verification_result: UnifiedVerificationResult,
    ) -> list[TimelineItem]:
        if counterexample is None:
            return []

        timeline_items = []

        step_index = 0
        while step_index < len(counterexample.steps):
            step = counterexample.steps[step_index]
            resource = step.original_resource

            label = step.thread_id + " " + step.event_kind
            if resource is not None:
                label = label + " " + resource

            timeline_items.append(
                TimelineItem(
                    step_index=step.step_index,
                    thread_id=step.thread_id,
                    action=step.event_kind,
                    resource=resource,
                    line=step.source_line,
                    label=label,
                    derived=False,
                )
            )
            step_index = step_index + 1

        selected_property = verification_result.selected_property

        if selected_property == "starvation" or selected_property == "deadlock":
            self._append_waiting_items_from_final_state(
                timeline_items,
                counterexample,
            )

        return timeline_items

    def _append_waiting_items_from_final_state(
        self,
        timeline_items: list[TimelineItem],
        counterexample: ExecutionScenario,
    ) -> None:
        final_state = counterexample.final_state
        next_index = len(timeline_items) + 1

        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        pair_index = 0
        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                label = thread_id + " wait " + waited_lock

                timeline_items.append(
                    TimelineItem(
                        step_index=next_index,
                        thread_id=thread_id,
                        action="wait",
                        resource=waited_lock,
                        line=None,
                        label=label,
                        derived=True,
                    )
                )
                next_index = next_index + 1

            pair_index = pair_index + 1

    def _waiting_sort_key(self, item):
        thread_id, waited_lock = item
        return (thread_id, waited_lock or "")