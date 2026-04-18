from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import GraphEdge, GraphNode


class GraphBuilder:
    # construiește graful scenariului și completează cu muchii de wait
    # din starea finală


    def build(
        self,
        counterexample: ExecutionScenario | None,
        verification_result: UnifiedVerificationResult,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        if counterexample is None:
            return [], []

        nodes = []
        edges = []

        seen_nodes = set()
        seen_edges = set()

        step_index = 0
        while step_index < len(counterexample.steps):
            step = counterexample.steps[step_index]

            thread_node_id = "thread:" + step.thread_id
            self._ensure_node(
                nodes,
                seen_nodes,
                thread_node_id,
                step.thread_id,
                "thread",
            )

            if step.original_resource is not None:
                resource_node_id = "resource:" + step.original_resource
                self._ensure_node(
                    nodes,
                    seen_nodes,
                    resource_node_id,
                    step.original_resource,
                    "resource",
                )

                edge_id = (
                    "edge:" + str(step.step_index)
                    + ":" + thread_node_id
                    + ":" + resource_node_id
                    + ":" + step.event_kind
                )

                self._ensure_edge(
                    edges,
                    seen_edges,
                    edge_id,
                    thread_node_id,
                    resource_node_id,
                    step.event_kind,
                    step.event_kind,
                )

            step_index = step_index + 1

        final_state = counterexample.final_state
        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        pair_index = 0
        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                thread_node_id = "thread:" + thread_id
                resource_node_id = "resource:" + waited_lock

                self._ensure_node(
                    nodes,
                    seen_nodes,
                    thread_node_id,
                    thread_id,
                    "thread",
                )

                self._ensure_node(
                    nodes,
                    seen_nodes,
                    resource_node_id,
                    waited_lock,
                    "resource",
                )

                wait_edge_id = "wait-edge:" + thread_id + ":" + waited_lock
                self._ensure_edge(
                    edges,
                    seen_edges,
                    wait_edge_id,
                    thread_node_id,
                    resource_node_id,
                    "wait",
                    "wait",
                )

            pair_index = pair_index + 1

        return nodes, edges

    def _ensure_node(
        self,
        nodes: list[GraphNode],
        seen_nodes: set,
        node_id: str,
        label: str,
        node_type: str,
    ) -> None:
        if node_id in seen_nodes:
            return

        nodes.append(
            GraphNode(
                id=node_id,
                label=label,
                node_type=node_type,
                highlighted=False,
            )
        )
        seen_nodes.add(node_id)

    def _ensure_edge(
        self,
        edges: list[GraphEdge],
        seen_edges: set,
        edge_id: str,
        source: str,
        target: str,
        label: str,
        edge_type: str,
    ) -> None:
        if edge_id in seen_edges:
            return

        edges.append(
            GraphEdge(
                id=edge_id,
                source=source,
                target=target,
                label=label,
                edge_type=edge_type,
                highlighted=False,
            )
        )
        seen_edges.add(edge_id)

    def _waiting_sort_key(self, item):
        thread_id, waited_lock = item
        return (thread_id, waited_lock or "")