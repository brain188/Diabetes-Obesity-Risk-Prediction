"""
Initial schema creation for Intelligent DSS.

Revision ID: 2026_06_17_0001
Revises: 
Create Date: 2026-06-17 00:00:00.000000

This migration creates all initial tables for the Intelligent DSS application:
- healthcare_workers
- patients
- screening_visits
- screening_data
- predictions
- recommendations
- shap_explanations
- audit_logs
- clinical_notes
- reports
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2024_01_01_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create all initial tables for the Intelligent DSS application.
    """
    
    # ──────────────────────────────────────────────────────────────────────────
    # 1. healthcare_workers table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'healthcare_workers',
        sa.Column('worker_id', sa.String(36), nullable=False, comment='Unique identifier for the healthcare worker'),
        sa.Column('full_name', sa.String(255), nullable=False, comment='Full name of the healthcare worker'),
        sa.Column('email', sa.String(255), nullable=False, comment='Email address (used for login)'),
        sa.Column('password_hash', sa.String(255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('clinic_name', sa.String(255), nullable=True, comment='Name of the healthcare facility'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether the account is active'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false', comment='Whether email has been verified'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of last successful login'),
        sa.Column('password_reset_token', sa.String(255), nullable=True, comment='Token for password reset (temporary)'),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True, comment='Expiration time for password reset token'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.PrimaryKeyConstraint('worker_id'),
        sa.UniqueConstraint('email'),
    )
    
    # Create indexes for healthcare_workers
    op.create_index('idx_hw_email_active', 'healthcare_workers', ['email', 'is_active'])
    op.create_index('idx_hw_created_at', 'healthcare_workers', ['created_at'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 2. patients table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'patients',
        sa.Column('patient_id', sa.String(36), nullable=False, comment='Unique identifier for the patient'),
        sa.Column('worker_id', sa.String(36), nullable=False, comment='Healthcare worker who registered this patient'),
        sa.Column('full_name', sa.String(200), nullable=False, comment="Patient's full name"),
        sa.Column('date_of_birth', sa.Date(), nullable=False, comment="Patient's date of birth"),
        sa.Column('sex', sa.String(10), nullable=False, comment="Patient's biological sex: Male | Female"),
        sa.Column('contact_info', sa.String(200), nullable=True, comment='Optional phone number or contact detail'),
        sa.Column('national_id', sa.String(50), nullable=True, comment='National ID or medical record number (optional)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['worker_id'], ['healthcare_workers.worker_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('patient_id'),
        sa.UniqueConstraint('national_id'),
    )
    
    # Create indexes for patients
    op.create_index('idx_patient_name_search', 'patients', ['full_name'])
    op.create_index('idx_patient_dob', 'patients', ['date_of_birth'])
    op.create_index('idx_patient_registered_by', 'patients', ['worker_id'])
    op.create_index('idx_patient_sex', 'patients', ['sex'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 3. screening_visits table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'screening_visits',
        sa.Column('visit_id', sa.String(36), nullable=False, comment='Unique identifier for the screening visit'),
        sa.Column('patient_id', sa.String(36), nullable=False, comment='Patient associated with this visit'),
        sa.Column('visit_date', sa.DateTime(timezone=True), nullable=False, comment='Date and time of the screening visit'),
        sa.Column('notes', sa.String(1000), nullable=True, comment='Optional notes about the screening visit'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('visit_id'),
    )
    
    # Create indexes for screening_visits
    op.create_index('idx_visit_patient_date', 'screening_visits', ['patient_id', 'visit_date'])
    op.create_index('idx_visit_date', 'screening_visits', ['visit_date'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 4. screening_data table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'screening_data',
        sa.Column('visit_id', sa.String(36), nullable=False, comment='Foreign key to screening visit'),
        sa.Column('weight', sa.Float(), nullable=False, comment='Weight in kilograms (kg)'),
        sa.Column('height', sa.Float(), nullable=False, comment='Height in meters (m)'),
        sa.Column('bmi', sa.Float(), nullable=False, comment='Body Mass Index (calculated from weight/height²)'),
        sa.Column('bmi_category', sa.String(20), nullable=False, comment='BMI category (Normal/Overweight/Obese I/Obese II+)'),
        sa.Column('glucose_level', sa.Float(), nullable=True, comment='Blood glucose level (mg/dL) - optional'),
        sa.Column('blood_pressure', sa.String(20), nullable=True, comment="Blood pressure reading (e.g., '120/80') - optional"),
        sa.Column('physical_activity', sa.Boolean(), nullable=False, server_default='false', comment='Whether patient is physically active'),
        sa.Column('diet_score', sa.Integer(), nullable=True, comment='Diet quality score (0-10) - optional'),
        sa.Column('family_history_diabetes', sa.Boolean(), nullable=False, server_default='false', comment='Whether patient has family history of diabetes'),
        sa.Column('previous_gdm', sa.Boolean(), nullable=False, server_default='false', comment='Whether patient had Gestational Diabetes Mellitus'),
        sa.Column('has_hypertension', sa.Boolean(), nullable=False, server_default='false', comment='Whether patient has hypertension'),
        sa.Column('is_pregnant', sa.Boolean(), nullable=False, server_default='false', comment='Whether the patient is currently pregnant'),
        sa.Column('residence', sa.String(20), nullable=False, server_default='Rural', comment='Residence type (Urban/Rural)'),
        sa.Column('age', sa.Integer(), nullable=False, comment="Patient's age at time of screening"),
        sa.Column('model_version_used', sa.String(50), nullable=True, comment='Version of the model used for preprocessing/prediction'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['visit_id'], ['screening_visits.visit_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('visit_id'),
        sa.CheckConstraint('weight >= 20 AND weight <= 300', name='ck_weight_range'),
        sa.CheckConstraint('height >= 1.0 AND height <= 2.5', name='ck_height_range'),
        sa.CheckConstraint('bmi >= 10 AND bmi <= 70', name='ck_bmi_range'),
        sa.CheckConstraint('age >= 18 AND age <= 100', name='ck_age_range'),
    )
    
    # Create index for screening_data
    op.create_index('idx_screening_visit', 'screening_data', ['visit_id'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 5. predictions table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'predictions',
        sa.Column('prediction_id', sa.String(36), nullable=False, comment='Unique identifier for the prediction'),
        sa.Column('visit_id', sa.String(36), nullable=False, comment='Foreign key to screening visit'),
        sa.Column('diabetes_probability', sa.Float(), nullable=False, comment='Probability of diabetes (0.0 to 1.0)'),
        sa.Column('diabetes_risk_class', sa.String(20), nullable=False, comment='Risk class: Low/Moderate/High'),
        sa.Column('diabetes_class', sa.String(20), nullable=True, comment='Detailed class: Normal/Prediabetes/Diabetic'),
        sa.Column('obesity_probability', sa.Float(), nullable=True, comment='Probability of obesity (0.0 to 1.0)'),
        sa.Column('obesity_risk_class', sa.String(20), nullable=False, comment='Risk class: Low/Moderate/High'),
        sa.Column('obesity_class', sa.String(20), nullable=True, comment='Obesity class: Normal/Overweight/Obese'),
        sa.Column('model_version', sa.String(50), nullable=False, comment='Version of the model used for prediction'),
        sa.Column('prediction_date', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when prediction was made'),
        sa.Column('latency_ms', sa.Float(), nullable=True, comment='Prediction latency in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['visit_id'], ['screening_visits.visit_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('prediction_id'),
        sa.UniqueConstraint('visit_id'),
    )
    
    # Create indexes for predictions
    op.create_index('idx_prediction_visit', 'predictions', ['visit_id'])
    op.create_index('idx_prediction_date', 'predictions', ['prediction_date'])
    op.create_index('idx_prediction_model', 'predictions', ['model_version'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 6. recommendations table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'recommendations',
        sa.Column('recommendation_id', sa.String(36), nullable=False, comment='Unique identifier for the recommendation'),
        sa.Column('prediction_id', sa.String(36), nullable=False, comment='Foreign key to prediction'),
        sa.Column('priority', sa.String(20), nullable=False, comment='Priority level: Urgent/High/Medium/Low'),
        sa.Column('action_text', sa.Text(), nullable=False, comment='Detailed recommendation text for healthcare worker'),
        sa.Column('patient_advice', sa.Text(), nullable=True, comment='Patient-friendly advice text'),
        sa.Column('follow_up_interval_days', sa.Integer(), nullable=True, comment='Recommended days until follow-up'),
        sa.Column('referral_required', sa.String(100), nullable=True, comment='Specialist referral required'),
        sa.Column('diabetes_guidance', sa.Text(), nullable=True, comment='Diabetes-specific recommendations'),
        sa.Column('obesity_guidance', sa.Text(), nullable=True, comment='Obesity-specific recommendations'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.prediction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('recommendation_id'),
        sa.UniqueConstraint('prediction_id'),
    )
    
    # Create indexes for recommendations
    op.create_index('idx_recommendation_prediction', 'recommendations', ['prediction_id'])
    op.create_index('idx_recommendation_priority', 'recommendations', ['priority'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 7. shap_explanations table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'shap_explanations',
        sa.Column('explanation_id', sa.String(36), nullable=False, comment='Unique identifier for the SHAP explanation'),
        sa.Column('prediction_id', sa.String(36), nullable=False, comment='Foreign key to prediction'),
        sa.Column('base_value', sa.Float(), nullable=False, comment='Base value (expected model output)'),
        sa.Column('feature_contributions', postgresql.JSON(astext_type=sa.Text()), nullable=False, comment='Dictionary mapping feature names to SHAP values'),
        sa.Column('top_positive_features', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Top 5 features that increased risk'),
        sa.Column('top_negative_features', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Top 5 features that decreased risk'),
        sa.Column('method', sa.String(50), nullable=False, server_default='SHAP', comment='Explanation method used (SHAP/LIME)'),
        sa.Column('force_plot_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Force plot data for visualization'),
        sa.Column('waterfall_data', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='Waterfall plot data for visualization'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['prediction_id'], ['predictions.prediction_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('explanation_id'),
        sa.UniqueConstraint('prediction_id'),
    )
    
    # Create index for shap_explanations
    op.create_index('idx_shap_prediction', 'shap_explanations', ['prediction_id'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 8. audit_logs table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(36), nullable=False, comment='Unique identifier for the audit log entry'),
        sa.Column('worker_id', sa.String(36), nullable=True, comment='Healthcare worker who performed the action'),
        sa.Column('event_type', sa.String(50), nullable=False, comment='Type of event'),
        sa.Column('action', sa.String(255), nullable=False, comment='Detailed action description'),
        sa.Column('resource_type', sa.String(50), nullable=True, comment='Type of resource accessed'),
        sa.Column('resource_id', sa.String(255), nullable=True, comment='Identifier of the resource accessed'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='Client IP address'),
        sa.Column('user_agent', sa.String(500), nullable=True, comment='Client user agent string'),
        sa.Column('request_id', sa.String(100), nullable=True, comment='Correlation ID for request tracing'),
        sa.Column('status', sa.String(20), nullable=False, server_default='SUCCESS', comment='Outcome status: SUCCESS/FAILED'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='Error message if status is FAILED'),
        sa.Column('details', sa.Text(), nullable=True, comment='Additional JSON details about the event'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['worker_id'], ['healthcare_workers.worker_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('log_id'),
    )
    
    # Create indexes for audit_logs
    op.create_index('idx_audit_event_timestamp', 'audit_logs', ['event_type', 'created_at'])
    op.create_index('idx_audit_worker_timestamp', 'audit_logs', ['worker_id', 'created_at'])
    op.create_index('idx_audit_status', 'audit_logs', ['status'])
    op.create_index('idx_audit_resource', 'audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_request_id', 'audit_logs', ['request_id'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 9. clinical_notes table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'clinical_notes',
        sa.Column('note_id', sa.String(36), nullable=False, comment='Unique identifier for the clinical note'),
        sa.Column('patient_id', sa.String(36), nullable=False, comment='Patient this note is about'),
        sa.Column('visit_id', sa.String(36), nullable=True, comment='Optional: Specific screening visit this note relates to'),
        sa.Column('author_id', sa.String(36), nullable=True, comment='Healthcare worker who wrote the note'),
        sa.Column('title', sa.String(255), nullable=True, comment='Optional title/summary of the note'),
        sa.Column('content', sa.Text(), nullable=False, comment='Full clinical note text'),
        sa.Column('note_type', sa.String(50), nullable=False, server_default='GENERAL', comment='Type of note'),
        sa.Column('is_urgent', sa.String(20), nullable=False, server_default='NO', comment='Urgency flag: NO/YES/CRITICAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.patient_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['visit_id'], ['screening_visits.visit_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['author_id'], ['healthcare_workers.worker_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('note_id'),
    )
    
    # Create indexes for clinical_notes
    op.create_index('idx_clinical_note_patient', 'clinical_notes', ['patient_id', 'created_at'])
    op.create_index('idx_clinical_note_author', 'clinical_notes', ['author_id', 'created_at'])
    op.create_index('idx_clinical_note_visit', 'clinical_notes', ['visit_id'])
    op.create_index('idx_clinical_note_type', 'clinical_notes', ['note_type'])
    
    # ──────────────────────────────────────────────────────────────────────────
    # 10. reports table
    # ──────────────────────────────────────────────────────────────────────────
    op.create_table(
        'reports',
        sa.Column('report_id', sa.String(36), nullable=False, comment='Unique identifier for the report'),
        sa.Column('visit_id', sa.String(36), nullable=False, comment='Screening visit this report belongs to'),
        sa.Column('generated_by', sa.String(36), nullable=True, comment='Healthcare worker who generated the report'),
        sa.Column('format', sa.String(10), nullable=False, server_default='PDF', comment='Report format: PDF or JSON'),
        sa.Column('file_path', sa.String(500), nullable=False, comment='Path to the stored report file'),
        sa.Column('file_size_bytes', sa.String(20), nullable=True, comment='Size of the report file'),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when report was generated'),
        sa.Column('downloaded_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when report was last downloaded'),
        sa.Column('download_count', sa.String(20), nullable=False, server_default='0', comment='Number of times report has been downloaded'),
        sa.Column('checksum', sa.String(64), nullable=True, comment='SHA-256 checksum of the report file'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Timestamp when the record was last updated'),
        sa.ForeignKeyConstraint(['visit_id'], ['screening_visits.visit_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['healthcare_workers.worker_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('report_id'),
        sa.UniqueConstraint('visit_id'),
    )
    
    # Create indexes for reports
    op.create_index('idx_report_visit', 'reports', ['visit_id'])
    op.create_index('idx_report_generated_at', 'reports', ['generated_at'])
    op.create_index('idx_report_format', 'reports', ['format'])


def downgrade() -> None:
    """
    Drop all tables in reverse order of creation.
    """
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('reports')
    op.drop_table('clinical_notes')
    op.drop_table('audit_logs')
    op.drop_table('shap_explanations')
    op.drop_table('recommendations')
    op.drop_table('predictions')
    op.drop_table('screening_data')
    op.drop_table('screening_visits')
    op.drop_table('patients')
    op.drop_table('healthcare_workers')