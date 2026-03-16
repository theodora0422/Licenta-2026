from trace_vizualizer.domain.concurrency import ThreadInfo, SynchronizationOperation, SharedAccessOperation, \
    ConcurrencyIR


class ConcurrencyIRBuilder:
    """
    Asamblează rezultatele extractorilor într-o reprezentare intermediară unificată.
    """

    def build(
        self,
        threads: list[ThreadInfo],
        synchronization_operations: list[SynchronizationOperation],
        shared_access_operations: list[SharedAccessOperation],
    ) -> ConcurrencyIR:
        return ConcurrencyIR(
            threads=threads,
            synchronization_operations=synchronization_operations,
            shared_access_operations=shared_access_operations,
        )