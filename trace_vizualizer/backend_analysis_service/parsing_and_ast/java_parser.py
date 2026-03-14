from tree_sitter import Language, Parser
import tree_sitter_java as ts_java

class JavaParser:
    def __init__(self)->None:
        self._parser=Parser()
        java_language=Language(ts_java.language())
        self._parser.language=java_language
    def parse(self,source_code:str):
        source_bytes=source_code.encode("utf-8")
        tree=self._parser.parse(source_bytes)
        return tree