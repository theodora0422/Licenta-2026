from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import TimelineItem


class TimelineBuilder:
    # construieste timeline-ul scenariului;
    # pentru starvation si deadlock adauga pasi derivati din starea finala, de tip wait,
    # ca sa fie mai clar cine nu a progresat / cine asteapta un lock

    def build(
        self,
        counterexample: ExecutionScenario | None,
        verification_result: UnifiedVerificationResult,
    ) -> list[TimelineItem]:
        if counterexample is None:
            return []

        timeline_items = []

        canonical_to_original_resource = self._build_resource_label_mapping(
            counterexample
        )

        step_index = 0
        while step_index < len(counterexample.steps):
            step = counterexample.steps[step_index]

            thread_label = self._format_thread_label(step.thread_id)
            resource_label = self._format_resource_label(
                resource_id=step.resource_id,
                original_resource=step.original_resource,
                canonical_to_original_resource=canonical_to_original_resource,
            )

            label = thread_label + " " + step.event_kind

            if resource_label is not None:
                label = label + " " + resource_label

            timeline_items.append(
                TimelineItem(
                    step_index=step.step_index,
                    thread_id=thread_label,
                    action=step.event_kind,
                    resource=resource_label,
                    line=step.source_line,
                    label=label,
                    derived=False,
                )
            )

            step_index = step_index + 1

        selected_property = verification_result.selected_property

        if selected_property == "starvation" or selected_property == "deadlock":
            self._append_waiting_items_from_final_state(
                timeline_items=timeline_items,
                counterexample=counterexample,
                canonical_to_original_resource=canonical_to_original_resource,
            )

        return timeline_items

    def _append_waiting_items_from_final_state(
        self,
        timeline_items: list[TimelineItem],
        counterexample: ExecutionScenario,
        canonical_to_original_resource: dict[str, str],
    ) -> None:
        final_state = counterexample.final_state
        next_index = len(timeline_items) + 1

        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        pair_index = 0
        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                thread_label = self._format_thread_label(thread_id)
                resource_label = self._format_resource_label(
                    resource_id=waited_lock,
                    original_resource=None,
                    canonical_to_original_resource=canonical_to_original_resource,
                )

                label = thread_label + " wait " + resource_label

                timeline_items.append(
                    TimelineItem(
                        step_index=next_index,
                        thread_id=thread_label,
                        action="wait",
                        resource=resource_label,
                        line=None,
                        label=label,
                        derived=True,
                    )
                )

                next_index = next_index + 1

            pair_index = pair_index + 1

    def _build_resource_label_mapping(
        self,
        counterexample: ExecutionScenario,
    ) -> dict[str, str]:
        mapping = {}

        index = 0
        while index < len(counterexample.steps):
            step = counterexample.steps[index]

            if step.resource_id is not None and step.original_resource is not None:
                mapping[step.resource_id] = step.original_resource

            index = index + 1

        return mapping

    def _format_resource_label(
        self,
        resource_id: str | None,
        original_resource: str | None,
        canonical_to_original_resource: dict[str, str],
    ) -> str | None:
        if resource_id is not None:
            if resource_id in canonical_to_original_resource:
                return canonical_to_original_resource[resource_id]

        if original_resource is not None:
            return original_resource

        return resource_id

    def _format_thread_label(self, thread_id: str) -> str:
        if thread_id.startswith("thread_entity_"):
            suffix = thread_id.replace("thread_entity_", "")
            return "thread_" + suffix

        return thread_id

    def _waiting_sort_key(self, item):
        thread_id, waited_lock = item
        return (thread_id, waited_lock or "")