from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult
from trace_vizualizer.domain.visualization import GraphEdge, GraphNode


class GraphBuilder:
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

        canonical_to_original_resource = self._build_resource_label_mapping(
            counterexample
        )

        step_index = 0
        while step_index < len(counterexample.steps):
            step = counterexample.steps[step_index]

            thread_node_id = self._thread_node_id(step.thread_id)
            thread_label = self._format_thread_label(step.thread_id)

            self._ensure_node(
                nodes=nodes,
                seen_nodes=seen_nodes,
                node_id=thread_node_id,
                label=thread_label,
                node_type="thread",
            )

            if step.resource_id is not None:
                resource_label = self._format_resource_label(
                    step.resource_id,
                    step.original_resource,
                    canonical_to_original_resource,
                )
                resource_node_id = self._resource_node_id(step.resource_id)

                self._ensure_node(
                    nodes=nodes,
                    seen_nodes=seen_nodes,
                    node_id=resource_node_id,
                    label=resource_label,
                    node_type="resource",
                )

                edge_id = (
                    "edge:"
                    + str(step.step_index)
                    + ":"
                    + thread_node_id
                    + ":"
                    + resource_node_id
                    + ":"
                    + step.event_kind
                )

                self._ensure_edge(
                    edges=edges,
                    seen_edges=seen_edges,
                    edge_id=edge_id,
                    source=thread_node_id,
                    target=resource_node_id,
                    label=step.event_kind,
                    edge_type=step.event_kind,
                )

            step_index = step_index + 1

        final_state = counterexample.final_state
        waiting_items = list(final_state.waiting_for.items())
        waiting_items.sort(key=self._waiting_sort_key)

        pair_index = 0
        while pair_index < len(waiting_items):
            thread_id, waited_lock = waiting_items[pair_index]

            if waited_lock is not None:
                thread_node_id = self._thread_node_id(thread_id)
                thread_label = self._format_thread_label(thread_id)

                resource_label = self._format_resource_label(
                    waited_lock,
                    None,
                    canonical_to_original_resource,
                )
                resource_node_id = self._resource_node_id(waited_lock)

                self._ensure_node(
                    nodes=nodes,
                    seen_nodes=seen_nodes,
                    node_id=thread_node_id,
                    label=thread_label,
                    node_type="thread",
                )

                self._ensure_node(
                    nodes=nodes,
                    seen_nodes=seen_nodes,
                    node_id=resource_node_id,
                    label=resource_label,
                    node_type="resource",
                )

                wait_edge_id = (
                    "wait-edge:"
                    + thread_id
                    + ":"
                    + waited_lock
                )

                self._ensure_edge(
                    edges=edges,
                    seen_edges=seen_edges,
                    edge_id=wait_edge_id,
                    source=thread_node_id,
                    target=resource_node_id,
                    label="wait",
                    edge_type="wait",
                )

            pair_index = pair_index + 1

        return nodes, edges

    def _build_resource_label_mapping(
        self,
        counterexample: ExecutionScenario,
    ) -> dict[str, str]:
        mapping = {}

        index = 0
        while index < len(counterexample.steps):
            step = counterexample.steps[index]

            if step.resource_id is not None and step.original_resource is not None:
                mapping[step.resource_id] = step.original_resource

            index = index + 1

        return mapping

    def _format_resource_label(
        self,
        resource_id: str,
        original_resource: str | None,
        canonical_to_original_resource: dict[str, str],
    ) -> str:
        if resource_id in canonical_to_original_resource:
            return canonical_to_original_resource[resource_id]

        if original_resource is not None:
            return original_resource

        return resource_id

    def _thread_node_id(self, thread_id: str) -> str:
        return "thread:" + thread_id

    def _resource_node_id(self, resource_id: str) -> str:
        return "resource:" + resource_id

    def _format_thread_label(self, thread_id: str) -> str:
        if thread_id.startswith("thread_entity_"):
            suffix = thread_id.replace("thread_entity_", "")
            return "thread_" + suffix

        return thread_id

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