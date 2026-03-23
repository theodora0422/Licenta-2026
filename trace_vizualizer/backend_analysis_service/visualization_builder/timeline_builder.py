from trace_vizualizer.domain.scenario import ExecutionScenario
from trace_vizualizer.domain.visualization import TimelineItem


class TimelineBuilder:
    def build(self,counterexample:ExecutionScenario|None):
        if counterexample is None:
            return []
        timeline_items:list[TimelineItem]=[]
        for step in counterexample.steps:
            resource=step.original_resource
            label=(f"{step.thread_id} {step.event_kind}"+(f" {resource}" if resource else ""))
            timeline_items.append(
                TimelineItem(
                    step_index=step.step_index,
                    thread_id=step.thread_id,
                    action=step.event_kind,
                    resource=resource,
                    line=step.source_line,
                    label=label,
                )
            )
        return timeline_items