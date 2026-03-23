from trace_vizualizer.domain.explanation import ExplanationModel
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult


class FindingNarrator:
    def narrate(self,verification_result:UnifiedVerificationResult):
        selected_property=verification_result.selected_property
        counterexample=verification_result.selected_counterexample
        if verification_result.overall_status=="ok" or selected_property is None:
            return ExplanationModel(
                title="No violation detected",
                summary="No selected property violation was detected in the explored scenarios",
                detailed_steps=[],
                source_references=[],
            )
        if selected_property=="deadlock":
            return self._build_deadlock_narrative(verification_result)
        if selected_property=="data_race":
            return self._build_data_race_narrative(verification_result)
        if selected_property=="mutual_exclusion":
            return self._build_mutual_exclusion_narrative(verification_result)
        if selected_property=="starvation":
            return self._build_starvation_narrative(verification_result)
        return ExplanationModel(
            title="Verification result",
            summary=verification_result.selected_message or "A property violation was detected",
            detailed_steps=[],
            source_references=[],
        )
    def _build_deadlock_narrative(self,verification_result:UnifiedVerificationResult):
        counterexample=verification_result.selected_counterexample
        steps=[]
        if counterexample is not None:
            for step in counterexample.steps:
                steps.append(
                    f"Step {step.step_index}:{step.thread_id} performs"
                    f"{step.event_kind} on {step.original_resource}."
                )
            for thread_id,waited_lock in counterexample.final_state.waiting_for.items():
                if waited_lock is not None:
                    owner=counterexample.final_state.lock_owners.get(waited_lock)
                    if owner is not None:
                        steps.append(
                            f"In the final state, {thread_id} waits for {waited_lock}, which is currently held by {owner}."
                        )
                    else:
                        steps.append(f"In the final state, {thread_id} waits for {waited_lock}.")
        return ExplanationModel(
            title="Deadlock detected",
            summary=verification_result.selected_message or "A deadlock state was detected during bounded exploration.",
            detailed_steps=steps,
            source_references=[],
        )
    def _build_data_race_narrative(self,verification_result:UnifiedVerificationResult):
        counterexample=verification_result.selected_counterexample
        steps=[]
        if counterexample is not None:
            for step in counterexample.steps:
                steps.append(
                    f"Step {step.step_index}: {step.thread_id} performs "
                    f"{step.event_kind} on {step.original_resource}."
                )
        return ExplanationModel(
            title="Data race detected",
            summary=verification_result.selected_message or "A potential data race was detected during bounded exploration",
            detailed_steps=steps,
            source_references=[]
        )
    def _build_mutual_exclusion_narrative(self,verification_result:UnifiedVerificationResult):
        counterexample=verification_result.selected_counterexample
        steps=[]
        if counterexample is not None:
            for step in counterexample.steps:
                steps.append(
                    f"Step {step.step_index}: {step.thread_id} performs {step.event_kind} on {step.original_resource}."
                )
        return ExplanationModel(
            title="Mutual exclusion violation detected",
            summary=verification_result.selected_message or "A mutual exclusion violation was detected during bounded exploration",
            detailed_steps=steps,
            source_references=[],
        )
    def _build_starvation_narrative(self,verification_result:UnifiedVerificationResult):
        counterexample=verification_result.selected_counterexample
        steps=[]
        if counterexample is not None:
            for step in counterexample.steps:
                steps.append(
                    f"Step {step.step_index}: {step.thread_id} performs "
                    f"{step.event_kind} on {step.original_resource}."
                )
        return ExplanationModel(
            title="Starvation indicator detected",
            summary=verification_result.selected_message or "A potential starvation pattern was detected during bounded exploration,",
            detailed_steps=steps,
            source_references=[],
        )
