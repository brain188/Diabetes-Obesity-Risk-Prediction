"""
Report generation business logic.
Handles PDF report generation, storage, and retrieval.
"""

import logging
import os
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from app.core.config import settings
from app.core.exceptions import ReportGenerationError, NotFoundError
from app.repositories.report_repository import ReportRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.prediction_service import PredictionService
from app.utils.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)


class ReportService:
    """Service for report generation business logic."""
    
    def __init__(self, session, model_loader=None):
        """
        Initialize report service with database session.
        
        Args:
            session: SQLAlchemy async session
            model_loader: Optional model loader for predictions
        """
        self.session = session
        self.report_repo = ReportRepository(session)
        self.screening_repo = ScreeningRepository(session)
        self.prediction_repo = PredictionRepository(session)
        self.patient_repo = PatientRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.model_loader = model_loader
        self.pdf_generator = PDFGenerator()
    
    async def generate_report(
        self,
        visit_id: str,
        worker_id: str,
        format: str = "PDF",
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a report for a screening visit.
        
        Args:
            visit_id: Screening visit identifier
            worker_id: Healthcare worker generating report
            format: Report format (PDF/JSON)
            ip_address: Client IP for audit
            request_id: Request ID for tracing
            
        Returns:
            Report metadata dictionary
            
        Raises:
            NotFoundError: If visit not found
            ReportGenerationError: If report generation fails
        """
        try:
            # Get visit with all related data
            visit = await self.screening_repo.get_visit_with_data_or_fail(
                visit_id, 
                include_patient=True
            )
            
            if not visit.screening_data:
                raise NotFoundError("ScreeningData", visit_id)
            
            # Get prediction if exists
            prediction = await self.prediction_repo.get_prediction_by_visit(
                visit_id, 
                include_details=True
            )
            
            # Get patient info
            patient = visit.patient
            
            # Prepare report data
            report_data = await self._prepare_report_data(
                visit=visit,
                patient=patient,
                screening_data=visit.screening_data,
                prediction=prediction
            )
            
            # Generate report file
            if format.upper() == "PDF":
                file_path, file_size, checksum = await self._generate_pdf_report(
                    report_data=report_data,
                    visit_id=visit_id,
                    patient_name=patient.full_name
                )
            else:
                file_path, file_size, checksum = await self._generate_json_report(
                    report_data=report_data,
                    visit_id=visit_id
                )
            
            # Save (idempotent) report record to database
            # Report.visit_id is unique, so repeated calls for the same visit_id should reuse/update the existing record.
            existing_report = await self.report_repo.get_report_by_visit(visit_id)
            if existing_report:
                report = await self.report_repo.update(
                    id=existing_report.report_id,
                    id_column="report_id",
                    format=format.upper(),
                    file_path=str(file_path),
                    generated_by=worker_id,
                    file_size_bytes=str(file_size),
                    checksum=checksum,
                    generated_at=datetime.now(timezone.utc),
                    download_count="0",
                )
            else:
                report = await self.report_repo.create_report(
                    visit_id=visit_id,
                    format=format.upper(),
                    file_path=str(file_path),
                    generated_by=worker_id,
                    file_size_bytes=str(file_size),
                    checksum=checksum
                )
            
            # Log report generation
            await self.audit_repo.log_report_generated(
                worker_id=worker_id,
                patient_id=patient.patient_id,
                report_id=report.report_id,
                ip_address=ip_address,
                request_id=request_id
            )
            
            logger.info(f"Report generated: {report.report_id} for visit {visit_id}")
            
            return {
                "report_id": report.report_id,
                "visit_id": visit_id,
                "patient_id": patient.patient_id,
                "patient_name": patient.full_name,
                "format": report.format,
                "file_path": report.file_path,
                "file_size_bytes": report.file_size_bytes,
                "generated_at": report.generated_at,
                "download_count": int(report.download_count) if report.download_count else 0
            }
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")
    
    async def _prepare_report_data(
    self,
    visit,
    patient,
    screening_data,
    prediction
) -> Dict[str, Any]:
        """
        Prepare data for report generation.
        
        Args:
            visit: ScreeningVisit instance
            patient: Patient instance
            screening_data: ScreeningData instance
            prediction: Prediction instance (may be None)
            
        Returns:
            Dictionary with report data
        """
        age = patient.age
        
        # Get SHAP explanation, LIME explanation, and recommendation
        shap_explanation = None
        lime_explanation = None
        recommendation = None
        global_importance = None
        
        if prediction:
            # Get all explanations
            if prediction.shap_explanation:
                if prediction.shap_explanation.method == "SHAP":
                    shap_explanation = prediction.shap_explanation
                elif prediction.shap_explanation.method == "LIME":
                    lime_explanation = prediction.shap_explanation
            
            # Get recommendation
            recommendation = await self.prediction_repo.recommendation_repo.get_by_id(
                prediction.prediction_id,
                id_column="prediction_id"
            ) if prediction.prediction_id else None
        
        # Get global feature importance
        try:
            # Use the cached global feature importance from model_loader
            if self.model_loader:
                importance_list, method = self.model_loader.get_feature_importance_cached()
                global_importance = {
                    "feature_importance": {
                        item["feature"]: item["importance"]
                        for item in importance_list
                    },
                    "method": method,
                    "model_version": self.model_loader.model_version,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            logger.warning(f"Failed to get global feature importance: {str(e)}")
        
        # Prepare report data
        report_data = {
            "report_id": str(hash(visit.visit_id + str(datetime.now(timezone.utc))))[:8],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_version": prediction.model_version if prediction else settings.MODEL_VERSION,
            "patient": {
                "patient_id": patient.patient_id,
                "full_name": patient.full_name,
                "date_of_birth": patient.date_of_birth.isoformat(),
                "age": age,
                "sex": patient.sex,
                "contact_info": patient.contact_info
            },
            "screening": {
                "visit_date": visit.visit_date.isoformat(),
                "weight_kg": screening_data.weight,
                "height_m": screening_data.height,
                "bmi": screening_data.bmi,
                "bmi_category": screening_data.bmi_category,
                "physical_activity": screening_data.physical_activity,  # Boolean
                "family_history_diabetes": screening_data.family_history_diabetes,
                "previous_gdm": screening_data.previous_gdm,
                "has_hypertension": screening_data.has_hypertension,
                "is_pregnant": screening_data.is_pregnant,
                "residence": screening_data.residence,
                "notes": visit.notes
            }
        }
        
        # Add prediction results if available
        if prediction:
            report_data["predictions"] = {
                "diabetes": {
                    "probability": prediction.diabetes_probability,
                    "risk_class": prediction.diabetes_risk_class,
                    "class_label": prediction.diabetes_class
                },
                "obesity": {
                    "bmi": screening_data.bmi,
                    "bmi_category": screening_data.bmi_category,
                    "risk_class": prediction.obesity_risk_class,
                    "class_label": prediction.obesity_class
                }
            }
        
        # Add SHAP explanation if available
        if shap_explanation and shap_explanation.feature_contributions:
            report_data["explanation"] = {
                "base_value": shap_explanation.base_value,
                "feature_contributions": shap_explanation.feature_contributions,
                "top_positive_features": shap_explanation.top_positive_features,
                "top_negative_features": shap_explanation.top_negative_features
            }
        
        # Add LIME explanation if available
        if lime_explanation and lime_explanation.feature_contributions:
            report_data["lime_explanation"] = {
                "feature_contributions": lime_explanation.feature_contributions,
                "top_positive_features": lime_explanation.top_positive_features,
                "top_negative_features": lime_explanation.top_negative_features
            }
        
        # Add global feature importance
        if global_importance:
            report_data["global_feature_importance"] = global_importance
        
        # Add recommendations if available
        if recommendation:
            report_data["recommendations"] = {
                "priority": recommendation.priority,
                "action_text": recommendation.action_text,
                "patient_advice": recommendation.patient_advice,
                "follow_up_interval_days": recommendation.follow_up_interval_days,
                "referral_required": recommendation.referral_required,
                "diabetes_guidance": recommendation.diabetes_guidance,
                "obesity_guidance": recommendation.obesity_guidance
            }
        
        return report_data
    
    async def _generate_pdf_report(
        self,
        report_data: Dict[str, Any],
        visit_id: str,
        patient_name: str
    ) -> Tuple[Path, int, str]:
        """
        Generate PDF report file.
        
        Args:
            report_data: Report data dictionary
            visit_id: Visit identifier
            patient_name: Patient name for filename
            
        Returns:
            Tuple of (file_path, file_size_bytes, checksum)
            
        Raises:
            ReportGenerationError: If PDF generation fails
        """
        try:
            # Create reports directory if it doesn't exist
            reports_dir = Path(settings.REPORTS_DIR)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Create date-based subdirectory
            date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            date_dir = reports_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            safe_name = "".join(c for c in patient_name if c.isalnum() or c in " ._-")[:50]
            filename = f"report_{visit_id}_{safe_name}.pdf"
            file_path = date_dir / filename
            
            # Generate PDF
            pdf_bytes = await self.pdf_generator.generate_report_pdf(report_data)
            
            # Write to file
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)
            
            # Calculate file size and checksum
            file_size = file_path.stat().st_size
            checksum = hashlib.sha256(pdf_bytes).hexdigest()
            
            logger.info(f"PDF report generated: {file_path} ({file_size} bytes)")
            
            return file_path, file_size, checksum
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise ReportGenerationError(f"Failed to generate PDF report: {str(e)}")
    
    async def _generate_json_report(
        self,
        report_data: Dict[str, Any],
        visit_id: str
    ) -> Tuple[Path, int, str]:
        """
        Generate JSON report file.
        
        Args:
            report_data: Report data dictionary
            visit_id: Visit identifier
            
        Returns:
            Tuple of (file_path, file_size_bytes, checksum)
            
        Raises:
            ReportGenerationError: If JSON generation fails
        """
        try:
            # Create reports directory
            reports_dir = Path(settings.REPORTS_DIR)
            reports_dir.mkdir(parents=True, exist_ok=True)
            
            # Create date-based subdirectory
            date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
            date_dir = reports_dir / date_str
            date_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"report_{visit_id}.json"
            file_path = date_dir / filename
            
            # Generate JSON
            json_bytes = json.dumps(report_data, indent=2, default=str).encode('utf-8')
            
            # Write to file
            with open(file_path, "wb") as f:
                f.write(json_bytes)
            
            # Calculate file size and checksum
            file_size = file_path.stat().st_size
            checksum = hashlib.sha256(json_bytes).hexdigest()
            
            logger.info(f"JSON report generated: {file_path} ({file_size} bytes)")
            
            return file_path, file_size, checksum
            
        except Exception as e:
            logger.error(f"JSON generation failed: {str(e)}")
            raise ReportGenerationError(f"Failed to generate JSON report: {str(e)}")
    
    async def get_report(
        self,
        report_id: str,
        worker_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get report metadata.
        
        Args:
            report_id: Report identifier
            worker_id: Optional worker ID for access logging
            
        Returns:
            Report metadata dictionary
            
        Raises:
            NotFoundError: If report not found
        """
        report = await self.report_repo.get_report_with_details(report_id)
        
        if not report:
            raise NotFoundError("Report", report_id)
        
        # Log access
        if worker_id:
            await self.audit_repo.log_event(
                event_type="REPORT_VIEWED",
                action=f"Report viewed",
                worker_id=worker_id,
                resource_type="Report",
                resource_id=report_id,
                status="SUCCESS"
            )
        
        return {
            "report_id": report.report_id,
            "visit_id": report.visit_id,
            "patient_id": report.visit.patient_id if report.visit else None,
            "patient_name": report.visit.patient.full_name if report.visit and report.visit.patient else None,
            "format": report.format,
            "file_path": report.file_path,
            "file_size_bytes": report.file_size_bytes,
            "generated_at": report.generated_at.isoformat() if report.generated_at else None,
            "download_count": int(report.download_count) if report.download_count else 0
        }
    
    async def download_report(
        self,
        report_id: str,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download a report file.
        
        Args:
            report_id: Report identifier
            worker_id: Healthcare worker downloading
            ip_address: Client IP for audit
            
        Returns:
            Download information dictionary
            
        Raises:
            NotFoundError: If report not found
        """
        report = await self.report_repo.get_report_with_details(report_id)
        
        if not report:
            raise NotFoundError("Report", report_id)
        
        # Check if file exists
        file_path = Path(report.file_path)
        if not file_path.exists():
            raise ReportGenerationError(f"Report file not found: {report.file_path}")
        
        # Increment download count
        await self.report_repo.increment_download_count(report_id)
        
        # Log download
        await self.audit_repo.log_event(
            event_type="REPORT_DOWNLOADED",
            action=f"Report downloaded",
            worker_id=worker_id,
            resource_type="Report",
            resource_id=report_id,
            ip_address=ip_address,
            status="SUCCESS"
        )
        
        logger.info(f"Report downloaded: {report_id} by worker {worker_id}")
        
        # Read file
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Determine content type
        content_type = "application/pdf" if report.format == "PDF" else "application/json"
        
        # Generate filename for download
        filename = f"patient_report_{report.visit_id}.{report.format.lower()}"
        
        return {
            "content": file_content,
            "content_type": content_type,
            "filename": filename,
            "file_size": len(file_content)
        }
    
    async def get_patient_reports(
        self,
        patient_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get all reports for a patient.
        
        Args:
            patient_id: Patient identifier
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (reports list, total count)
        """
        offset = (page - 1) * page_size
        
        reports, total = await self.report_repo.get_patient_reports(
            patient_id=patient_id,
            skip=offset,
            limit=page_size
        )
        
        report_responses = []
        for report in reports:
            report_responses.append({
                "report_id": report.report_id,
                "visit_id": report.visit_id,
                "format": report.format,
                "generated_at": report.generated_at.isoformat() if report.generated_at else None,
                "download_count": int(report.download_count) if report.download_count else 0
            })
        
        return report_responses, total