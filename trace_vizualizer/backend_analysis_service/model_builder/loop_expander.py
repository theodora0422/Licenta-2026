from trace_vizualizer.domain.concurrency import ExpandedSharedAccessOperation,ExpandedSynchronizationOperation,LoopRegionInfo,SourceLocation

class LoopExpander:
    # repetă bounded operațiile aflate în interiorul unei bucle

    def expand_synchronization_operations(
        self,
        operations: list,
        loop_regions: list[LoopRegionInfo],
        scope_location: SourceLocation,
        loop_unroll_factor: int,
    ) -> list[ExpandedSynchronizationOperation]:
        results = []
        ordered_operations = self._sort_operations(operations)

        index = 0
        while index < len(ordered_operations):
            operation = ordered_operations[index]

            if self._contains(scope_location, operation.source_location):
                containing_loop = self._find_smallest_containing_loop(
                    operation.source_location,
                    loop_regions,
                    scope_location,
                )

                repeat_count = 1
                if containing_loop is not None:
                    repeat_count = loop_unroll_factor

                iteration = 1
                while iteration <= repeat_count:
                    results.append(
                        ExpandedSynchronizationOperation(
                            kind=operation.kind,
                            resource=operation.original_resource if hasattr(operation, "original_resource") else operation.resource,
                            source_location=operation.source_location,
                            expression=operation.expression,
                            iteration_index=iteration,
                            synthetic_order_offset=(iteration - 1) * 1000,
                        )
                    )
                    iteration = iteration + 1

            index = index + 1

        return results

    def expand_shared_access_operations(
        self,
        operations: list,
        loop_regions: list[LoopRegionInfo],
        scope_location: SourceLocation,
        loop_unroll_factor: int,
    ) -> list[ExpandedSharedAccessOperation]:
        results = []
        ordered_operations = self._sort_operations(operations)

        index = 0
        while index < len(ordered_operations):
            operation = ordered_operations[index]

            if self._contains(scope_location, operation.source_location):
                containing_loop = self._find_smallest_containing_loop(
                    operation.source_location,
                    loop_regions,
                    scope_location,
                )

                repeat_count = 1
                if containing_loop is not None:
                    repeat_count = loop_unroll_factor

                iteration = 1
                while iteration <= repeat_count:
                    results.append(
                        ExpandedSharedAccessOperation(
                            kind=operation.kind,
                            resource=operation.original_resource if hasattr(operation, "original_resource") else operation.resource,
                            expression=operation.expression,
                            source_location=operation.source_location,
                            iteration_index=iteration,
                            synthetic_order_offset=(iteration - 1) * 1000,
                        )
                    )
                    iteration = iteration + 1

            index = index + 1

        return results

    def _find_smallest_containing_loop(
        self,
        operation_location: SourceLocation,
        loop_regions: list[LoopRegionInfo],
        scope_location: SourceLocation,
    ) -> LoopRegionInfo | None:
        candidates = []

        index = 0
        while index < len(loop_regions):
            loop_region = loop_regions[index]

            if self._contains(scope_location, loop_region.source_location):
                if self._contains(loop_region.source_location, operation_location):
                    candidates.append(loop_region)

            index = index + 1

        if len(candidates) == 0:
            return None

        candidates.sort(key=self._loop_span_size)
        return candidates[0]

    def _loop_span_size(self, loop_region: LoopRegionInfo) -> int:
        return self._span_size(loop_region.source_location)

    def _sort_operations(self, operations: list) -> list:
        ordered = list(operations)
        ordered.sort(key=self._operation_sort_key)
        return ordered

    def _operation_sort_key(self, operation):
        return (
            operation.source_location.start_line,
            operation.source_location.start_column,
            operation.source_location.end_line,
            operation.source_location.end_column,
        )

    def _contains(
        self,
        outer: SourceLocation,
        inner: SourceLocation,
    ) -> bool:
        starts_after = False
        ends_before = False

        if inner.start_line > outer.start_line:
            starts_after = True
        elif inner.start_line == outer.start_line:
            if inner.start_column >= outer.start_column:
                starts_after = True

        if inner.end_line < outer.end_line:
            ends_before = True
        elif inner.end_line == outer.end_line:
            if inner.end_column <= outer.end_column:
                ends_before = True

        if starts_after and ends_before:
            return True

        return False

    def _span_size(self, location: SourceLocation) -> int:
        line_span = location.end_line - location.start_line
        column_span = location.end_column - location.start_column
        return line_span * 10000 + column_span