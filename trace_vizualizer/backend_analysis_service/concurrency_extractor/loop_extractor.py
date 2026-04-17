from trace_vizualizer.domain.concurrency import LoopRegionInfo, SourceLocation


class LoopExtractor:
    def extract_loops(self,tree):
        results=[]
        counters={"loop":1}
        self._walk(tree.root_node,results,counters)
        return results
    def _walk(self,node,results:list[LoopRegionInfo],counters:dict):
        loop_kind=self._map_loop_kind(node.type)
        if loop_kind is not None:
            loop_id="loop_" + str(counters["loop"])
            counters["loop"]=counters["loop"]+1
            results.append(LoopRegionInfo(loop_id=loop_id,loop_kind=loop_kind,source_location=self._build_source_location(node)))

        child_index=0
        while child_index<len(node.children):
            child=node.children[child_index]
            self._walk(child,results,counters)
            child_index=child_index+1
    def _map_loop_kind(self,node_type:str):
        if node_type=="while_statement":
            return "while"
        if node_type=="for_statement":
            return "for"
        if node_type=="enhanced_for_statement":
            return "enhanced_for"
        if node_type=="do_statement":
            return "do_while"
        return None
    def _build_source_location(self,node):
        return SourceLocation(
            start_line=node.start_point[0]+1,
            start_column=node.start_point[1]+1,
            end_line=node.end_point[0]+1,
            end_column=node.end_point[1]+1,
        )