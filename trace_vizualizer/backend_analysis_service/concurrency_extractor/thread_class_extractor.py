from trace_vizualizer.domain.concurrency import SourceLocation, ThreadClassInfo


class ThreadClassExtractor:
    # detectează clase care extind Thread sau implementează Runnable
    # și extrage locația metodei run().

    def extract_thread_classes(self, tree, source_code: str) -> list[ThreadClassInfo]:
        results = []
        self._walk(tree.root_node, source_code, results)
        return results

    def _walk(self, node, source_code: str, results: list[ThreadClassInfo]) -> None:
        if node.type == "class_declaration":
            info = self._extract_from_class(node, source_code)
            if info is not None:
                results.append(info)

        child_index = 0
        while child_index < len(node.children):
            child = node.children[child_index]
            self._walk(child, source_code, results)
            child_index = child_index + 1

    def _extract_from_class(self, node, source_code: str) -> ThreadClassInfo | None:
        class_name = self._find_first_child_text(node, source_code, "identifier")
        if class_name is None:
            return None

        superclass_text = self._find_first_child_text(node, source_code, "superclass")
        interfaces_text = self._find_first_child_text(node, source_code, "super_interfaces")

        kind = None

        if superclass_text is not None:
            if "Thread" in superclass_text:
                kind = "thread_class"

        if kind is None and interfaces_text is not None:
            if "Runnable" in interfaces_text:
                kind = "runnable_class"

        if kind is None:
            return None

        run_method_location = self._find_run_method_location(node)

        return ThreadClassInfo(
            identifier="thread-class:" + class_name,
            class_name=class_name,
            kind=kind,
            class_location=self._build_source_location(node),
            run_method_location=run_method_location,
        )

    def _find_run_method_location(self, class_node) -> SourceLocation | None:
        child_index = 0
        while child_index < len(class_node.children):
            child = class_node.children[child_index]

            if child.type == "class_body":
                method_location = self._search_run_method_in_class_body(child)
                if method_location is not None:
                    return method_location

            child_index = child_index + 1

        return None

    def _search_run_method_in_class_body(self, class_body_node) -> SourceLocation | None:
        child_index = 0
        while child_index < len(class_body_node.children):
            child = class_body_node.children[child_index]

            if child.type == "method_declaration":
                method_name = self._find_first_child_text(child, None, "identifier", use_node_text=False)
                if method_name == "run":
                    body_node = self._find_first_child_node(child, "block")
                    if body_node is not None:
                        return self._build_source_location(body_node)
                    return self._build_source_location(child)

            child_index = child_index + 1

        return None

    def _find_first_child_text(
        self,
        node,
        source_code: str | None,
        wanted_type: str,
        use_node_text: bool = True,
    ) -> str | None:
        child_index = 0
        while child_index < len(node.children):
            child = node.children[child_index]
            if child.type == wanted_type:
                if use_node_text:
                    if source_code is None:
                        return None
                    return self._node_text(child, source_code)
                return child.text.decode("utf-8")
            child_index = child_index + 1
        return None

    def _find_first_child_node(self, node, wanted_type: str):
        child_index = 0
        while child_index < len(node.children):
            child = node.children[child_index]
            if child.type == wanted_type:
                return child
            child_index = child_index + 1
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