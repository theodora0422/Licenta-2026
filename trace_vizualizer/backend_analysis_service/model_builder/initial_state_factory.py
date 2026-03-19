from trace_vizualizer.domain.model import InitialState, ThreadEventSequence


class InitialStateFactory:
    def build(self, thread_event_sequences: list[ThreadEventSequence]) -> InitialState:
        thread_ids = [sequence.thread_id for sequence in thread_event_sequences]

        lock_ids = sorted({
            event.resource_id
            for sequence in thread_event_sequences
            for event in sequence.events
            if event.kind in {"acquire", "release"}
        })

        return InitialState(
            program_counters={thread_id: 0 for thread_id in thread_ids},
            lock_owners={lock_id: None for lock_id in lock_ids},
            held_locks={thread_id: [] for thread_id in thread_ids},
            waiting_for={thread_id: None for thread_id in thread_ids},
        )