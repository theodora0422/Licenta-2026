from trace_vizualizer.backend_analysis_service.concurrency_extractor.concurrency_ir_builder import ConcurrencyIRBuilder
from trace_vizualizer.backend_analysis_service.concurrency_extractor.identifier_resolver import IdentifierResolver
from trace_vizualizer.backend_analysis_service.concurrency_extractor.loop_extractor import LoopExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.shared_access_extractor import \
    SharedAccessExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.synchronization_extractor import \
    SynchronizationExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.thread_binding_resolver import \
    ThreadBindingResolver
from trace_vizualizer.backend_analysis_service.concurrency_extractor.thread_class_extractor import ThreadClassExtractor
from trace_vizualizer.backend_analysis_service.concurrency_extractor.thread_extractor import ThreadExtractor
from trace_vizualizer.backend_analysis_service.explanation_engine.finding_narrator import FindingNarrator
from trace_vizualizer.backend_analysis_service.explanation_engine.source_linker import SourceLinker
from trace_vizualizer.backend_analysis_service.model_builder.event_builder import EventBuilder
from trace_vizualizer.backend_analysis_service.model_builder.initial_state_factory import InitialStateFactory
from trace_vizualizer.backend_analysis_service.model_builder.program_model_assembler import ProgramModelAssembler
from trace_vizualizer.backend_analysis_service.parsing_and_ast.ast_diagnostics import ASTDiagnostics
from trace_vizualizer.backend_analysis_service.parsing_and_ast.boolean_constant_resolver import BooleanConstantResolver
from trace_vizualizer.backend_analysis_service.parsing_and_ast.java_parser import JavaParser
from trace_vizualizer.backend_analysis_service.parsing_and_ast.method_index import MethodIndex
from trace_vizualizer.backend_analysis_service.property_checker.data_race import DataRaceChecker
from trace_vizualizer.backend_analysis_service.property_checker.deadlock import DeadlockChecker
from trace_vizualizer.backend_analysis_service.property_checker.finding_aggregator import FindingAggregator
from trace_vizualizer.backend_analysis_service.property_checker.mutual_exclusion import MutualExclusionChecker
from trace_vizualizer.backend_analysis_service.property_checker.starvation import StarvationChecker
from trace_vizualizer.backend_analysis_service.property_checker.verification_result_builder import \
    VerificationResultBuilder
from trace_vizualizer.backend_analysis_service.scenario_generator.state_explorer import StateExplorer
from trace_vizualizer.backend_analysis_service.visualization_builder.graph_builder import GraphBuilder
from trace_vizualizer.backend_analysis_service.visualization_builder.highlight_rules import HighlightRules
from trace_vizualizer.backend_analysis_service.visualization_builder.timeline_builder import TimelineBuilder
from trace_vizualizer.backend_analysis_service.visualization_builder.visualization_assembler import \
    VisualizationAssembler
from trace_vizualizer.domain.concurrency import ConcurrencyIR
from trace_vizualizer.domain.parsing import ParsingResult
from trace_vizualizer.domain.requests import AnalysisRequest
from trace_vizualizer.domain.responses import AnalysisResponse, Finding, ScenarioStep
from trace_vizualizer.domain.verification import VerificationResult, VerificationFinding


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
        self.mutual_exclusion_checker=MutualExclusionChecker()
        self.starvation_checker=StarvationChecker()
        self.finding_aggregator=FindingAggregator()
        self.verification_result_builder=VerificationResultBuilder()
        self.finding_narrator=FindingNarrator()
        self.source_linker=SourceLinker()
        self.timeline_builder=TimelineBuilder()
        self.graph_builder=GraphBuilder()
        self.highlight_rules=HighlightRules()
        self.visualization_assembler=VisualizationAssembler()
        self.thread_class_extractor=ThreadClassExtractor()
        self.thread_binding_resolver=ThreadBindingResolver()
        self.loop_extractor=LoopExtractor()
        self.loop_unroll_factor=3
        self.boolean_constant_resolver=BooleanConstantResolver()
        self.method_index=MethodIndex()
    def _get_checked_properties(self,request:AnalysisRequest):
        checked_properties=[]
        if request.check_deadlock:
            checked_properties.append("deadlock")
        if request.check_data_race:
            checked_properties.append("data_race")
        if request.check_mutual_exclusion:
            checked_properties.append("mutual_exclusion")
        if request.check_starvation:
            checked_properties.append("starvation")
        return checked_properties
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

    def _build_mutual_exclusion_location(self, counterexample) -> str | None:
        if counterexample is None or not counterexample.steps:
            return None

        lines = sorted({step.source_line for step in counterexample.steps if step.source_line is not None})
        if not lines:
            return None

        return "lines " + ", ".join(str(line) for line in lines)

    def _build_mutual_exclusion_explanation(self, verification_result) -> str:
        if not verification_result.mutual_exclusion_violated:
            return "No mutual exclusion violation was detected in the explored scenarios."

        if not verification_result.findings:
            return (
                "A mutual exclusion violation was found during bounded exploration. "
                "Conflicting accesses to the same critical resource were observed without common synchronization."
            )

        return (
            "A mutual exclusion violation was found during bounded exploration. "
            f"{verification_result.findings[0].message} "
            "The accesses were not protected by a common lock."
        )

    def _build_starvation_location(self, counterexample) -> str | None:
        if counterexample is None or not counterexample.steps:
            return None

        lines = sorted({step.source_line for step in counterexample.steps if step.source_line is not None})
        if not lines:
            return None

        return "lines " + ", ".join(str(line) for line in lines)

    def _build_starvation_explanation(self, verification_result) -> str:
        if not verification_result.starvation_detected:
            return "No starvation indicator was detected in the explored scenarios."

        if not verification_result.findings:
            return (
                "A potential starvation pattern was detected during bounded exploration. "
                "At least one thread remained unfinished while others continued to make progress."
            )

        return (
            "A potential starvation pattern was detected during bounded exploration. "
            f"{verification_result.findings[0].message} "
            "Because the analysis is bounded, this result should be interpreted as an indicator, "
            "not as a formal proof."
        )
    def _run_selected_verifiers(self,scenario_generation_result,checked_properties:list[str]):
        deadlock_verification_result=None
        data_race_verification_result=None
        mutual_exclusion_verification_result=None
        starvation_verification_result=None

        if "deadlock" in checked_properties:
            deadlock_verification_result=self.deadlock_checker.check(scenario_generation_result)
        if "data_race" in checked_properties:
            data_race_verification_result=self.data_race_checker.check(scenario_generation_result)
        if "mutual_exclusion" in checked_properties:
            mutual_exclusion_verification_result=self.mutual_exclusion_checker.check(scenario_generation_result)
        if "starvation" in checked_properties:
            starvation_verification_result=self.starvation_checker.check(scenario_generation_result)
        return deadlock_verification_result,data_race_verification_result,mutual_exclusion_verification_result,starvation_verification_result
    def _build_not_requested_result(self,property_name:str):
        return VerificationResult(
            deadlock_detected=False,
            data_race_detected=False,
            mutual_exclusion_violated=False,
            starvation_detected=False,
            findings=[
                VerificationFinding(
                    property_name=property_name,
                    violated=False,
                    message=f"{property_name} check was not requested",
                    scenario_id=None,
                )
            ],
            counterexample=None,
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

        boolean_constants=self.boolean_constant_resolver.resolve(tree,request.source_code)
        method_index=self.method_index.build(tree,request.source_code)

        print("=== BOOLEAN CONSTANTS ===")
        print(boolean_constants)
        print("=== METHOD INDEX ===")
        method_names=list(method_index.keys())
        method_names.sort()
        index=0
        while index<len(method_names):
            print(method_names[index])
            index+=1

        threads = self.thread_extractor.extract_threads(tree, request.source_code)
        thread_classes=self.thread_class_extractor.extract_thread_classes(tree,request.source_code)
        thread_instances,thread_start_bindings=self.thread_binding_resolver.resolve(tree,request.source_code,thread_classes)
        synchronization_operations = self.synchronization_extractor.extract_synchronization_operations(
            tree,
            request.source_code,
            boolean_constants, method_index
        )
        shared_access_operations = self.shared_access_extractor.extract_shared_access_operations(
            tree,
            request.source_code,
            boolean_constants,
            method_index
        )
        loop_regions=self.loop_extractor.extract_loops(tree)

        concurrency_ir = self.concurrency_ir_builder.build(
            threads=threads,
            thread_classes=thread_classes,
            thread_instances=thread_instances,
            thread_start_bindings=thread_start_bindings,
            loop_regions=loop_regions,
            synchronization_operations=synchronization_operations,
            shared_access_operations=shared_access_operations,
        )

        canonical_concurrency_ir = self.identifier_resolver.resolve(concurrency_ir)

        print("===CANONICAL THREAD BINDINGS===")
        index=0
        while index<len(canonical_concurrency_ir.thread_bindings):
            print(canonical_concurrency_ir.thread_bindings[index].model_dump())
            index=index+1

        thread_event_sequences = self.event_builder.build(canonical_concurrency_ir,loop_regions,self.loop_unroll_factor)
        initial_state = self.initial_state_factory.build(thread_event_sequences)
        program_model = self.program_model_assembler.build(
            thread_event_sequences=thread_event_sequences,
            initial_state=initial_state,
        )


        print("===EXTRACTED LOOP REGIONS===")
        index=0
        while index<len(loop_regions):
            print(loop_regions[index].model_dump())
            index=index+1

        scenario_generation_result = self.state_explorer.explore(
            program_model=program_model,
            max_depth=request.max_depth,
        )

        checked_properties=self._get_checked_properties(request)
        deadlock_verification_result,data_race_verification_result,mutual_exclusion_verification_result,starvation_verification_result=self._run_selected_verifiers(scenario_generation_result,checked_properties)
        if deadlock_verification_result is None:
            deadlock_verification_result=self._build_not_requested_result("deadlock")
        if data_race_verification_result is None:
            data_race_verification_result=self._build_not_requested_result("data_race")
        if mutual_exclusion_verification_result is None:
            mutual_exclusion_verification_result=self._build_not_requested_result("mutual_exclusion")
        if starvation_verification_result is None:
            starvation_verification_result=self._build_not_requested_result("starvation")

        aggregated_data = self.finding_aggregator.aggregate(
            deadlock_result=deadlock_verification_result,
            data_race_result=data_race_verification_result,
            mutual_exclusion_result=mutual_exclusion_verification_result,
            starvation_result=starvation_verification_result,
            checked_properties=checked_properties,
        )

        unified_verification_result = self.verification_result_builder.build(
            aggregated_data=aggregated_data,
            checked_properties=checked_properties,
        )

        narrated_explanation=self.finding_narrator.narrate(unified_verification_result)
        linked_explanation=self.source_linker.link(narrated_explanation,unified_verification_result,request.source_code)

        timeline_model=self.timeline_builder.build(unified_verification_result.selected_counterexample,unified_verification_result)
        graph_nodes,graph_edges=self.graph_builder.build(unified_verification_result.selected_counterexample,unified_verification_result)
        highlight_markers=self.highlight_rules.build(unified_verification_result,unified_verification_result.selected_counterexample)
        visualization_model=self.visualization_assembler.build(timeline=timeline_model,graph_nodes=graph_nodes,graph_edges=graph_edges,highlights=highlight_markers)

        print("=== DEADLOCK VERIFICATION RESULT ===")
        print(deadlock_verification_result.model_dump())

        print("=== DATA RACE VERIFICATION RESULT ===")
        print(data_race_verification_result.model_dump())

        print("=== MUTUAL EXCLUSION VERIFICATION RESULT ===")
        print(mutual_exclusion_verification_result.model_dump())

        print("=== STARVATION VERIFICATION RESULT ===")
        print(starvation_verification_result.model_dump())

        print("=== UNIFIED VERIFICATION RESULT ===")
        print(unified_verification_result.model_dump())

        print("=== STRUCTURED EXPLANATION ===")
        print(linked_explanation.model_dump())

        print("=== VISUALIZATION MODEL ===")
        print(visualization_model.model_dump())

        print("=== EXTRACTED THREAD CLASSES ===")
        index = 0
        while index < len(thread_classes):
            print(thread_classes[index].model_dump())
            index = index + 1

        print("=== EXTRACTED THREAD INSTANCES ===")
        index = 0
        while index < len(thread_instances):
            print(thread_instances[index].model_dump())
            index = index + 1

        print("=== EXTRACTED THREAD START BINDINGS ===")
        index = 0
        while index < len(thread_start_bindings):
            print(thread_start_bindings[index].model_dump())
            index = index + 1

        status = unified_verification_result.overall_status
        findings = []
        scenario = []
        explanation = "No property violation was detected in the explored scenarios."

        selected_property = unified_verification_result.selected_property
        counterexample = unified_verification_result.selected_counterexample

        if unified_verification_result.findings:
            selected_aggregated_finding = next(
                (
                    finding
                    for finding in unified_verification_result.findings
                    if finding.property_name == selected_property and finding.violated
                ),
                None,
            )

            if selected_aggregated_finding is not None:
                if selected_property == "deadlock":
                    findings = [
                        Finding(
                            type="deadlock",
                            message=selected_aggregated_finding.message,
                            location=self._build_deadlock_location(counterexample),
                        )
                    ]
                    scenario = self._build_deadlock_scenario_steps(counterexample)
                    explanation = self._build_deadlock_explanation(counterexample)

                elif selected_property == "data_race":
                    findings = [
                        Finding(
                            type="data_race",
                            message=selected_aggregated_finding.message,
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

                elif selected_property == "mutual_exclusion":
                    findings = [
                        Finding(
                            type="mutual_exclusion",
                            message=selected_aggregated_finding.message,
                            location=self._build_mutual_exclusion_location(counterexample),
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
                    explanation = self._build_mutual_exclusion_explanation(
                        mutual_exclusion_verification_result
                    )

                elif selected_property == "starvation":
                    findings = [
                        Finding(
                            type="starvation",
                            message=selected_aggregated_finding.message,
                            location=self._build_starvation_location(counterexample),
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
                    explanation = self._build_starvation_explanation(
                        starvation_verification_result
                    )
        return AnalysisResponse(
            status=status,
            findings=findings,
            scenario=scenario,
            explanation=explanation,
            parsing=parsing_result,
            structured_explanation=linked_explanation,
            visualization=visualization_model,
        )