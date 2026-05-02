class ConditionalScopeResolver:
    """
    Determina daca un nod este in interiorul unei ramuri if care poate fie xclusa pe baza unei conditii boolene simple
    Suport pentru:
        if (true)
        if (false)
        if (booleanVariable)
        if (!booleanVariable)
    """
    def is_node_reachable(self,node,source_code:str,boolean_constants:dict):
        current=node
        while current is not None:
            parent=current.parent
            if parent is not None and parent.type=="if_statement":
                branch_kind=self._get_branch_kind(parent,current)
                condition_value=self._evaluate_condition(parent,source_code,boolean_constants)
                if condition_value is not None:
                    if branch_kind == "then" and condition_value is False:
                        return False
                    if branch_kind == "else" and condition_value is True:
                        return False
            current=parent
        return True
    def _get_branch_kind(self,if_node,child_node):
        consequence=if_node.child_by_field_name("consequence")
        alternative=if_node.child_by_field_name("alternative")
        if consequence is not None:
            if self._contains_node(consequence,child_node):
                return "then"
        if alternative is not None:
            if self._contains_node(alternative,child_node):
                return "else"
        return None
    def _evaluate_condition(self,if_node,source_code,boolean_constants):
        condition=if_node.child_by_field_name("condition")
        if condition is None:
            return None
        text=self._text(condition,source_code)
        text=text.strip()
        if text.startswith("(") and text.endswith(")"):
            text=text[1:len(text)-1].strip()
        if text=="true":
            return True
        if text=="false":
            return False
        if text.startswith("!"):
            name=text[1:].strip()
            if name is boolean_constants:
                    return not boolean_constants[name]
        if text in boolean_constants:
            return boolean_constants[text]
        return None
    def _contains_node(self,outer,inner):
        if inner.start_byte>=outer.start_byte and inner.end_byte<=outer.end_byte:
            return True
        return False
    def _text(self,node,source_code):
        return source_code[node.start_byte:node.end_byte]