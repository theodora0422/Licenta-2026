from trace_vizualizer.domain.concurrency import (
    CanonicalConcurrencyIR,
    CanonicalSharedAccessOperation,
    CanonicalSynchronizationOperation,
    CanonicalThread,
    ConcurrencyIR,
)


class IdentifierResolver:

    def resolve(self, concurrency_ir: ConcurrencyIR) -> CanonicalConcurrencyIR:
        thread_mapping = self._build_thread_mapping(concurrency_ir)
        sync_resource_mapping = self._build_sync_resource_mapping(concurrency_ir)
        shared_resource_mapping = self._build_shared_resource_mapping(concurrency_ir)

        canonical_threads = [
            CanonicalThread(
                canonical_id=thread_mapping[thread.identifier],
                original_identifier=thread.identifier,
                original_name=thread.name,
                kind=thread.kind,
                source_location=thread.source_location,
            )
            for thread in concurrency_ir.threads
        ]

        canonical_sync_operations = [
            CanonicalSynchronizationOperation(
                kind=operation.kind,
                canonical_resource_id=sync_resource_mapping[operation.resource],
                original_resource=operation.resource,
                source_location=operation.source_location,
                expression=operation.expression,
            )
            for operation in concurrency_ir.synchronization_operations
        ]

        canonical_shared_operations = [
            CanonicalSharedAccessOperation(
                kind=operation.kind,
                canonical_resource_id=shared_resource_mapping[operation.resource],
                original_resource=operation.resource,
                expression=operation.expression,
                source_location=operation.source_location,
            )
            for operation in concurrency_ir.shared_access_operations
        ]

        return CanonicalConcurrencyIR(
            threads=canonical_threads,
            synchronization_operations=canonical_sync_operations,
            shared_access_operations=canonical_shared_operations,
            thread_mapping=thread_mapping,
            synchronization_resource_mapping=sync_resource_mapping,
            shared_resource_mapping=shared_resource_mapping,
        )

    def _build_thread_mapping(self, concurrency_ir: ConcurrencyIR) -> dict[str, str]:
        mapping: dict[str, str] = {}

        for index, thread in enumerate(concurrency_ir.threads, start=1):
            mapping[thread.identifier] = f"thread_{index}"

        return mapping

    def _build_sync_resource_mapping(self, concurrency_ir: ConcurrencyIR) -> dict[str, str]:
        mapping: dict[str, str] = {}
        seen_resources: list[str] = []

        for operation in concurrency_ir.synchronization_operations:
            resource = operation.resource
            if resource not in seen_resources:
                seen_resources.append(resource)

        for index, resource in enumerate(seen_resources, start=1):
            mapping[resource] = f"lock_{index}"

        return mapping

    def _build_shared_resource_mapping(self, concurrency_ir: ConcurrencyIR) -> dict[str, str]:
        mapping: dict[str, str] = {}
        seen_resources: list[str] = []

        for operation in concurrency_ir.shared_access_operations:
            resource = operation.resource
            if resource not in seen_resources:
                seen_resources.append(resource)

        for index, resource in enumerate(seen_resources, start=1):
            mapping[resource] = f"resource_{index}"

        return mapping