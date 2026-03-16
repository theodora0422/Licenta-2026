from typing import List, Optional

from trace_vizualizer.domain.concurrency import SourceLocation, ThreadInfo


class ThreadExtractor:

    def extract_threads(self, tree, source_code: str) -> List[ThreadInfo]:
        threads: List[ThreadInfo] = []
        self._walk(tree.root_node, source_code, threads)
        return threads

    def _walk(self, node, source_code: str, threads: List[ThreadInfo]) -> None:
        if node.type == "class_declaration":
            thread_info = self._extract_thread_from_class(node, source_code)
            if thread_info is not None:
                threads.append(thread_info)

        if node.type == "object_creation_expression":
            thread_info = self._extract_thread_from_object_creation(node, source_code)
            if thread_info is not None:
                threads.append(thread_info)

        if node.type == "method_invocation":
            thread_info = self._extract_thread_start_invocation(node, source_code)
            if thread_info is not None:
                threads.append(thread_info)

        for child in node.children:
            self._walk(child, source_code, threads)

    def _extract_thread_from_class(self, node, source_code: str) -> Optional[ThreadInfo]:
        class_name = self._find_child_text_by_type(node, source_code, "identifier")
        if class_name is None:
            return None

        superclass_text = self._find_child_text_by_type(node, source_code, "superclass")
        interfaces_text = self._find_child_text_by_type(node, source_code, "super_interfaces")

        if superclass_text and "Thread" in superclass_text:
            return ThreadInfo(
                identifier=f"class:{class_name}",
                kind="thread_subclass",
                name=class_name,
                source_location=self._build_source_location(node),
            )

        if interfaces_text and "Runnable" in interfaces_text:
            return ThreadInfo(
                identifier=f"class:{class_name}",
                kind="runnable_implementation",
                name=class_name,
                source_location=self._build_source_location(node),
            )

        return None

    def _extract_thread_from_object_creation(self, node, source_code: str) -> Optional[ThreadInfo]:
        created_type = self._find_child_text_by_type(node, source_code, "type_identifier")

        if created_type == "Thread":
            return ThreadInfo(
                identifier=f"new-thread:{node.start_point[0] + 1}:{node.start_point[1] + 1}",
                kind="thread_instantiation",
                name="Thread",
                source_location=self._build_source_location(node),
            )

        return None

    def _extract_thread_start_invocation(self, node, source_code: str) -> Optional[ThreadInfo]:
        invocation_text = self._node_text(node, source_code).strip()

        if not invocation_text.endswith(".start()"):
            return None

        receiver = invocation_text[:-len(".start()")].strip()
        if not receiver:
            receiver = "unknown_thread_reference"

        return ThreadInfo(
            identifier=f"start-call:{node.start_point[0] + 1}:{node.start_point[1] + 1}",
            kind="thread_start_invocation",
            name=receiver,
            source_location=self._build_source_location(node),
        )

    def _find_child_text_by_type(self, node, source_code: str, target_type: str) -> Optional[str]:
        for child in node.children:
            if child.type == target_type:
                return self._node_text(child, source_code)
        return None

    def _node_text(self, node, source_code: str) -> str:
        return source_code[node.start_byte:node.end_byte]

    def _build_source_location(self, node) -> SourceLocation:
        return SourceLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )