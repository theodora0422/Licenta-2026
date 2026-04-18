from trace_vizualizer.domain.explanation import ExplanationModel
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult


class FindingNarrator:
    def narrate(self, verification_result: UnifiedVerificationResult) -> ExplanationModel:
        selected_property = verification_result.selected_property

        if verification_result.overall_status == "ok" or selected_property is None:
            return ExplanationModel(
                title="No violation detected",
                summary="No selected property violation was detected in the explored scenarios.",
                detailed_steps=[],
                source_references=[],
            )

        if selected_property == "deadlock":
            return self._build_deadlock_narrative(verification_result)

        if selected_property == "starvation":
            return self._build_starvation_narrative(verification_result)

        if selected_property == "data_race":
            return self._build_data_race_narrative(verification_result)

        if selected_property == "mutual_exclusion":
            return self._build_mutual_exclusion_narrative(verification_result)

        return ExplanationModel(
            title="Verification result",
            summary=verification_result.selected_message or "A property violation was detected.",
            detailed_steps=[],
            source_references=[],
        )

    def _build_deadlock_narrative(
        self,
        verification_result: UnifiedVerificationResult,
    ) -> ExplanationModel:
        counterexample = verification_result.selected_counterexample
        detailed_steps = []

        if counterexample is not None:
            step_index = 0
            while step_index < len(counterexample.steps):
                step = counterexample.steps[step_index]

                detailed_steps.append(
                    "Step "
                    + str(step.step_index)
                    + ": "
                    + step.thread_id
                    + " acquires or attempts to acquire "
                    + str(step.original_resource)
                    + "."
                )

                step_index = step_index + 1

            final_state = counterexample.final_state
            waiting_items = list(final_state.waiting_for.items())
            waiting_items.sort(key=self._waiting_sort_key)

            pair_index = 0
            while pair_index < len(waiting_items):
                thread_id, waited_lock = waiting_items[pair_index]

                if waited_lock is not None:
                    owner = final_state.lock_owners.get(waited_lock)

                    if owner is not None:
                        detailed_steps.append(
                            thread_id
                            + " is waiting for "
                            + waited_lock
                            + ", which is currently held by "
                            + owner
                            + "."
                        )
                    else:
                        detailed_steps.append(
                            thread_id
                            + " is waiting for "
                            + waited_lock
                            + "."
                        )

                pair_index = pair_index + 1

            cycle_description = self._build_deadlock_cycle_description(final_state)
            if cycle_description is not None:
                detailed_steps.append(cycle_description)

        return ExplanationModel(
            title="Deadlock detected",
            summary=verification_result.selected_message or
            "A deadlock state was detected during bounded exploration.",
            detailed_steps=detailed_steps,
            source_references=[],
        )

    def _build_starvation_narrative(
        self,
        verification_result: UnifiedVerificationResult,
    ) -> ExplanationModel:
        counterexample = verification_result.selected_counterexample
        detailed_steps = []

        if counterexample is not None:
            step_index = 0
            while step_index < len(counterexample.steps):
                step = counterexample.steps[step_index]

                detailed_steps.append(
                    "Step "
                    + str(step.step_index)
                    + ": "
                    + step.thread_id
                    + " performs "
                    + step.event_kind
                    + " on "
                    + str(step.original_resource)
                    + "."
                )

                step_index = step_index + 1

            final_state = counterexample.final_state

            progress_items = list(final_state.program_counters.items())
            progress_items.sort(key=self._progress_sort_key)

            progress_index = 0
            while progress_index < len(progress_items):
                thread_id, program_counter = progress_items[progress_index]
                detailed_steps.append(
                    "In the final state, "
                    + thread_id
                    + " reached program counter "
                    + str(program_counter)
                    + "."
                )
                progress_index = progress_index + 1

            waiting_items = list(final_state.waiting_for.items())
            waiting_items.sort(key=self._waiting_sort_key)

            pair_index = 0
            while pair_index < len(waiting_items):
                thread_id, waited_lock = waiting_items[pair_index]

                if waited_lock is not None:
                    owner = final_state.lock_owners.get(waited_lock)

                    if owner is not None:
                        detailed_steps.append(
                            thread_id
                            + " is still waiting for "
                            + waited_lock
                            + ", which is currently held by "
                            + owner
                            + "."
                        )
                    else:
                        detailed_steps.append(
                            thread_id
                            + " is still waiting for "
                            + waited_lock
                            + "."
                        )

                pair_index = pair_index + 1

            starvation_summary = self._build_starvation_summary(final_state)
            if starvation_summary is not None:
                detailed_steps.append(starvation_summary)

        return ExplanationModel(
            title="Starvation indicator detected",
            summary=verification_result.selected_message or
            "A potential starvation pattern was detected during bounded exploration.",
            detailed_steps=detailed_steps,
            source_references=[],
        )

    def _build_data_race_narrative(
        self,
        verification_result: UnifiedVerificationResult,
    ) -> ExplanationModel:
        counterexample = verification_result.selected_counterexample
        detailed_steps = []

        if counterexample is not None:
            step_index = 0
            while step_index < len(counterexample.steps):
                step = counterexample.steps[step_index]

                detailed_steps.append(
                    "Step "
                    + str(step.step_index)
                    + ": "
                    + step.thread_id
                    + " performs "
                    + step.event_kind
                    + " on "
                    + str(step.original_resource)
                    + "."
                )

                step_index = step_index + 1

            race_summary = self._build_conflicting_access_summary(
                counterexample,
                "data race",
            )
            if race_summary is not None:
                detailed_steps.append(race_summary)

        return ExplanationModel(
            title="Data race detected",
            summary=verification_result.selected_message or
            "A potential data race was detected during bounded exploration.",
            detailed_steps=detailed_steps,
            source_references=[],
        )

    def _build_mutual_exclusion_narrative(
        self,
        verification_result: UnifiedVerificationResult,
    ) -> ExplanationModel:
        counterexample = verification_result.selected_counterexample
        detailed_steps = []

        if counterexample is not None:
            step_index = 0
            while step_index < len(counterexample.steps):
                step = counterexample.steps[step_index]

                detailed_steps.append(
                    "Step "
                    + str(step.step_index)
                    + ": "
                    + step.thread_id
                    + " performs "
                    + step.event_kind
                    + " on "
                    + str(step.original_resource)
                    + "."
                )

                step_index = step_index + 1

            exclusion_summary = self._build_conflicting_access_summary(
                counterexample,
                "mutual exclusion violation",
            )
            if exclusion_summary is not None:
                detailed_steps.append(exclusion_summary)

        return ExplanationModel(
            title="Mutual exclusion violation detected",
            summary=verification_result.selected_message or
            "A mutual exclusion violation was detected during bounded exploration.",
            detailed_steps=detailed_steps,
            source_references=[],
        )

    def _build_deadlock_cycle_description(self, final_state) -> str | None:
        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        relations = []

        pair_index = 0
        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                owner = final_state.lock_owners.get(waited_lock)
                if owner is not None and owner != thread_id:
                    relations.append(
                        thread_id
                        + " waits for a lock held by "
                        + owner
                    )

            pair_index = pair_index + 1

        if len(relations) == 0:
            return None

        return "The final state contains a circular waiting pattern: " + "; ".join(relations) + "."

    def _build_starvation_summary(self, final_state) -> str | None:
        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        waiting_threads = []
        pair_index = 0

        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]
            if waited_lock is not None:
                waiting_threads.append(thread_id)
            pair_index = pair_index + 1

        if len(waiting_threads) == 0:
            return None

        return (
            "The scenario suggests starvation because some threads remain without progress "
            "while other threads continue to hold or reacquire shared resources."
        )

    def _build_conflicting_access_summary(
        self,
        counterexample,
        property_label: str,
    ) -> str | None:
        steps = counterexample.steps

        first_index = 0
        while first_index < len(steps):
            first_step = steps[first_index]

            second_index = first_index + 1
            while second_index < len(steps):
                second_step = steps[second_index]

                same_resource = first_step.original_resource == second_step.original_resource
                different_thread = first_step.thread_id != second_step.thread_id
                at_least_one_write = (
                    first_step.event_kind == "write"
                    or second_step.event_kind == "write"
                )

                if same_resource and different_thread and at_least_one_write:
                    return (
                        "The scenario suggests a "
                        + property_label
                        + " because "
                        + first_step.thread_id
                        + " and "
                        + second_step.thread_id
                        + " access the same resource ("
                        + str(first_step.original_resource)
                        + ") without an explicit common protection visible in the selected scenario."
                    )

                second_index = second_index + 1

            first_index = first_index + 1

        return None

    def _waiting_sort_key(self, item):
        thread_id, waited_lock = item
        if waited_lock is None:
            return (thread_id, "")
        return (thread_id, waited_lock)

    def _progress_sort_key(self, item):
        thread_id, program_counter = item
        return (thread_id, program_counter)