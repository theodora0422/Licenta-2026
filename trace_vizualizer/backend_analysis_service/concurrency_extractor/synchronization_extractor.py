from __future__ import annotations

from typing import List, Optional

from trace_vizualizer.domain.concurrency import (
    SourceLocation,
    SynchronizationOperation,
)


class SynchronizationExtractor:

    def extract_synchronization_operations(self, tree, source_code: str) -> List[SynchronizationOperation]:
        operations: List[SynchronizationOperation] = []
        self._walk(tree.root_node, source_code, operations)
        return operations

    def _walk(self, node, source_code: str, operations: List[SynchronizationOperation]) -> None:
        if node.type == "synchronized_statement":
            operation = self._extract_synchronized_statement(node, source_code)
            if operation is not None:
                operations.append(operation)

        if node.type == "method_invocation":
            method_operations = self._extract_lock_method_invocation(node, source_code)
            operations.extend(method_operations)

        for child in node.children:
            self._walk(child, source_code, operations)

    def _extract_synchronized_statement(self, node, source_code: str) -> Optional[SynchronizationOperation]:
        resource = self._extract_synchronized_resource(node, source_code)
        if resource is None:
            resource = "<unknown_monitor>"

        return SynchronizationOperation(
            kind="synchronized_block",
            resource=resource,
            source_location=self._build_source_location(node),
        )

    def _extract_synchronized_resource(self, node, source_code: str) -> Optional[str]:
        for child in node.children:
            if child.type == "parenthesized_expression":
                return self._strip_parentheses(self._node_text(child, source_code))
        return None

    def _extract_lock_method_invocation(self, node, source_code: str) -> List[SynchronizationOperation]:
        invocation_text = self._node_text(node, source_code).strip()

        if invocation_text.endswith(".lock()"):
            receiver = invocation_text[:-len(".lock()")].strip()
            if not receiver:
                receiver = "<unknown_lock>"

            return [
                SynchronizationOperation(
                    kind="lock_acquire",
                    resource=receiver,
                    source_location=self._build_source_location(node),
                )
            ]

        if invocation_text.endswith(".unlock()"):
            receiver = invocation_text[:-len(".unlock()")].strip()
            if not receiver:
                receiver = "<unknown_lock>"

            return [
                SynchronizationOperation(
                    kind="lock_release",
                    resource=receiver,
                    source_location=self._build_source_location(node),
                )
            ]

        return []

    def _extract_invocation_receiver(self, node, source_code: str) -> Optional[str]:
        object_node = None
        name_node = None

        for child in node.children:
            if child.type == "identifier" and name_node is None:
                name_node = child
            elif child.type in {"field_access", "identifier"} and object_node is None:
                object_node = child

        if object_node is not None:
            return self._node_text(object_node, source_code)

        full_text = self._node_text(node, source_code)
        if "." in full_text:
            return full_text.split(".", 1)[0].strip()

        return None

    def _find_child_text_by_type(self, node, source_code: str, target_type: str) -> Optional[str]:
        for child in node.children:
            if child.type == target_type:
                return self._node_text(child, source_code)
        return None

    def _node_text(self, node, source_code: str) -> str:
        return source_code[node.start_byte:node.end_byte]

    def _strip_parentheses(self, text: str) -> str:
        text = text.strip()
        if text.startswith("(") and text.endswith(")"):
            return text[1:-1].strip()
        return text

    def _build_source_location(self, node) -> SourceLocation:
        return SourceLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1] + 1,
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1] + 1,
        )