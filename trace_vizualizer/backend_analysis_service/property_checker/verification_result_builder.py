from trace_vizualizer.domain.verification_result import UnifiedVerificationResult


class VerificationResultBuilder:
    def build(self,*,aggregated_data:dict,checked_properties:list[str])->UnifiedVerificationResult:
        violated_properties=aggregated_data["violated_properties"]
        if violated_properties:
            overall_status="violation_found"
        else:
            overall_status="ok"

        return UnifiedVerificationResult(
            overall_status=overall_status,
            selected_property=aggregated_data["selected_property"],
            selected_message=aggregated_data["selected_message"],
            selected_counterexample=aggregated_data["selected_counterexample"],
            findings=aggregated_data["findings"],
            violated_properties=violated_properties,
            checked_properties=checked_properties,
        )