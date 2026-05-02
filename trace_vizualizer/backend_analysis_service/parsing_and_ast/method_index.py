from trace_vizualizer.domain.concurrency import SourceLocation


class MethodInfo:
    def __init__(self,name:str,body_name,source_location:SourceLocation):
        self.name=name
        self.body_node=body_name
        self.source_location=source_location
class MethodIndex:
    # index minimal pentru metode auxiliare fară parametri
    def build(self,tree,source_code:str):
        methods={}
        self._walk(tree.root_node,source_code,methods)
        return methods
    def _walk(self,node,source_code,methods):
        if node.type=="method_declaration":
            self._handle_method(node,source_code,methods)
        index=0
        while index<len(node.children):
            self._walk(node.children[index],source_code,methods)
            index+=1
    def _handle_method(self,node,source_code,methods):
        name_node=node.child_by_field_name("name")
        body_node=node.child_by_field_name("body")
        if name_node is None:
            return
        if body_node is None:
            return
        parameters_node=node.child_by_field_name("parameters")
        if parameters_node is not None:
            parameters_text=self._text(parameters_node,source_code).strip()
            if parameters_text != "()":
                return
        method_name=self._text(name_node,source_code).strip()
        methods[method_name]=MethodInfo(name=method_name,body_name=body_node,source_location=self._build_source_location(body_node))
    def _text(self,node,source_code):
        return source_code[node.start_byte:node.end_byte]
    def _build_source_location(self,node):
        return SourceLocation(
            start_line=node.start_point[0]+1,
            start_column=node.start_point[1]+1,
            end_line=node.end_point[0]+1,
            end_column=node.end_point[1]+1,
        )