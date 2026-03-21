
from typing import List

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

    EXECUTABLE_THREAD_KINDS = {
        "thread_instantiation",
        "thread_subclass",
        "runnable_implementation",
    }

    def build(self, canonical_ir: CanonicalConcurrencyIR) -> List[ThreadEventSequence]:
        executable_threads = [
            thread for thread in canonical_ir.threads
            if thread.kind in self.EXECUTABLE_THREAD_KINDS
        ]

        synthetic_main_id = "thread_main"
        synthetic_main_name = "main"

        pending_events_by_thread: dict[str, list[PendingEvent]] = {
            thread.canonical_id: []
            for thread in executable_threads
        }
        pending_events_by_thread[synthetic_main_id] = []

        thread_names: dict[str, str | None] = {
            thread.canonical_id: thread.original_name
            for thread in executable_threads
        }
        thread_names[synthetic_main_id] = synthetic_main_name

        sync_operations = sorted(
            canonical_ir.synchronization_operations,
            key=lambda op: (
                op.source_location.start_line,
                op.source_location.start_column,
                op.source_location.end_line,
                op.source_location.end_column,
            ),
        )

        for operation in sync_operations:
            owner_thread_id = self._resolve_owner_thread_id(
                operation.source_location,
                executable_threads,
                fallback_thread_id=synthetic_main_id,
            )

            pending_events = self._build_pending_events_from_sync_operation(
                operation=operation,
                thread_id=owner_thread_id,
                thread_name=thread_names.get(owner_thread_id),
            )

            pending_events_by_thread.setdefault(owner_thread_id, []).extend(pending_events)

        shared_operations = sorted(
            canonical_ir.shared_access_operations,
            key=lambda op: (
                op.source_location.start_line,
                op.source_location.start_column,
            ),
        )

        for operation in shared_operations:
            owner_thread_id = self._resolve_owner_thread_id(
                operation.source_location,
                executable_threads,
                fallback_thread_id=synthetic_main_id,
            )

            pending_event = self._build_pending_event_from_shared_access(
                operation=operation,
                thread_id=owner_thread_id,
                thread_name=thread_names.get(owner_thread_id),
            )

            pending_events_by_thread.setdefault(owner_thread_id, []).append(pending_event)

        thread_sequences: list[ThreadEventSequence] = []
        event_counter = 1

        for thread_id, pending_events in pending_events_by_thread.items():
            if not pending_events:
                continue

            sorted_pending_events = sorted(
                pending_events,
                key=lambda event: (
                    event.order_line,
                    event.order_column,
                    event.phase_priority,
                ),
            )

            concrete_events: list[AbstractEvent] = []
            for pending in sorted_pending_events:
                concrete_events.append(
                    AbstractEvent(
                        event_id=f"event_{event_counter}",
                        thread_id=pending.thread_id,
                        kind=pending.kind,
                        resource_id=pending.resource_id,
                        original_resource=pending.original_resource,
                        source_location=pending.source_location,
                        expression=pending.expression,
                    )
                )
                event_counter += 1

            thread_sequences.append(
                ThreadEventSequence(
                    thread_id=thread_id,
                    thread_name=thread_names.get(thread_id),
                    events=concrete_events,
                )
            )

        if not thread_sequences:
            thread_sequences.append(
                ThreadEventSequence(
                    thread_id=synthetic_main_id,
                    thread_name=synthetic_main_name,
                    events=[],
                )
            )

        return thread_sequences

    def _build_pending_events_from_sync_operation(
        self,
        operation: CanonicalSynchronizationOperation,
        thread_id: str,
        thread_name: str | None,
    ) -> List[PendingEvent]:
        if operation.kind == "lock_acquire":
            return [
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
            ]

        if operation.kind == "lock_release":
            return [
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
            ]

        if operation.kind == "synchronized_block":
            acquire_event = PendingEvent(
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

            release_event = PendingEvent(
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

            return [acquire_event, release_event]

        return []

    def _build_pending_event_from_shared_access(
        self,
        operation: CanonicalSharedAccessOperation,
        thread_id: str,
        thread_name: str | None,
    ) -> PendingEvent:
        event_kind = "read" if operation.kind == "read" else "write"

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

    def _resolve_owner_thread_id(
        self,
        operation_location: SourceLocation,
        executable_threads: List[CanonicalThread],
        fallback_thread_id: str,
    ) -> str:
        containing_threads = [
            thread
            for thread in executable_threads
            if self._contains(thread.source_location, operation_location)
        ]

        if not containing_threads:
            return fallback_thread_id

        containing_threads.sort(
            key=lambda thread: self._span_size(thread.source_location)
        )
        return containing_threads[0].canonical_id

    def _contains(
        self,
        outer: SourceLocation,
        inner: SourceLocation,
    ) -> bool:
        starts_after_or_equal = (
            (inner.start_line > outer.start_line)
            or (
                inner.start_line == outer.start_line
                and inner.start_column >= outer.start_column
            )
        )

        ends_before_or_equal = (
            (inner.end_line < outer.end_line)
            or (
                inner.end_line == outer.end_line
                and inner.end_column <= outer.end_column
            )
        )

        return starts_after_or_equal and ends_before_or_equal

    def _span_size(self, location: SourceLocation) -> int:
        line_span = location.end_line - location.start_line
        column_span = location.end_column - location.start_column
        return line_span * 10_000 + column_span