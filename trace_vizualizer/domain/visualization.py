from socketserver import StreamRequestHandler
from typing import Optional, List

from pydantic import BaseModel


class TimelineItem(BaseModel):
    step_index:int
    thread_id:str
    action:str
    resource:Optional[str]=None
    line:Optional[int]=None
    label:str
    derived:bool=False

class GraphNode(BaseModel):
    id:str
    label:str
    node_type:str
    highlighted:bool=False
class GraphEdge(BaseModel):
    id:str
    source:str
    target:str
    label:str
    edge_type:str
    highlighted:bool=False
class HighlightMarker(BaseModel):
    target_type:str
    target_id:str
    reason:str
class VisualizationModel(BaseModel):
    timeline:List[TimelineItem]
    graph_nodes:List[GraphNode]
    graph_edges:List[GraphEdge]
    highlights:List[HighlightMarker]
