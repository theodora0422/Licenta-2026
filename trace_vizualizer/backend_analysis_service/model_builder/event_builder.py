from trace_vizualizer.domain.concurrency import (
    CanonicalConcurrencyIR,
    CanonicalSharedAccessOperation,
    CanonicalSynchronizationOperation,
    CanonicalThread,
    CanonicalThreadStartBinding,
    SourceLocation,
)
from trace_vizualizer.domain.model import (
    AbstractEvent,
    PendingEvent,
    ThreadEventSequence,
)


class EventBuilder:

    EXECUTABLE_THREAD_KINDS = {
        "thread_instantiation",
        "thread_subclass",
        "runnable_implementation",
    }

    def build(self, canonical_ir: CanonicalConcurrencyIR) -> list[ThreadEventSequence]:
        has_real_bindings = False
        index = 0
        while index < len(canonical_ir.thread_bindings):
            binding = canonical_ir.thread_bindings[index]
            if binding.run_method_location is not None:
                has_real_bindings = True
                break
            index = index + 1

        if has_real_bindings:
            return self._build_from_thread_bindings(canonical_ir)

        return self._build_from_structural_threads(canonical_ir)

    def _build_from_thread_bindings(
        self,
        canonical_ir: CanonicalConcurrencyIR,
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
                self._append_sync_events_for_scope(
                    pending_events=pending_by_thread[thread_id],
                    synchronization_operations=canonical_ir.synchronization_operations,
                    scope_location=binding.run_method_location,
                    thread_id=thread_id,
                    thread_name=binding.thread_name,
                )

                self._append_shared_events_for_scope(
                    pending_events=pending_by_thread[thread_id],
                    shared_operations=canonical_ir.shared_access_operations,
                    scope_location=binding.run_method_location,
                    thread_id=thread_id,
                    thread_name=binding.thread_name,
                )

            binding_index = binding_index + 1

        return self._finalize_sequences(pending_by_thread, thread_name_by_id)

    def _build_from_structural_threads(
        self,
        canonical_ir: CanonicalConcurrencyIR,
    ) -> list[ThreadEventSequence]:
        executable_threads = []
        index = 0
        while index < len(canonical_ir.threads):
            thread = canonical_ir.threads[index]
            if thread.kind in self.EXECUTABLE_THREAD_KINDS:
                executable_threads.append(thread)
            index = index + 1

        synthetic_main_id = "thread_main"
        pending_by_thread = {}
        thread_name_by_id = {}

        index = 0
        while index < len(executable_threads):
            thread = executable_threads[index]
            pending_by_thread[thread.canonical_id] = []
            thread_name_by_id[thread.canonical_id] = thread.original_name
            index = index + 1

        pending_by_thread[synthetic_main_id] = []
        thread_name_by_id[synthetic_main_id] = "main"

        index = 0
        while index < len(canonical_ir.synchronization_operations):
            operation = canonical_ir.synchronization_operations[index]
            owner_thread_id = self._resolve_owner_thread_id_for_location(
                operation.source_location,
                executable_threads,
                synthetic_main_id,
            )
            pending_events = self._build_pending_events_from_sync_operation(
                operation,
                owner_thread_id,
                thread_name_by_id.get(owner_thread_id),
            )
            inner_index = 0
            while inner_index < len(pending_events):
                pending_by_thread[owner_thread_id].append(pending_events[inner_index])
                inner_index = inner_index + 1
            index = index + 1

        index = 0
        while index < len(canonical_ir.shared_access_operations):
            operation = canonical_ir.shared_access_operations[index]
            owner_thread_id = self._resolve_owner_thread_id_for_location(
                operation.source_location,
                executable_threads,
                synthetic_main_id,
            )
            pending_event = self._build_pending_event_from_shared_access(
                operation,
                owner_thread_id,
                thread_name_by_id.get(owner_thread_id),
            )
            pending_by_thread[owner_thread_id].append(pending_event)
            index = index + 1

        return self._finalize_sequences(pending_by_thread, thread_name_by_id)

    def _append_sync_events_for_scope(
        self,
        pending_events: list,
        synchronization_operations: list[CanonicalSynchronizationOperation],
        scope_location: SourceLocation,
        thread_id: str,
        thread_name: str | None,
    ) -> None:
        ordered_operations = self._sort_sync_operations(synchronization_operations)

        index = 0
        while index < len(ordered_operations):
            operation = ordered_operations[index]
            if self._contains(scope_location, operation.source_location):
                generated = self._build_pending_events_from_sync_operation(
                    operation,
                    thread_id,
                    thread_name,
                )
                inner_index = 0
                while inner_index < len(generated):
                    pending_events.append(generated[inner_index])
                    inner_index = inner_index + 1
            index = index + 1

    def _append_shared_events_for_scope(
        self,
        pending_events: list,
        shared_operations: list[CanonicalSharedAccessOperation],
        scope_location: SourceLocation,
        thread_id: str,
        thread_name: str | None,
    ) -> None:
        ordered_operations = self._sort_shared_operations(shared_operations)

        index = 0
        while index < len(ordered_operations):
            operation = ordered_operations[index]
            if self._contains(scope_location, operation.source_location):
                pending_event = self._build_pending_event_from_shared_access(
                    operation,
                    thread_id,
                    thread_name,
                )
                pending_events.append(pending_event)
            index = index + 1

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

    def _build_pending_events_from_sync_operation(
        self,
        operation: CanonicalSynchronizationOperation,
        thread_id: str,
        thread_name: str | None,
    ) -> list[PendingEvent]:
        results = []

        if operation.kind == "lock_acquire":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="acquire",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                    expression=operation.expression,
                    order_line=operation.source_location.start_line,
                    order_column=operation.source_location.start_column,
                    phase_priority=0,
                )
            )
            return results

        if operation.kind == "lock_release":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="release",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                    expression=operation.expression,
                    order_line=operation.source_location.start_line,
                    order_column=operation.source_location.start_column,
                    phase_priority=2,
                )
            )
            return results

        if operation.kind == "synchronized_block":
            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="acquire",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                    expression=operation.expression,
                    order_line=operation.source_location.start_line,
                    order_column=operation.source_location.start_column,
                    phase_priority=0,
                )
            )

            results.append(
                PendingEvent(
                    thread_id=thread_id,
                    thread_name=thread_name,
                    kind="release",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                    expression=operation.expression,
                    order_line=operation.source_location.end_line,
                    order_column=operation.source_location.end_column,
                    phase_priority=2,
                )
            )

        return results

    def _build_pending_event_from_shared_access(
        self,
        operation: CanonicalSharedAccessOperation,
        thread_id: str,
        thread_name: str | None,
    ) -> PendingEvent:
        event_kind = "write"
        if operation.kind == "read":
            event_kind = "read"

        return PendingEvent(
            thread_id=thread_id,
            thread_name=thread_name,
            kind=event_kind,
            resource_id=operation.canonical_resource_id,
            original_resource=operation.original_resource,
            source_location=operation.source_location,
            expression=operation.expression,
            order_line=operation.source_location.start_line,
            order_column=operation.source_location.start_column,
            phase_priority=1,
        )

    def _resolve_owner_thread_id_for_location(
        self,
        operation_location: SourceLocation,
        executable_threads: list[CanonicalThread],
        fallback_thread_id: str,
    ) -> str:
        containing_threads = []

        index = 0
        while index < len(executable_threads):
            thread = executable_threads[index]
            if self._contains(thread.source_location, operation_location):
                containing_threads.append(thread)
            index = index + 1

        if len(containing_threads) == 0:
            return fallback_thread_id

        containing_threads.sort(key=self._thread_span_size)
        return containing_threads[0].canonical_id

    def _thread_span_size(self, thread: CanonicalThread) -> int:
        return self._span_size(thread.source_location)

    def _contains(
        self,
        outer: SourceLocation,
        inner: SourceLocation,
    ) -> bool:
        starts_after = False
        ends_before = False

        if inner.start_line > outer.start_line:
            starts_after = True
        elif inner.start_line == outer.start_line:
            if inner.start_column >= outer.start_column:
                starts_after = True

        if inner.end_line < outer.end_line:
            ends_before = True
        elif inner.end_line == outer.end_line:
            if inner.end_column <= outer.end_column:
                ends_before = True

        if starts_after and ends_before:
            return True

        return False

    def _span_size(self, location: SourceLocation) -> int:
        line_span = location.end_line - location.start_line
        column_span = location.end_column - location.start_column
        return line_span * 10000 + column_span

    def _sort_sync_operations(
        self,
        operations: list[CanonicalSynchronizationOperation],
    ) -> list[CanonicalSynchronizationOperation]:
        ordered = list(operations)
        ordered.sort(
            key=self._sync_sort_key,
        )
        return ordered

    def _sync_sort_key(self, operation: CanonicalSynchronizationOperation):
        return (
            operation.source_location.start_line,
            operation.source_location.start_column,
            operation.source_location.end_line,
            operation.source_location.end_column,
        )

    def _sort_shared_operations(
        self,
        operations: list[CanonicalSharedAccessOperation],
    ) -> list[CanonicalSharedAccessOperation]:
        ordered = list(operations)
        ordered.sort(
            key=self._shared_sort_key,
        )
        return ordered

    def _shared_sort_key(self, operation: CanonicalSharedAccessOperation):
        return (
            operation.source_location.start_line,
            operation.source_location.start_column,
        )

    def _sort_pending_events(
        self,
        pending_events: list[PendingEvent],
    ) -> list[PendingEvent]:
        ordered = list(pending_events)
        ordered.sort(
            key=self._pending_sort_key,
        )
        return ordered

    def _pending_sort_key(self, event: PendingEvent):
        return (
            event.order_line,
            event.order_column,
            event.phase_priority,
        )