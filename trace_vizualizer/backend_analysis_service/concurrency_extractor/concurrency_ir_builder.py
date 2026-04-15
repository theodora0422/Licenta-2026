from trace_vizualizer.domain.concurrency import ThreadInfo, SynchronizationOperation, SharedAccessOperation, \
    ConcurrencyIR, ThreadClassInfo, ThreadInstanceInfo, ThreadStartBinding


class ConcurrencyIRBuilder:
    """
    Asamblează rezultatele extractorilor într-o reprezentare intermediară unificată.
    """

    def build(
        self,
        threads: list[ThreadInfo],
        thread_classes:list[ThreadClassInfo],
        thread_instances:list[ThreadInstanceInfo],
        thread_start_bindings:list[ThreadStartBinding],
        synchronization_operations: list[SynchronizationOperation],
        shared_access_operations: list[SharedAccessOperation],
    ) -> ConcurrencyIR:
        return ConcurrencyIR(
            threads=threads,
            thread_classes=thread_classes,
            thread_instances=thread_instances,
            thread_start_bindings=thread_start_bindings,
            synchronization_operations=synchronization_operations,
            shared_access_operations=shared_access_operations,
        )