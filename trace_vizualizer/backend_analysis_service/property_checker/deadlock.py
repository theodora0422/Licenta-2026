from trace_vizualizer.domain.model import ProgramModel
from trace_vizualizer.domain.scenario import ExecutionScenario, ScenarioGenerationResult
from trace_vizualizer.domain.verification import VerificationFinding, VerificationResult
from trace_vizualizer.backend_analysis_service.scenario_generator.transition_system import TransitionSystem


class DeadlockChecker:
    """
    Detectează deadlock doar dacă există ciclu real în graful wait-for.

    Regulă:
    - starea finală nu are tranziții enabled;
    - există thread-uri care așteaptă lock-uri;
    - din relația:
         thread waits for lock
         lock owned by other thread
      se construiește un graf wait-for între thread-uri;
    - se raportează deadlock doar dacă există ciclu în acest graf.
    """

    def __init__(self) -> None:
        self.transition_system = TransitionSystem()

    def check(
        self,
        scenario_generation_result: ScenarioGenerationResult,
    ) -> VerificationResult:
        program_model = scenario_generation_result.program_model_snapshot

        scenario_index = 0
        while scenario_index < len(scenario_generation_result.scenarios):
            scenario = scenario_generation_result.scenarios[scenario_index]

            deadlock_info = self._analyze_deadlock_scenario(scenario, program_model)
            if deadlock_info is not None:
                return VerificationResult(
                    deadlock_detected=True,
                    data_race_detected=False,
                    mutual_exclusion_violated=False,
                    starvation_detected=False,
                    findings=[
                        VerificationFinding(
                            property_name="deadlock",
                            violated=True,
                            message="A potential deadlock was detected during scenario exploration.",
                            scenario_id=scenario.scenario_id,
                        )
                    ],
                    counterexample=scenario,
                )

            scenario_index = scenario_index + 1

        return VerificationResult(
            deadlock_detected=False,
            data_race_detected=False,
            mutual_exclusion_violated=False,
            starvation_detected=False,
            findings=[
                VerificationFinding(
                    property_name="deadlock",
                    violated=False,
                    message="No deadlock state was detected.",
                    scenario_id=None,
                )
            ],
            counterexample=None,
        )

    def _analyze_deadlock_scenario(
        self,
        scenario: ExecutionScenario,
        program_model: ProgramModel,
    ) -> dict | None:
        final_state = scenario.final_state

        enabled = self.transition_system.get_enabled_transitions(final_state, program_model)
        if len(enabled) > 0:
            return None

        wait_for_graph = self._build_wait_for_graph(final_state)

        if len(wait_for_graph) == 0:
            return None

        cycle = self._find_cycle(wait_for_graph)
        if cycle is None:
            return None

        return {
            "cycle": cycle,
        }

    def _build_wait_for_graph(self, final_state) -> dict[str, list[str]]:
        graph = {}

        waiting_items = list(final_state.waiting_for.items())
        index = 0
        while index < len(waiting_items):
            thread_id, waited_lock = waiting_items[index]

            if waited_lock is not None:
                owner = final_state.lock_owners.get(waited_lock)

                if owner is not None:
                    if owner != thread_id:
                        if thread_id not in graph:
                            graph[thread_id] = []
                        graph[thread_id].append(owner)

            index = index + 1

        return graph

    def _find_cycle(self, graph: dict[str, list[str]]) -> list[str] | None:
        visited = set()
        recursion_stack = set()
        path = []

        node_keys = list(graph.keys())
        index = 0
        while index < len(node_keys):
            node = node_keys[index]

            if node not in visited:
                cycle = self._dfs_cycle(
                    node=node,
                    graph=graph,
                    visited=visited,
                    recursion_stack=recursion_stack,
                    path=path,
                )
                if cycle is not None:
                    return cycle

            index = index + 1

        return None

    def _dfs_cycle(
        self,
        node: str,
        graph: dict[str, list[str]],
        visited: set,
        recursion_stack: set,
        path: list[str],
    ) -> list[str] | None:
        visited.add(node)
        recursion_stack.add(node)
        path.append(node)

        neighbors = graph.get(node, [])
        neighbor_index = 0

        while neighbor_index < len(neighbors):
            neighbor = neighbors[neighbor_index]

            if neighbor not in visited:
                cycle = self._dfs_cycle(
                    node=neighbor,
                    graph=graph,
                    visited=visited,
                    recursion_stack=recursion_stack,
                    path=path,
                )
                if cycle is not None:
                    return cycle

            elif neighbor in recursion_stack:
                return self._extract_cycle_from_path(path, neighbor)

            neighbor_index = neighbor_index + 1

        recursion_stack.remove(node)
        path.pop()
        return None

    def _extract_cycle_from_path(self, path: list[str], repeated_node: str) -> list[str]:
        cycle = []

        index = 0
        start_found = False

        while index < len(path):
            current = path[index]
            if current == repeated_node:
                start_found = True

            if start_found:
                cycle.append(current)

            index = index + 1

        cycle.append(repeated_node)
        return cycle