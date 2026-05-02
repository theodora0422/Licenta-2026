import re

from trace_vizualizer.domain.concurrency import SourceLocation, SynchronizationOperation
from trace_vizualizer.backend_analysis_service.parsing_and_ast.conditional_scope_resolver import ConditionalScopeResolver


class SynchronizationExtractor:
    def __init__(self):
        self.conditional_scope_resolver = ConditionalScopeResolver()

    def extract_synchronization_operations(
        self,
        tree,
        source_code: str,
        boolean_constants: dict | None = None,
        method_index: dict | None = None,
    ) -> list[SynchronizationOperation]:
        if boolean_constants is None:
            boolean_constants = {}

        if method_index is None:
            method_index = {}

        results = []
        visited_methods = []

        self._walk(
            node=tree.root_node,
            source_code=source_code,
            boolean_constants=boolean_constants,
            method_index=method_index,
            visited_methods=visited_methods,
            results=results,
        )

        return results

    def _walk(
        self,
        node,
        source_code: str,
        boolean_constants: dict,
        method_index: dict,
        visited_methods: list,
        results: list[SynchronizationOperation],
    ) -> None:
        if not self.conditional_scope_resolver.is_node_reachable(
            node,
            source_code,
            boolean_constants,
        ):
            return

        if node.type == "method_invocation":
            handled = self._handle_method_invocation(
                node=node,
                source_code=source_code,
                method_index=method_index,
                visited_methods=visited_methods,
                results=results,
            )

            if handled:
                return

        if node.type == "synchronized_statement":
            operation = self._extract_synchronized_block(
                node=node,
                source_code=source_code,
                location_override=None,
            )
            if operation is not None:
                results.append(operation)

        index = 0
        while index < len(node.children):
            self._walk(
                node=node.children[index],
                source_code=source_code,
                boolean_constants=boolean_constants,
                method_index=method_index,
                visited_methods=visited_methods,
                results=results,
            )
            index = index + 1

    def _handle_method_invocation(
        self,
        node,
        source_code: str,
        method_index: dict,
        visited_methods: list,
        results: list[SynchronizationOperation],
    ) -> bool:
        invocation_text = self._text(node, source_code).strip()

        if invocation_text.endswith(".lock()"):
            resource = invocation_text.replace(".lock()", "").strip()
            results.append(
                SynchronizationOperation(
                    kind="lock_acquire",
                    resource=resource,
                    source_location=self._build_source_location(node),
                    expression=invocation_text,
                )
            )
            return True

        if invocation_text.endswith(".unlock()"):
            resource = invocation_text.replace(".unlock()", "").strip()
            results.append(
                SynchronizationOperation(
                    kind="lock_release",
                    resource=resource,
                    source_location=self._build_source_location(node),
                    expression=invocation_text,
                )
            )
            return True

        method_name = self._extract_simple_method_name(invocation_text)

        if method_name is None:
            return False

        if method_name not in method_index:
            return False

        if method_name in visited_methods:
            return True

        call_site_location = self._build_source_location(node)

        visited_methods.append(method_name)
        method_info = method_index[method_name]
        method_body_text = self._text(method_info.body_node, source_code)

        self._extract_operations_from_method_body_text(
            method_body_text=method_body_text,
            call_site_location=call_site_location,
            results=results,
        )

        visited_methods.pop()
        return True

    def _extract_operations_from_method_body_text(
        self,
        method_body_text: str,
        call_site_location: SourceLocation,
        results: list[SynchronizationOperation],
    ) -> None:
        synchronized_matches = re.finditer(
            r"synchronized\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)",
            method_body_text,
        )

        for match in synchronized_matches:
            resource = match.group(1)
            results.append(
                SynchronizationOperation(
                    kind="synchronized_block",
                    resource=resource,
                    source_location=call_site_location,
                    expression=None,
                )
            )

        lock_matches = re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.lock\s*\(\s*\)",
            method_body_text,
        )

        for match in lock_matches:
            resource = match.group(1)
            results.append(
                SynchronizationOperation(
                    kind="lock_acquire",
                    resource=resource,
                    source_location=call_site_location,
                    expression=resource + ".lock()",
                )
            )

        unlock_matches = re.finditer(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\.unlock\s*\(\s*\)",
            method_body_text,
        )

        for match in unlock_matches:
            resource = match.group(1)
            results.append(
                SynchronizationOperation(
                    kind="lock_release",
                    resource=resource,
                    source_location=call_site_location,
                    expression=resource + ".unlock()",
                )
            )

    def _extract_synchronized_block(
        self,
        node,
        source_code: str,
        location_override: SourceLocation | None,
    ) -> SynchronizationOperation | None:
        text = self._text(node, source_code)

        start = text.find("(")
        end = text.find(")")

        if start == -1:
            return None

        if end == -1:
            return None

        resource = text[start + 1:end].strip()

        effective_location = self._build_source_location(node)
        if location_override is not None:
            effective_location = location_override

        return SynchronizationOperation(
            kind="synchronized_block",
            resource=resource,
            source_location=effective_location,
            expression=None,
        )

    def _extract_simple_method_name(self, invocation_text: str) -> str | None:
        if "(" not in invocation_text:
            return None

        if ")" not in invocation_text:
            return None

        if "." in invocation_text:
            return None

        name = invocation_text.split("(")[0].strip()

        if name == "":
            return None

        return name

    def _text(self, node, source_code: str) -> str:
        return source_code[node.start_byte:node.end_byte]

    def _build_source_location(self, node) -> SourceLocation:
        return SourceLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )