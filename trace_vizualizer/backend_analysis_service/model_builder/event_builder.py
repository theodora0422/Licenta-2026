from trace_vizualizer.backend_analysis_service.model_builder.loop_expander import LoopExpander
from trace_vizualizer.domain.concurrency import (
    CanonicalConcurrencyIR,
    CanonicalSharedAccessOperation,
    CanonicalSynchronizationOperation,
    CanonicalThread,
    SourceLocation,
)
from trace_vizualizer.domain.model import (
    AbstractEvent,
    PendingEvent,
    ThreadEventSequence,
)


class EventBuilder:
    def __init__(self):
        self.loop_expander = LoopExpander()

    def build(
        self,
        canonical_ir: CanonicalConcurrencyIR,
        source_loop_regions: list,
        loop_unroll_factor: int,
    ) -> list[ThreadEventSequence]:
        has_real_bindings = False
        index = 0
        while index < len(canonical_ir.thread_bindings):
            binding = canonical_ir.thread_bindings[index]
            if binding.run_method_location is not None:
                has_real_bindings = True
                break
            index = index + 1

        if has_real_bindings:
            return self._build_from_thread_bindings(
                canonical_ir,
                source_loop_regions,
                loop_unroll_factor,
            )

        return self._build_from_structural_threads(canonical_ir)

    def _build_from_thread_bindings(
        self,
        canonical_ir: CanonicalConcurrencyIR,
        source_loop_regions: list,
        loop_unroll_factor: int,
    ) -> list[ThreadEventSequence]:
        pending_by_thread = {}
        thread_name_by_id = {}

        binding_index = 0
        while binding_index < len(canonical_ir.thread_bindings):
            binding = canonical_ir.thread_bindings[binding_index]
            thread_id = binding.canonical_thread_id

            if thread_id not in pending_by_thread:
                pending_by_thread[thread_id] = []

            if thread_id not in thread_name_by_id:
                thread_name_by_id[thread_id] = binding.thread_name

            if binding.run_method_location is not None:
                expanded_sync_operations = self.loop_expander.expand_synchronization_operations(
                    canonical_ir.synchronization_operations,
                    source_loop_regions,
                    binding.run_method_location,
                    loop_unroll_factor,
                )

                expanded_shared_operations = self.loop_expander.expand_shared_access_operations(
                    canonical_ir.shared_access_operations,
                    source_loop_regions,
                    binding.run_method_location,
                    loop_unroll_factor,
                )

                self._append_expanded_sync_events(
                    pending_by_thread[thread_id],
                    expanded_sync_operations,
                    thread_id,
                    binding.thread_name,
                    canonical_ir,
                )

                self._append_expanded_shared_events(
                    pending_by_thread[thread_id],
                    expanded_shared_operations,
                    thread_id,
                    binding.thread_name,
                    canonical_ir,
                )

            binding_index = binding_index + 1

        return self._finalize_sequences(pending_by_thread, thread_name_by_id)

    def _append_expanded_sync_events(
        self,
        pending_events: list,
        expanded_operations: list,
        thread_id: str,
        thread_name: str | None,
        canonical_ir: CanonicalConcurrencyIR,
    ) -> None:
        index = 0
        while index < len(expanded_operations):
            expanded = expanded_operations[index]

            canonical_resource_id = self._find_canonical_lock_id(
                canonical_ir,
                expanded.resource,
            )

            generated = self._build_pending_events_from_expanded_sync_operation(
                expanded,
                canonical_resource_id,
                thread_id,
                thread_name,
            )

            inner_index = 0
            while inner_index < len(generated):
                pending_events.append(generated[inner_index])
                inner_index = inner_index + 1

            index = index + 1

    def _append_expanded_shared_events(
        self,
        pending_events: list,
        expanded_operations: list,
        thread_id: str,
        thread_name: str | None,
        canonical_ir: CanonicalConcurrencyIR,
    ) -> None:
        index = 0
        while index < len(expanded_operations):
            expanded = expanded_operations[index]

            canonical_resource_id = self._find_canonical_shared_id(
                canonical_ir,
                expanded.resource,
            )

            pending_event = self._build_pending_event_from_expanded_shared_access(
                expanded,
                canonical_resource_id,
                thread_id,
                thread_name,
            )
            pending_events.append(pending_event)

            index = index + 1

    def _build_pending_events_from_expanded_sync_operation(
        self,
        expanded_operation,
        canonical_resource_id: str,
        thread_id: str,
        thread_name: str | None,
    ) -> list[PendingEvent]:
        results = []

        if expanded_operation.kind == "lock_acquire":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="acquire",
                    resource_id=canonical_resource_id,
                    original_resource=expanded_operation.resource,
                    source_location=expanded_operation.source_location,
                    expression=expanded_operation.expression,
                    order_line=expanded_operation.source_location.start_line,
                    order_column=expanded_operation.source_location.start_column + expanded_operation.synthetic_order_offset,
                    phase_priority=0,
                )
            )
            return results

        if expanded_operation.kind == "lock_release":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="release",
                    resource_id=canonical_resource_id,
                    original_resource=expanded_operation.resource,
                    source_location=expanded_operation.source_location,
                    expression=expanded_operation.expression,
                    order_line=expanded_operation.source_location.start_line,
                    order_column=expanded_operation.source_location.start_column + expanded_operation.synthetic_order_offset,
                    phase_priority=2,
                )
            )
            return results

        if expanded_operation.kind == "synchronized_block":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="acquire",
                    resource_id=canonical_resource_id,
                    original_resource=expanded_operation.resource,
                    source_location=expanded_operation.source_location,
                    expression=expanded_operation.expression,
                    order_line=expanded_operation.source_location.start_line,
                    order_column=expanded_operation.source_location.start_column + expanded_operation.synthetic_order_offset,
                    phase_priority=0,
                )
            )

            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="release",
                    resource_id=canonical_resource_id,
                    original_resource=expanded_operation.resource,
                    source_location=expanded_operation.source_location,
                    expression=expanded_operation.expression,
                    order_line=expanded_operation.source_location.end_line,
                    order_column=expanded_operation.source_location.end_column + expanded_operation.synthetic_order_offset,
                    phase_priority=2,
                )
            )

        return results

    def _build_pending_event_from_expanded_shared_access(
        self,
        expanded_operation,
        canonical_resource_id: str,
        thread_id: str,
        thread_name: str | None,
    ) -> PendingEvent:
        event_kind = "write"
        if expanded_operation.kind == "read":
            event_kind = "read"

        return PendingEvent(
            thread_id=thread_id,
            thread_name=thread_name,
            kind=event_kind,
            resource_id=canonical_resource_id,
            original_resource=expanded_operation.resource,
            source_location=expanded_operation.source_location,
            expression=expanded_operation.expression,
            order_line=expanded_operation.source_location.start_line,
            order_column=expanded_operation.source_location.start_column + expanded_operation.synthetic_order_offset,
            phase_priority=1,
        )

    def _find_canonical_lock_id(
        self,
        canonical_ir: CanonicalConcurrencyIR,
        original_resource: str,
    ) -> str:
        index = 0
        while index < len(canonical_ir.synchronization_operations):
            operation = canonical_ir.synchronization_operations[index]
            if operation.original_resource == original_resource:
                return operation.canonical_resource_id
            index = index + 1

        return original_resource

    def _find_canonical_shared_id(
        self,
        canonical_ir: CanonicalConcurrencyIR,
        original_resource: str,
    ) -> str:
        index = 0
        while index < len(canonical_ir.shared_access_operations):
            operation = canonical_ir.shared_access_operations[index]
            if operation.original_resource == original_resource:
                return operation.canonical_resource_id
            index = index + 1

        return original_resource

    def _build_from_structural_threads(
        self,
        canonical_ir: CanonicalConcurrencyIR,
    ) -> list[ThreadEventSequence]:
        pending_by_thread = {}
        thread_name_by_id = {}

        pending_by_thread["thread_main"] = []
        thread_name_by_id["thread_main"] = "main"

        return self._finalize_sequences(pending_by_thread, thread_name_by_id)

    def _finalize_sequences(
        self,
        pending_by_thread: dict,
        thread_name_by_id: dict,
    ) -> list[ThreadEventSequence]:
        thread_sequences = []
        event_counter = 1

        thread_ids = list(pending_by_thread.keys())
        thread_ids.sort()

        index = 0
        while index < len(thread_ids):
            thread_id = thread_ids[index]
            pending_events = pending_by_thread[thread_id]

            if len(pending_events) > 0:
                sorted_pending = self._sort_pending_events(pending_events)

                concrete_events = []
                inner_index = 0
                while inner_index < len(sorted_pending):
                    pending = sorted_pending[inner_index]
                    concrete_events.append(
                        AbstractEvent(
                            event_id="event_" + str(event_counter),
                            thread_id=pending.thread_id,
                            kind=pending.kind,
                            resource_id=pending.resource_id,
                            original_resource=pending.original_resource,
                            source_location=pending.source_location,
                            expression=pending.expression,
                        )
                    )
                    event_counter = event_counter + 1
                    inner_index = inner_index + 1

                thread_sequences.append(
                    ThreadEventSequence(
                        thread_id=thread_id,
                        thread_name=thread_name_by_id.get(thread_id),
                        events=concrete_events,
                    )
                )

            index = index + 1

        if len(thread_sequences) == 0:
            thread_sequences.append(
                ThreadEventSequence(
                    thread_id="thread_main",
                    thread_name="main",
                    events=[],
                )
            )

        return thread_sequences

    def _sort_pending_events(
        self,
        pending_events: list[PendingEvent],
    ) -> list[PendingEvent]:
        ordered = list(pending_events)
        ordered.sort(key=self._pending_sort_key)
        return ordered

    def _pending_sort_key(self, event: PendingEvent):
        return (
            event.order_line,
            event.order_column,
            event.phase_priority,
        )