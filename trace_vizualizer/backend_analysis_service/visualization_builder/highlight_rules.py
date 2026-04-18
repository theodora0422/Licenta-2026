from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import HighlightMarker


class HighlightRules:
    # marchează elementele importante pentru proprietatea selectată


    def build(
        self,
        verification_result: UnifiedVerificationResult,
        counterexample: ExecutionScenario | None,
    ) -> list[HighlightMarker]:
        highlights = []

        selected_property = verification_result.selected_property
        if selected_property is None or counterexample is None:
            return highlights

        step_index = 0
        while step_index < len(counterexample.steps):
            step = counterexample.steps[step_index]

            highlights.append(
                HighlightMarker(
                    target_type="timeline",
                    target_id="timeline-step:" + str(step.step_index),
                    reason=selected_property,
                )
            )

            highlights.append(
                HighlightMarker(
                    target_type="node",
                    target_id="thread:" + step.thread_id,
                    reason=selected_property,
                )
            )

            if step.original_resource is not None:
                highlights.append(
                    HighlightMarker(
                        target_type="node",
                        target_id="resource:" + step.original_resource,
                        reason=selected_property,
                    )
                )

                edge_id = (
                    "edge:" + str(step.step_index)
                    + ":thread:" + step.thread_id
                    + ":resource:" + step.original_resource
                    + ":" + step.event_kind
                )

                highlights.append(
                    HighlightMarker(
                        target_type="edge",
                        target_id=edge_id,
                        reason=selected_property,
                    )
                )

            step_index = step_index + 1

        final_state = counterexample.final_state
        waiting_items = list(final_state.waiting_for.items())

        pair_index = 0
        next_timeline_index = len(counterexample.steps) + 1

        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                highlights.append(
                    HighlightMarker(
                        target_type="timeline",
                        target_id="timeline-step:" + str(next_timeline_index),
                        reason=selected_property,
                    )
                )

                highlights.append(
                    HighlightMarker(
                        target_type="node",
                        target_id="thread:" + thread_id,
                        reason=selected_property,
                    )
                )

                highlights.append(
                    HighlightMarker(
                        target_type="node",
                        target_id="resource:" + waited_lock,
                        reason=selected_property,
                    )
                )

                highlights.append(
                    HighlightMarker(
                        target_type="edge",
                        target_id="wait-edge:" + thread_id + ":" + waited_lock,
                        reason=selected_property,
                    )
                )

                next_timeline_index = next_timeline_index + 1

            pair_index = pair_index + 1

        return highlights