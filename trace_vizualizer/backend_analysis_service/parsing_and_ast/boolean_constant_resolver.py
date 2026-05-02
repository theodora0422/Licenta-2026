
class BooleanConstantResolver:
    # extrage val boolene: static boolean flax=true / false; static final boolean flag=true
    def resolve(self,tree,source_code:str):
        result={}
        self._walk(tree.root_node,source_code,result)
        return result
    def _walk(self,node,source_code:str,result:dict):
        if node.type=="field_declaration":
            self._handle_field_declaration(node,source_code,result)
        index=0
        while index<len(node.children):
            self._walk(node.children[index],source_code, result)
            index+=1
    def _handle_field_declaration(self,node,source_code:str,result:dict):
        text=self._text(node,source_code)
        if "boolean" not in text:
            return
        if "=" not in text:
            return
        clean_text=text.replace(";","").strip()
        parts=clean_text.split("=")
        if len(parts)!=2:
            return
        left=parts[0].strip()
        right=parts[1].strip()
        if right!="true" and right!="false":
            return
        left_parts=left.split()
        if len(left_parts)==0:
            return
        variable_name=left_parts[len(left_parts)-1]
        result[variable_name]=right=="true"
    def _text(self,node,source_code:str):
        return source_code[node.start_byte:node.end_byte]