import re

from trace_vizualizer.domain.concurrency import SharedAccessOperation, SourceLocation
from trace_vizualizer.backend_analysis_service.parsing_and_ast.conditional_scope_resolver import ConditionalScopeResolver


class SharedAccessExtractor:
    def __init__(self):
        self.conditional_scope_resolver = ConditionalScopeResolver()

    def extract_shared_access_operations(
        self,
        tree,
        source_code: str,
        boolean_constants: dict | None = None,
        method_index: dict | None = None,
    ) -> list[SharedAccessOperation]:
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
        results: list[SharedAccessOperation],
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

        if node.type == "assignment_expression":
            operation = self._extract_assignment(
                node=node,
                source_code=source_code,
                location_override=None,
            )
            if operation is not None:
                results.append(operation)

        if node.type == "update_expression":
            operation = self._extract_update(
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
        results: list[SharedAccessOperation],
    ) -> bool:
        invocation_text = self._text(node, source_code).strip()
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
        results: list[SharedAccessOperation],
    ) -> None:
        statements = self._split_body_into_statements(method_body_text)

        index = 0
        while index < len(statements):
            statement = statements[index].strip()

            operation = self._extract_update_from_text(
                statement,
                call_site_location,
            )
            if operation is not None:
                results.append(operation)

            operation = self._extract_assignment_from_text(
                statement,
                call_site_location,
            )
            if operation is not None:
                results.append(operation)

            index = index + 1

    def _split_body_into_statements(self, body_text: str) -> list[str]:
        text = body_text.replace("{", "\n").replace("}", "\n")
        raw_parts = text.split(";")

        parts = []
        index = 0
        while index < len(raw_parts):
            part = raw_parts[index].strip()
            if part != "":
                parts.append(part)
            index = index + 1

        return parts

    def _extract_update_from_text(
        self,
        statement: str,
        call_site_location: SourceLocation,
    ) -> SharedAccessOperation | None:
        update_match = re.search(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*(\+\+|--)",
            statement,
        )

        if update_match is None:
            return None

        resource = update_match.group(1)

        if resource.startswith("System"):
            return None

        return SharedAccessOperation(
            kind="write",
            resource=resource,
            expression=statement,
            source_location=call_site_location,
        )

    def _extract_assignment_from_text(
        self,
        statement: str,
        call_site_location: SourceLocation,
    ) -> SharedAccessOperation | None:
        if "=" not in statement:
            return None

        if "==" in statement:
            return None

        left = statement.split("=")[0].strip()

        if left == "":
            return None

        if " " in left:
            left_parts = left.split()
            left = left_parts[len(left_parts) - 1]

        if left.startswith("System"):
            return None

        return SharedAccessOperation(
            kind="write",
            resource=left,
            expression=statement,
            source_location=call_site_location,
        )

    def _extract_assignment(
        self,
        node,
        source_code: str,
        location_override: SourceLocation | None,
    ) -> SharedAccessOperation | None:
        text = self._text(node, source_code).strip()

        if "=" not in text:
            return None

        if "==" in text:
            return None

        left = text.split("=")[0].strip()

        if left == "":
            return None

        if left.startswith("System."):
            return None

        effective_location = self._build_source_location(node)
        if location_override is not None:
            effective_location = location_override

        return SharedAccessOperation(
            kind="write",
            resource=left,
            expression=text,
            source_location=effective_location,
        )

    def _extract_update(
        self,
        node,
        source_code: str,
        location_override: SourceLocation | None,
    ) -> SharedAccessOperation | None:
        text = self._text(node, source_code).strip()

        resource = text.replace("++", "").replace("--", "").strip()

        if resource == "":
            return None

        if resource.startswith("System."):
            return None

        effective_location = self._build_source_location(node)
        if location_override is not None:
            effective_location = location_override

        return SharedAccessOperation(
            kind="write",
            resource=resource,
            expression=text,
            source_location=effective_location,
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