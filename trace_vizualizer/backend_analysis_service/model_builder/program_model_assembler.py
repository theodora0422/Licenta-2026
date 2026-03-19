from trace_vizualizer.domain.model import InitialState, ProgramModel, ThreadEventSequence


class ProgramModelAssembler:

    def build(
        self,
        thread_event_sequences: list[ThreadEventSequence],
        initial_state: InitialState,
    ) -> ProgramModel:
        all_events = [
            event
            for sequence in thread_event_sequences
            for event in sequence.events
        ]

        lock_ids = sorted({
            event.resource_id
            for event in all_events
            if event.kind in {"acquire", "release"}
        })

        shared_resource_ids = sorted({
            event.resource_id
            for event in all_events
            if event.kind in {"read", "write"}
        })

        return ProgramModel(
            thread_event_sequences=thread_event_sequences,
            initial_state=initial_state,
            thread_count=len(thread_event_sequences),
            event_count=len(all_events),
            lock_ids=lock_ids,
            shared_resource_ids=shared_resource_ids,
        )