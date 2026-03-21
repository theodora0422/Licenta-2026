from typing import List, Optional

from trace_vizualizer.domain.model import AbstractEvent, ProgramModel
from trace_vizualizer.domain.scenario import ExplorationState


class TransitionSystem:

    def get_enabled_transitions(
        self,
        state: ExplorationState,
        program_model: ProgramModel,
    ) -> List[tuple[str, AbstractEvent]]:
        enabled: List[tuple[str, AbstractEvent]] = []

        for sequence in program_model.thread_event_sequences:
            thread_id = sequence.thread_id
            pc = state.program_counters.get(thread_id, 0)

            if pc >= len(sequence.events):
                continue

            event = sequence.events[pc]

            if self._is_enabled(event, thread_id, state):
                enabled.append((thread_id, event))
            else:
                if event.kind == "acquire":
                    owner = state.lock_owners.get(event.resource_id)
                    if owner is not None and owner != thread_id:
                        state.waiting_for[thread_id] = event.resource_id

        return enabled

    def apply_transition(
        self,
        state: ExplorationState,
        thread_id: str,
        event: AbstractEvent,
    ) -> ExplorationState:
        new_state = ExplorationState(
            program_counters=dict(state.program_counters),
            lock_owners=dict(state.lock_owners),
            held_locks={k: list(v) for k, v in state.held_locks.items()},
            waiting_for=dict(state.waiting_for),
        )

        if event.kind == "acquire":
            new_state.lock_owners[event.resource_id] = thread_id
            new_state.held_locks.setdefault(thread_id, []).append(event.resource_id)
            new_state.waiting_for[thread_id] = None

        elif event.kind == "release":
            current_owner = new_state.lock_owners.get(event.resource_id)
            if current_owner == thread_id:
                new_state.lock_owners[event.resource_id] = None
                held = new_state.held_locks.setdefault(thread_id, [])
                if event.resource_id in held:
                    held.remove(event.resource_id)
            new_state.waiting_for[thread_id] = None

        elif event.kind in {"read", "write"}:
            new_state.waiting_for[thread_id] = None

        new_state.program_counters[thread_id] = new_state.program_counters.get(thread_id, 0) + 1
        return new_state

    def _is_enabled(
        self,
        event: AbstractEvent,
        thread_id: str,
        state: ExplorationState,
    ) -> bool:
        if event.kind in {"read", "write"}:
            return True

        if event.kind == "acquire":
            owner = state.lock_owners.get(event.resource_id)
            return owner is None

        if event.kind == "release":
            owner = state.lock_owners.get(event.resource_id)
            return owner == thread_id

        return False