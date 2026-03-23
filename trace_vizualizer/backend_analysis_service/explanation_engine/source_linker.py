from trace_vizualizer.domain.explanation import ExplanationModel, SourceReference
from trace_vizualizer.domain.verification_result import UnifiedVerificationResult


class SourceLinker:
    def link(self,explanation:ExplanationModel,verification_result:UnifiedVerificationResult,source_code:str):
        counterexample=verification_result.selected_counterexample
        if counterexample is None:
            return explanation
        source_lines=source_code.splitlines()
        references:list[SourceReference]=[]
        seen=set()
        for step in counterexample.steps:
            line_number=step.source_line
            if line_number<1 or line_number>len(source_lines):
                snippet=None
            else:
                snippet=source_lines[line_number-1].strip()
            key=(line_number,step.thread_id,step.event_kind,step.original_resource)
            if key in seen:
                continue
            seen.add(key)

            references.append(
                SourceReference(
                    line=line_number,
                    code_snippet=snippet,
                    resource=step.original_resource,
                    thread=step.thread_id,
                    action=step.event_kind,
                )
            )
        return ExplanationModel(
            title=explanation.title,
            summary=explanation.summary,
            detailed_steps=explanation.detailed_steps,
            source_references=references,
        )