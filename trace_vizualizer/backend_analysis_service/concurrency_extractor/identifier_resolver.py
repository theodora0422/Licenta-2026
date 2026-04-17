from trace_vizualizer.domain.concurrency import (
    CanonicalConcurrencyIR,
    CanonicalSharedAccessOperation,
    CanonicalSynchronizationOperation,
    CanonicalThread,
    CanonicalThreadInstance,
    CanonicalThreadStartBinding,
    ConcurrencyIR,
)


class IdentifierResolver:
    def resolve(self, concurrency_ir: ConcurrencyIR) -> CanonicalConcurrencyIR:
        thread_mapping = self._build_thread_mapping(concurrency_ir)
        thread_instance_mapping = self._build_thread_instance_mapping(concurrency_ir)
        sync_resource_mapping = self._build_sync_resource_mapping(concurrency_ir)
        shared_resource_mapping = self._build_shared_resource_mapping(concurrency_ir)

        canonical_threads = []
        index = 0
        while index < len(concurrency_ir.threads):
            thread = concurrency_ir.threads[index]
            canonical_threads.append(
                CanonicalThread(
                    canonical_id=thread_mapping[thread.identifier],
                    original_identifier=thread.identifier,
                    original_name=thread.name,
                    kind=thread.kind,
                    source_location=thread.source_location,
                )
            )
            index = index + 1

        canonical_instances = []
        index = 0
        while index < len(concurrency_ir.thread_instances):
            instance = concurrency_ir.thread_instances[index]
            canonical_instances.append(
                CanonicalThreadInstance(
                    canonical_thread_id=thread_instance_mapping[instance.instance_id],
                    original_instance_id=instance.instance_id,
                    class_name=instance.class_name,
                    declared_name=instance.declared_name,
                    creation_location=instance.creation_location,
                )
            )
            index = index + 1

        canonical_bindings = []
        index = 0
        while index < len(concurrency_ir.thread_start_bindings):
            binding = concurrency_ir.thread_start_bindings[index]
            if binding.instance_id in thread_instance_mapping:
                canonical_bindings.append(
                    CanonicalThreadStartBinding(
                        binding_id=binding.binding_id,
                        canonical_thread_id=thread_instance_mapping[binding.instance_id],
                        class_name=binding.class_name,
                        thread_name=binding.declared_name,
                        start_location=binding.start_location,
                        run_method_location=binding.run_method_location,
                    )
                )
            index = index + 1

        canonical_sync_operations = []
        index = 0
        while index < len(concurrency_ir.synchronization_operations):
            operation = concurrency_ir.synchronization_operations[index]
            canonical_sync_operations.append(
                CanonicalSynchronizationOperation(
                    kind=operation.kind,
                    canonical_resource_id=sync_resource_mapping[operation.resource],
                    original_resource=operation.resource,
                    source_location=operation.source_location,
                    expression=operation.expression,
                    iteration_index=1,
                    synthetic_order_offset=0,
                )
            )
            index = index + 1

        canonical_shared_operations = []
        index = 0
        while index < len(concurrency_ir.shared_access_operations):
            operation = concurrency_ir.shared_access_operations[index]
            canonical_shared_operations.append(
                CanonicalSharedAccessOperation(
                    kind=operation.kind,
                    canonical_resource_id=shared_resource_mapping[operation.resource],
                    original_resource=operation.resource,
                    expression=operation.expression,
                    source_location=operation.source_location,
                    iteration_index=1,
                    synthetic_order_offset=0,
                )
            )
            index = index + 1

        return CanonicalConcurrencyIR(
            threads=canonical_threads,
            thread_instances=canonical_instances,
            thread_bindings=canonical_bindings,
            synchronization_operations=canonical_sync_operations,
            shared_access_operations=canonical_shared_operations,
            thread_mapping=thread_mapping,
            thread_instance_mapping=thread_instance_mapping,
            synchronization_resource_mapping=sync_resource_mapping,
            shared_resource_mapping=shared_resource_mapping,
        )

    def _build_thread_mapping(self, concurrency_ir: ConcurrencyIR) -> dict:
        mapping = {}
        index = 0
        next_number = 1

        while index < len(concurrency_ir.threads):
            thread = concurrency_ir.threads[index]
            mapping[thread.identifier] = "thread_entity_" + str(next_number)
            next_number = next_number + 1
            index = index + 1

        return mapping

    def _build_thread_instance_mapping(self, concurrency_ir: ConcurrencyIR) -> dict:
        mapping = {}
        index = 0
        next_number = 1

        while index < len(concurrency_ir.thread_instances):
            instance = concurrency_ir.thread_instances[index]
            mapping[instance.instance_id] = "thread_" + str(next_number)
            next_number = next_number + 1
            index = index + 1

        return mapping

    def _build_sync_resource_mapping(self, concurrency_ir: ConcurrencyIR) -> dict:
        mapping = {}
        seen_resources = []
        index = 0

        while index < len(concurrency_ir.synchronization_operations):
            operation = concurrency_ir.synchronization_operations[index]
            if operation.resource not in seen_resources:
                seen_resources.append(operation.resource)
            index = index + 1

        index = 0
        next_number = 1
        while index < len(seen_resources):
            resource = seen_resources[index]
            mapping[resource] = "lock_" + str(next_number)
            next_number = next_number + 1
            index = index + 1

        return mapping

    def _build_shared_resource_mapping(self, concurrency_ir: ConcurrencyIR) -> dict:
        mapping = {}
        seen_resources = []
        index = 0

        while index < len(concurrency_ir.shared_access_operations):
            operation = concurrency_ir.shared_access_operations[index]
            if operation.resource not in seen_resources:
                seen_resources.append(operation.resource)
            index = index + 1

        index = 0
        next_number = 1
        while index < len(seen_resources):
            resource = seen_resources[index]
            mapping[resource] = "resource_" + str(next_number)
            next_number = next_number + 1
            index = index + 1

        return mapping