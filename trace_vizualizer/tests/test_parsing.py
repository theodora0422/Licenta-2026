from trace_vizualizer.backend_analysis_service.parsing_and_ast.ast_diagnostics import ASTDiagnostics
from trace_vizualizer.backend_analysis_service.parsing_and_ast.java_parser import JavaParser



def test_java_parser_valid_code():
    parser=JavaParser()
    diagnostics_tool=ASTDiagnostics()
    code="""
    public class Example {
        public static void main(String[] args) {
            Object lockA = new Object();
        }
    }
    """
    tree=parser.parse(code)
    diagnostics=diagnostics_tool.collect_diagnostics(tree,code)
    assert tree.root_node.type=="program"
    assert diagnostics == []

def test_java_parser_invalid_code():
    parser=JavaParser()
    diagnostics_tool=ASTDiagnostics()

    code="""
    public class Example {
        public static void main(String[] args) {
            Object lockA = ;
        }
    }
    """
    tree=parser.parse(code)
    diagnostics=diagnostics_tool.collect_diagnostics(tree,code)
    assert len(diagnostics)>0