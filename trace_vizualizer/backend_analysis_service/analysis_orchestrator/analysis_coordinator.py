from trace_vizualizer.backend_analysis_service.concurrency_extractor.concurrency_ir_builder import ConcurrencyIRBuilder
from trace_vizualizer.backend_analysis_service.concurrency_extractor.shared_access_extractor import \
    SharedAccessExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.synchronization_extractor import \
    SynchronizationExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.thread_extractor import ThreadExtractor
from trace_vizualizer.backend_analysis_service.parsing_and_ast.ast_diagnostics import ASTDiagnostics
from trace_vizualizer.backend_analysis_service.parsing_and_ast.java_parser import JavaParser
from trace_vizualizer.domain.concurrency import ConcurrencyIR
from trace_vizualizer.domain.parsing import ParsingResult
from trace_vizualizer.domain.requests import AnalysisRequest
from trace_vizualizer.domain.responses import AnalysisResponse, Finding, ScenarioStep


class AnalysisCoordinator:
    def __init__(self):
        self.java_parser = JavaParser()
        self.ast_diagnostics = ASTDiagnostics()
        self.thread_extractor=ThreadExtractor()
        self.synchronization_extractor=SynchronizationExtractor()
        self.shared_access_extractor=SharedAccessExtractor()
        self.concurrency_ir_builder=ConcurrencyIRBuilder()

    def run_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        tree = self.java_parser.parse(request.source_code)
        diagnostics = self.ast_diagnostics.collect_diagnostics(tree, request.source_code)

        findings = []
        scenario = []
        explanation = "No concurrency violation detected in the mock analysis."
        status = "ok"

        parsing_result = ParsingResult(
            ast_root_type=tree.root_node.type,
            diagnostics=diagnostics,
            has_syntax_errors=len(diagnostics) > 0,
        )

        if diagnostics:
            status = "parse_error"
            findings = [
                Finding(
                    type="parse_error",
                    message=diagnostics[0].message,
                    location=(
                        f"line {diagnostics[0].line}, column {diagnostics[0].column}"
                        if diagnostics[0].line is not None and diagnostics[0].column is not None
                        else None
                    ),
                )
            ]
            scenario = []
            explanation = "Java code cannot be structurally analyzed because of a parsing error."

            return AnalysisResponse(
                status=status,
                findings=findings,
                scenario=scenario,
                explanation=explanation,
                parsing=parsing_result,
            )
        threads = self.thread_extractor.extract_threads(tree, request.source_code)
        synchronization_operations = self.synchronization_extractor.extract_synchronization_operations(
            tree,
            request.source_code,
        )
        shared_access_operations = self.shared_access_extractor.extract_shared_access_operations(
            tree,
            request.source_code,
        )

        concurrency_ir = self.concurrency_ir_builder.build(
            threads=threads,
            synchronization_operations=synchronization_operations,
            shared_access_operations=shared_access_operations,
        )

        print("=== EXTRACTED THREADS ===")
        for thread in threads:
            print(thread.model_dump())

        print("=== EXTRACTED SYNCHRONIZATION OPERATIONS ===")
        for operation in synchronization_operations:
            print(operation.model_dump())

        print("=== EXTRACTED SHARED ACCESS OPERATIONS ===")
        for operation in shared_access_operations:
            print(operation.model_dump())

        print("=== CONCURRENCY IR ===")
        print(concurrency_ir.model_dump())

        if request.check_deadlock:
            status = "violation_found"
            findings = [
                Finding(
                    type="deadlock",
                    message="Potential deadlock detected between Thread-1 and Thread-2.",
                    location="Example.java:23"
                )
            ]
            scenario = [
                ScenarioStep(thread="Thread-1", action="acquire", resource="lockA"),
                ScenarioStep(thread="Thread-2", action="acquire", resource="lockB"),
                ScenarioStep(thread="Thread-1", action="wait", resource="lockB"),
                ScenarioStep(thread="Thread-2", action="wait", resource="lockA"),
            ]
            explanation = (
                "Two threads acquire different locks and then wait for each other, "
                "which may lead to a circular wait condition."
            )

        return AnalysisResponse(
            status=status,
            findings=findings,
            scenario=scenario,
            explanation=explanation,
            parsing=parsing_result,
        )