from typing import List

from trace_vizualizer.domain.verification import VerificationResult
from trace_vizualizer.domain.verification_result import AggregatedFinding


class FindingAggregator:
    PRIORITY_ORDER=["deadlock","data_race","mutual_exclusion","starvation"]
    def aggregate(self,*,deadlock_result:VerificationResult,data_race_result:VerificationResult,mutual_exclusion_result:VerificationResult,starvation_result:VerificationResult,checked_properties:List[str]):
        result_by_property={
            "deadlock":deadlock_result,
            "data_race":data_race_result,
            "mutual_exclusion":mutual_exclusion_result,
            "starvation":starvation_result,
        }
        aggregated_findings:List[AggregatedFinding]=[]
        violated_properties:List[str]=[]
        selected_property=None
        selected_message=None
        selected_counterexample=None

        for property_name in checked_properties:
            verification_result=result_by_property[property_name]
            for finding in verification_result.findings:
                aggregated_findings.append(
                    AggregatedFinding(
                        property_name=finding.property_name,
                        violated=finding.violated,
                        message=finding.message,
                        scenario_id=finding.scenario_id,
                    )
                )
                if self._is_violated(property_name,verification_result):
                    violated_properties.append(property_name)
            for property_name in self.PRIORITY_ORDER:
                if property_name not in checked_properties:
                    continue
                verification_result=result_by_property[property_name]
                if self._is_violated(property_name,verification_result):
                    selected_property=property_name
                    selected_message=(
                        verification_result.findings[0].message if verification_result.findings else None
                    )
                    selected_counterexample=verification_result.counterexample
                    break
        return {
                "findings":aggregated_findings,
                "violated_properties":violated_properties,
                "selected_property":selected_property,
                "selected_message":selected_message,
                "selected_counterexample":selected_counterexample,
        }
    def _is_violated(self,property_name:str,verification_result:VerificationResult):
        if property_name=="deadlock":
            return verification_result.deadlock_detected
        if property_name=="data_race":
            return verification_result.data_race_detected
        if property_name=="mutual_exclusion":
            return verification_result.mutual_exclusion_violated
        if property_name=="starvation":
            return verification_result.starvation_detected
        return False