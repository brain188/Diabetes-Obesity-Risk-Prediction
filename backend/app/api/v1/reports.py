"""
Report generation endpoints.
Handles PDF report generation and download.
"""

from fastapi import APIRouter, Depends, status, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.report import ReportGenerateRequest, ReportResponse, ReportDownloadResponse
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.services.report_service import ReportService
from app.core.exceptions import NotFoundError, ReportGenerationError
from app.models.report import Report
from app.models.screening_data import ScreeningVisit
from app.models.patient import Patient

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=list,
    summary="List all reports",
    description="List all reports with patient and visit details.",
)
async def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> list:
    """List all generated reports with associated patient info."""
    offset = (page - 1) * page_size
    stmt = (
        select(Report, ScreeningVisit, Patient)
        .join(ScreeningVisit, Report.visit_id == ScreeningVisit.visit_id)
        .join(Patient, ScreeningVisit.patient_id == Patient.patient_id)
        .order_by(desc(Report.generated_at))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "report_id": r.report_id,
            "visit_id": r.visit_id,
            "format": r.format,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "download_count": r.download_count,
            "file_size_bytes": r.file_size_bytes,
            "patient_id": p.patient_id,
            "patient_name": p.full_name,
            "patient_sex": p.sex,
        }
        for r, v, p in rows
    ]


@router.post(
    "/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
    description="Generate a PDF report for a screening visit.",
)
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
    metadata: dict = Depends(get_request_metadata),
) -> ReportResponse:
    """
    Generate a report.
    
    - Creates PDF report
    - Includes patient info, screening data, predictions
    - Saves report metadata
    - Returns report details
    """
    service = ReportService(db)
    
    try:
        result = await service.generate_report(
            visit_id=request.visit_id,
            worker_id=current_user,
            format=request.format,
            ip_address=client_ip,
            request_id=metadata.get("request_id")
        )
        
        logger.info(f"Report generated: {result['report_id']}")
        return ReportResponse(**result)
        
    except NotFoundError as e:
        logger.warning(f"Report generation failed - visit not found: {request.visit_id}")
        raise
    except ReportGenerationError as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report metadata",
    description="Get report metadata without downloading file.",
)
async def get_report(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> ReportResponse:
    """
    Get report metadata.
    
    - Returns report information
    - Does not download the file
    """
    service = ReportService(db)
    
    try:
        result = await service.get_report(
            report_id=report_id,
            worker_id=current_user
        )
        return ReportResponse(**result)
        
    except NotFoundError as e:
        logger.warning(f"Report not found: {report_id}")
        raise


@router.get(
    "/{report_id}/download",
    summary="Download report",
    description="Download the actual report file.",
)
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> Response:
    """
    Download a report.

    - Returns the actual file via FileResponse
    - Increments download counter
    - Logs download for audit
    """
    from pathlib import Path as FilePath

    service = ReportService(db)

    # Look up report metadata
    report = await service.report_repo.get_report_with_details(report_id)
    if not report:
        raise NotFoundError("Report", report_id)

    file_path = FilePath(report.file_path)
    if not file_path.exists():
        raise ReportGenerationError(
            f"Report file is no longer available on the server. Please regenerate it.",
            detail={"report_id": report_id}
        )

    # Increment download count and log
    await service.report_repo.increment_download_count(report_id)
    await service.audit_repo.log_event(
        event_type="REPORT_DOWNLOADED",
        action="Report downloaded",
        worker_id=current_user,
        resource_type="Report",
        resource_id=report_id,
        ip_address=client_ip,
        status="SUCCESS"
    )

    content_type = "application/pdf" if report.format == "PDF" else "application/json"
    filename = f"patient_report_{report.visit_id}.{report.format.lower()}"

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=content_type,
    )


@router.get(
    "/patients/{patient_id}",
    response_model=PaginatedResponse[dict],
    summary="Get patient reports",
    description="Get all reports for a patient.",
)
async def get_patient_reports(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[dict]:
    """
    Get all reports for a patient.
    
    - Paginated results
    - Sorted by generation date
    - Returns report metadata
    """
    service = ReportService(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    reports, total = await service.get_patient_reports(
        patient_id=patient_id,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse.create(reports, total, pagination)


@router.delete(
    "/{report_id}",
    response_model=SuccessResponse,
    summary="Delete report",
    description="Delete a report file and its metadata.",
)
async def delete_report(
    report_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """
    Delete a report.
    
    - Removes file from disk
    - Deletes metadata from database
    - Requires authentication
    """
    service = ReportService(db)
    
    # Check if report exists
    report = await service.report_repo.get_by_id(report_id)
    if not report:
        raise NotFoundError("Report", report_id)
    
    # Delete report
    deleted = await service.report_repo.delete(report_id)
    
    if deleted:
        logger.info(f"Report deleted: {report_id} by worker {current_user}")
        return SuccessResponse(
            success=True,
            message="Report deleted successfully"
        )
    else:
        raise ReportGenerationError("Failed to delete report")