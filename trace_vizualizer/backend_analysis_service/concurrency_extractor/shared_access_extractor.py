from __future__ import annotations

from typing import List

from trace_vizualizer.domain.concurrency import (
    SharedAccessOperation,
    SourceLocation,
)


class SharedAccessExtractor:

    def extract_shared_access_operations(self, tree, source_code: str) -> List[SharedAccessOperation]:
        operations: List[SharedAccessOperation] = []
        self._walk(tree.root_node, source_code, operations)
        return operations

    def _walk(self, node, source_code: str, operations: List[SharedAccessOperation]) -> None:
        if node.type == "assignment_expression":
            operation = self._extract_assignment(node, source_code)
            if operation is not None:
                operations.append(operation)

        elif node.type == "update_expression":
            operation = self._extract_update_expression(node, source_code)
            if operation is not None:
                operations.append(operation)

        for child in node.children:
            self._walk(child, source_code, operations)

    def _extract_assignment(self, node, source_code: str) -> SharedAccessOperation | None:
        left_side = self._extract_left_hand_side(node, source_code)
        if left_side is None:
            return None

        return SharedAccessOperation(
            kind="write",
            resource=left_side,
            expression=self._node_text(node, source_code).strip(),
            source_location=self._build_source_location(node),
        )

    def _extract_update_expression(self, node, source_code: str) -> SharedAccessOperation | None:
        expression_text = self._node_text(node, source_code).strip()
        resource = self._extract_update_target(expression_text)

        if resource is None:
            return None

        return SharedAccessOperation(
            kind="write",
            resource=resource,
            expression=expression_text,
            source_location=self._build_source_location(node),
        )

    def _extract_field_read(self, node, source_code: str) -> SharedAccessOperation | None:
        field_text = self._node_text(node, source_code).strip()

        return SharedAccessOperation(
            kind="read",
            resource=field_text,
            expression=field_text,
            source_location=self._build_source_location(node),
        )

    def _extract_left_hand_side(self, node, source_code: str) -> str | None:
        text = self._node_text(node, source_code)
        if "=" not in text:
            return None

        left_side = text.split("=", 1)[0].strip()
        return left_side if left_side else None

    def _extract_update_target(self, expression_text: str) -> str | None:
        cleaned = expression_text.replace("++", "").replace("--", "").strip()
        return cleaned if cleaned else None

    def _node_text(self, node, source_code: str) -> str:
        return source_code[node.start_byte:node.end_byte]

    def _build_source_location(self, node) -> SourceLocation:
        return SourceLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )