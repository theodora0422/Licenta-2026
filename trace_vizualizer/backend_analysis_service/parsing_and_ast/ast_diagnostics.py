from trace_vizualizer.domain.parsing import ASTDiagnostic


class ASTDiagnostics:
    def collect_diagnostics(self,tree,source_code:str)->list[ASTDiagnostic]:
        diagnostics:list[ASTDiagnostic]=[]
        self._walk(tree.root_node,diagnostics)
        return diagnostics
    def _walk(self,node,diagnostics:list[ASTDiagnostic])->None:
        if node.type=="ERROR":
            diagnostics.append(
                ASTDiagnostic(
                    message="Syntax error detected during Java parsing",
                    line=node.start_point[0]+1,
                    column=node.start_point[1]+1,
                    severity="error",
                )
            )
        if node.is_missing:
            diagnostics.append(
                ASTDiagnostic(
                    message=f"Missing syntax element near '{node.type}'",
                    line=node.start_point[0]+1,
                    column=node.start_point[1]+1,
                    severity="error",

                )
            )
        for child in node.children:
            self._walk(child,diagnostics)
