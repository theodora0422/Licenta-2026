from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import HighlightMarker


class HighlightRules:
    def build(self,verification_result:UnifiedVerificationResult,counterexample:ExecutionScenario|None):
        highlights:list[HighlightMarker]=[]
        selected_property=verification_result.selected_property
        if selected_property is None or counterexample is None:
            return highlights
        for step in counterexample.steps:
            highlights.append(
                HighlightMarker(
                    target_type="timeline",
                    target_id=f"timeline-step:{step.step_index}",
                    reason=selected_property,
                )
            )
            if step.original_resource:
                highlights.append(
                    HighlightMarker(
                        target_type="edge",
                        target_id=f"edge:{step.step_index}:thread:{step.thread_id}:resource:{step.original_resource}:{step.event_kind}",
                        reason=selected_property,
                    )

                )
        final_state=counterexample.final_state
        for thread_id, waited_lock in final_state.waiting_for.items():
            if waited_lock is not None:
                highlights.append(
                    HighlightMarker(
                        target_type="edge",
                        target_id=f"wait-edge:{thread_id}:{waited_lock}",
                        reason=selected_property,
                    )
                )
        return highlights