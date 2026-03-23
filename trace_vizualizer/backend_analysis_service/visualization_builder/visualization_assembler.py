from trace_vizualizer.domain.visualization import TimelineItem, GraphNode, GraphEdge, HighlightMarker, \
    VisualizationModel


class VisualizationAssembler:
    def build(self,*,timeline:list[TimelineItem],graph_nodes:list[GraphNode],graph_edges:list[GraphEdge],highlights:list[HighlightMarker]):
        highlighted_node_ids=set()
        highlighted_edge_ids = set()
        for marker in highlights:
            if marker.target_type=="node":
                highlighted_node_ids.add(marker.target_id)
            if marker.target_type=="edge":
                highlighted_edge_ids.add(marker.target_id)

        final_nodes=[]
        for node in graph_nodes:
            final_nodes+=GraphNode(id=node.id,label=node.label,node_type=node.node_type,highlighted=node.id in highlighted_node_ids)
        final_edges=[]
        for edge in graph_edges:
            final_edges+=GraphEdge(id=edge.id,source=edge.source,target=edge.target,label=edge.label,edge_type=edge.edge_type,highlighted=edge.id in highlighted_edge_ids)

        return VisualizationModel(
            timeline=timeline, graph_nodes=graph_nodes, graph_edges=graph_edges, highlights=highlights
        )