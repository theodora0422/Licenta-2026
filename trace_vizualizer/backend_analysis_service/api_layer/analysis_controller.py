import traceback

from fastapi import APIRouter,HTTPException,status

from trace_vizualizer.backend_analysis_service.analysis_orchestrator.analysis_coordinator import AnalysisCoordinator
from trace_vizualizer.backend_analysis_service.api_layer.request_validation.validator import validate_analysis_request, \
    RequestValidationException
from trace_vizualizer.domain.requests import AnalysisRequest
from trace_vizualizer.domain.responses import AnalysisResponse

router=APIRouter()
coordinator=AnalysisCoordinator()

@router.post("/analyze",response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest)->AnalysisResponse:
    try:
        validate_analysis_request(request)
        return coordinator.run_analysis(request)
    except RequestValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status":"error",
                "message":e.message,
                "details":e.details,
            }
        )
    except Exception as exc:
        print("=== INTERNAL ANALYSIS ERROR ===")
        traceback.print_exc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": "Internal server error during analysis.",
                "details": [str(exc)],
            }
        )