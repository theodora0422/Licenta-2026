from trace_vizualizer.backend_analysis_service.concurrency_extractor.concurrency_ir_builder import ConcurrencyIRBuilder
from trace_vizualizer.backend_analysis_service.concurrency_extractor.identifier_resolver import IdentifierResolver
from trace_vizualizer.backend_analysis_service.concurrency_extractor.shared_access_extractor import \
    SharedAccessExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.synchronization_extractor import \
    SynchronizationExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.thread_extractor import ThreadExtractor
from trace_vizualizer.backend_analysis_service.model_builder.event_builder import EventBuilder
from trace_vizualizer.backend_analysis_service.model_builder.initial_state_factory import InitialStateFactory
from trace_vizualizer.backend_analysis_service.model_builder.program_model_assembler import ProgramModelAssembler
from trace_vizualizer.backend_analysis_service.parsing_and_ast.ast_diagnostics import ASTDiagnostics
from trace_vizualizer.backend_analysis_service.parsing_and_ast.java_parser import JavaParser
from trace_vizualizer.backend_analysis_service.property_checker.data_race import DataRaceChecker
from trace_vizualizer.backend_analysis_service.property_checker.deadlock import DeadlockChecker
from trace_vizualizer.backend_analysis_service.scenario_generator.state_explorer import StateExplorer
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
        self.identifier_resolver=IdentifierResolver()
        self.event_builder=EventBuilder()
        self.initial_state_factory=InitialStateFactory()
        self.program_model_assembler=ProgramModelAssembler()
        self.state_explorer=StateExplorer()
        self.deadlock_checker=DeadlockChecker()
        self.data_race_checker=DataRaceChecker()

    def _build_deadlock_location(self, counterexample) -> str | None:
        if counterexample is None or not counterexample.steps:
            return None

        lines = sorted({step.source_line for step in counterexample.steps if step.source_line is not None})

        if not lines:
            return None

        return "lines " + ", ".join(str(line) for line in lines)

    def _build_deadlock_scenario_steps(self, counterexample) -> list[ScenarioStep]:
        if counterexample is None:
            return []

        scenario_steps = [
            ScenarioStep(
                thread=step.thread_id,
                action=step.event_kind,
                resource=step.original_resource,
            )
            for step in counterexample.steps
        ]

        final_state = counterexample.final_state

        waiting_pairs = [
            (thread_id, waited_lock)
            for thread_id, waited_lock in final_state.waiting_for.items()
            if waited_lock is not None
        ]

        for thread_id, waited_lock in waiting_pairs:
            scenario_steps.append(
                ScenarioStep(
                    thread=thread_id,
                    action="wait",
                    resource=waited_lock,
                )
            )

        return scenario_steps

    def _build_deadlock_explanation(self, counterexample) -> str:
        if counterexample is None:
            return (
                "A potential deadlock state was found during bounded exploration. "
                "The execution reached a state with no enabled transitions while "
                "at least one thread was waiting for a lock."
            )

        final_state = counterexample.final_state

        waiting_descriptions = []
        for thread_id, waited_lock in final_state.waiting_for.items():
            if waited_lock is None:
                continue

            owner = final_state.lock_owners.get(waited_lock)
            if owner is not None:
                waiting_descriptions.append(
                    f"{thread_id} waits for {waited_lock}, currently held by {owner}"
                )
            else:
                waiting_descriptions.append(
                    f"{thread_id} waits for {waited_lock}"
                )

        if waiting_descriptions:
            waiting_text = "; ".join(waiting_descriptions)
            return (
                "A potential deadlock state was found during bounded exploration. "
                "The execution reached a state with no enabled transitions. "
                f"In the final state, {waiting_text}."
            )

        return (
            "A potential deadlock state was found during bounded exploration. "
            "The execution reached a state with no enabled transitions while "
            "threads remained blocked."
        )

    def _build_data_race_location(self, counterexample) -> str | None:
        if counterexample is None or not counterexample.steps:
            return None

        lines = sorted({step.source_line for step in counterexample.steps if step.source_line is not None})
        if not lines:
            return None

        return "lines " + ", ".join(str(line) for line in lines)

    def _build_data_race_explanation(self, verification_result) -> str:
        if not verification_result.data_race_detected:
            return "No data race was detected in the explored scenarios."

        if not verification_result.findings:
            return (
                "A potential data race was found during bounded exploration. "
                "Conflicting accesses to the same resource were observed without a common protecting lock."
            )

        return (
            "A potential data race was found during bounded exploration. "
            f"{verification_result.findings[0].message} "
            "The conflicting accesses were not protected by a common lock."
        )
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

        canonical_concurrency_ir = self.identifier_resolver.resolve(concurrency_ir)

        thread_event_sequences = self.event_builder.build(canonical_concurrency_ir)
        initial_state = self.initial_state_factory.build(thread_event_sequences)
        program_model = self.program_model_assembler.build(
            thread_event_sequences=thread_event_sequences,
            initial_state=initial_state,
        )

        scenario_generation_result = self.state_explorer.explore(
            program_model=program_model,
            max_depth=request.max_depth,
        )

        deadlock_verification_result=self.deadlock_checker.check(scenario_generation_result)
        data_race_verification_result = self.data_race_checker.check(scenario_generation_result)

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

        print("=== CANONICAL CONCURRENCY IR ===")
        print(canonical_concurrency_ir.model_dump())

        print("=== THREAD EVENT SEQUENCES ===")
        for sequence in thread_event_sequences:
            print(sequence.model_dump())

        print("=== INITIAL STATE ===")
        print(initial_state.model_dump())

        print("=== PROGRAM MODEL ===")
        print(program_model.model_dump())

        print("=== SCENARIO GENERATION RESULT ===")
        print(scenario_generation_result.model_dump())

        print("=== DEADLOCK VERIFICATION RESULT ===")
        print(deadlock_verification_result.model_dump())
        print("=== DATA RACE VERIFICATION RESULT ===")
        print(data_race_verification_result.model_dump())

        if request.check_deadlock:
            if deadlock_verification_result.deadlock_detected:
                status = "violation_found"

                counterexample = deadlock_verification_result.counterexample

                findings = [
                    Finding(
                        type="deadlock",
                        message=deadlock_verification_result.findings[0].message,
                        location=self._build_deadlock_location(counterexample),
                    )
                ]

                scenario = self._build_deadlock_scenario_steps(counterexample)
                explanation = self._build_deadlock_explanation(counterexample)

            else:
                status = "ok"
                findings = []
                scenario = []
                explanation = "No deadlock was detected in the explored scenarios."
        if request.check_data_race:
            if data_race_verification_result.data_race_detected:
                status = "violation_found"

                counterexample = data_race_verification_result.counterexample

                findings = [
                    Finding(
                        type="data_race",
                        message=data_race_verification_result.findings[0].message,
                        location=self._build_data_race_location(counterexample),
                    )
                ]

                scenario = [
                    ScenarioStep(
                        thread=step.thread_id,
                        action=step.event_kind,
                        resource=step.original_resource,
                    )
                    for step in counterexample.steps
                ] if counterexample is not None else []

                explanation = self._build_data_race_explanation(data_race_verification_result)
            else:
                status = "ok"
                findings = []
                scenario = []
                explanation = "No data race was detected in the explored scenarios."

        return AnalysisResponse(
            status=status,
            findings=findings,
            scenario=scenario,
            explanation=explanation,
            parsing=parsing_result,
        )