from typing import List, Optional

from trace_vizualizer.domain.concurrency import (
    CanonicalConcurrencyIR,
    CanonicalSharedAccessOperation,
    CanonicalSynchronizationOperation,
    CanonicalThread,
    SourceLocation,
)
from trace_vizualizer.domain.model import AbstractEvent, ThreadEventSequence


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

        thread_sequences: dict[str, ThreadEventSequence] = {
            thread.canonical_id: ThreadEventSequence(
                thread_id=thread.canonical_id,
                thread_name=thread.original_name,
                events=[],
            )
            for thread in executable_threads
        }

        synthetic_main_id = "thread_main"
        thread_sequences[synthetic_main_id] = ThreadEventSequence(
            thread_id=synthetic_main_id,
            thread_name="main",
            events=[],
        )

        event_counter = 1

        sync_operations = sorted(
            canonical_ir.synchronization_operations,
            key=lambda op: (
                op.source_location.start_line,
                op.source_location.start_column,
            ),
        )

        for operation in sync_operations:
            owner_thread_id = self._resolve_owner_thread_id(
                operation.source_location,
                executable_threads,
                fallback_thread_id=synthetic_main_id,
            )

            generated_events = self._build_events_from_sync_operation(
                operation=operation,
                thread_id=owner_thread_id,
                start_index=event_counter,
            )

            for event in generated_events:
                thread_sequences[owner_thread_id].events.append(event)

            event_counter += len(generated_events)

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

            event = self._build_event_from_shared_access(
                operation=operation,
                thread_id=owner_thread_id,
                event_index=event_counter,
            )

            thread_sequences[owner_thread_id].events.append(event)
            event_counter += 1

        result = [
            sequence
            for sequence in thread_sequences.values()
            if sequence.events
        ]

        if not result:
            result = [thread_sequences[synthetic_main_id]]

        return result

    def _build_events_from_sync_operation(
        self,
        operation: CanonicalSynchronizationOperation,
        thread_id: str,
        start_index: int,
    ) -> List[AbstractEvent]:
        if operation.kind == "lock_acquire":
            return [
                AbstractEvent(
                    event_id=f"event_{start_index}",
                    thread_id=thread_id,
                    kind="acquire",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                )
            ]

        if operation.kind == "lock_release":
            return [
                AbstractEvent(
                    event_id=f"event_{start_index}",
                    thread_id=thread_id,
                    kind="release",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                )
            ]

        if operation.kind == "synchronized_block":
            return [
                AbstractEvent(
                    event_id=f"event_{start_index}",
                    thread_id=thread_id,
                    kind="acquire",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                ),
                AbstractEvent(
                    event_id=f"event_{start_index + 1}",
                    thread_id=thread_id,
                    kind="release",
                    resource_id=operation.canonical_resource_id,
                    original_resource=operation.original_resource,
                    source_location=operation.source_location,
                ),
            ]

        return []

    def _build_event_from_shared_access(
        self,
        operation: CanonicalSharedAccessOperation,
        thread_id: str,
        event_index: int,
    ) -> AbstractEvent:
        event_kind = "read" if operation.kind == "read" else "write"

        return AbstractEvent(
            event_id=f"event_{event_index}",
            thread_id=thread_id,
            kind=event_kind,
            resource_id=operation.canonical_resource_id,
            original_resource=operation.original_resource,
            source_location=operation.source_location,
            expression=operation.expression,
        )

    def _resolve_owner_thread_id(
        self,
        operation_location: SourceLocation,
        executable_threads: List[CanonicalThread],
        fallback_thread_id: str,
    ) -> str:
        containing_threads = [
            thread for thread in executable_threads
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