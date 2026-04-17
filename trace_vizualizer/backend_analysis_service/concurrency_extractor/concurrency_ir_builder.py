from trace_vizualizer.domain.concurrency import ThreadInfo, SynchronizationOperation, SharedAccessOperation, \
    ConcurrencyIR, ThreadClassInfo, ThreadInstanceInfo, ThreadStartBinding, LoopRegionInfo


class ConcurrencyIRBuilder:
    # asambleaz rezultatele extractorilor într-o reprezentare

    def build(
        self,
        threads: list[ThreadInfo],
        thread_classes:list[ThreadClassInfo],
        thread_instances:list[ThreadInstanceInfo],
        thread_start_bindings:list[ThreadStartBinding],
        loop_regions:list[LoopRegionInfo],
        synchronization_operations: list[SynchronizationOperation],
        shared_access_operations: list[SharedAccessOperation],
    ) -> ConcurrencyIR:
        return ConcurrencyIR(
            threads=threads,
            thread_classes=thread_classes,
            thread_instances=thread_instances,
            thread_start_bindings=thread_start_bindings,
            loop_regions=loop_regions,
            synchronization_operations=synchronization_operations,
            shared_access_operations=shared_access_operations,
        )