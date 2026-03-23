from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.visualization import GraphNode, GraphEdge


class GraphBuilder:
    def build(self,counterexample:ExecutionScenario|None):
        if counterexample is None:
            return [],[]
        nodes:list[GraphNode]=[]
        edges:list[GraphEdge]=[]
        seen_nodes:set[str]=set()
        seen_edges:set[str]=set()

        for step in counterexample.steps:
            thread_node_id=f"thread:{step.thread_id}"
            if thread_node_id not in seen_nodes:
                nodes.append(
                    GraphNode(
                        id=thread_node_id,
                        label=step.thread_id,
                        node_type="thread",
                    )
                )
                seen_nodes.add(thread_node_id)
            if step.original_resource:
                resource_node_id=f"resource:{step.original_resource}"
                if resource_node_id not in seen_nodes:
                    nodes.append(
                        GraphNode(
                            id=resource_node_id,
                            label=step.original_resource,
                            node_type="resource",
                        )
                    )
                    seen_nodes.add(resource_node_id)
                edge_id=f"Edge:{step.step_index}:{thread_node_id}:{resource_node_id}:{step.event_kind}"
                if edge_id not in seen_edges:
                    edges.append(
                        GraphEdge(
                            id=edge_id,
                            source=thread_node_id,
                            target=resource_node_id,
                            label=step.event_kind,
                            edge_type=step.event_kind,
                        )
                    )
                    seen_edges.add(edge_id)
        final_state=counterexample.final_state
        for thread_id,waited_lock in final_state.waiting_for.items():
            if waited_lock is None:
                continue
            thread_node_id=f"thread:{thread_id}"
            resource_node_id=f"resource:{waited_lock}"

            if thread_node_id not in seen_nodes:
                nodes.append(
                    GraphNode(
                        id=thread_node_id,
                        label=thread_id,
                        node_type="thread",
                    )
                )
                seen_nodes.add(thread_node_id)
            if resource_node_id not in seen_nodes:
                nodes.append(
                    GraphNode(
                        id=resource_node_id,
                        label=waited_lock,
                        node_type="resource",
                    )
                )
                seen_nodes.add(resource_node_id)
            edge_id=f"wait-edge:{thread_id}:{waited_lock}"
            if edge_id not in seen_edges:
                edges.append(
                    GraphEdge(
                        id=edge_id,
                        source=thread_node_id,
                        target=resource_node_id,
                        label="wait",
                        edge_type="wait",
                    )
                )
                seen_edges.add(edge_id)
        return nodes,edges
