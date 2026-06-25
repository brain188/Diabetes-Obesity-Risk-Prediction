"""
PDF report generation utilities.
Creates professional-looking PDF reports for patient screening results.
"""

import io
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from app.core.logging import get_logger
from app.core.constants import RISK_COLORS, get_risk_color

logger = get_logger(__name__)


class PDFGenerator:
    """
    Generate PDF reports for patient screening results.
    Creates professional, formatted PDF documents.
    """
    
    def __init__(self):
        """Initialize PDF generator with styles and fonts."""
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Set up custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=30,
            alignment=TA_CENTER,
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#34495E'),
            spaceAfter=12,
            spaceBefore=12,
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=8,
            spaceBefore=8,
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2C3E50'),
            spaceAfter=6,
            alignment=TA_LEFT,
        ))
        
        # Risk label styles
        self.styles.add(ParagraphStyle(
            name='RiskLow',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(RISK_COLORS.get('Low', '#2ECC71')),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskModerate',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(RISK_COLORS.get('Moderate', '#F39C12')),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        self.styles.add(ParagraphStyle(
            name='RiskHigh',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor(RISK_COLORS.get('High', '#E74C3C')),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#95A5A6'),
            alignment=TA_CENTER,
        ))
    
    async def generate_report_pdf(self, report_data: Dict[str, Any]) -> bytes:
        """
        Generate a PDF report from report data.
        
        Args:
            report_data: Dictionary with all report data
            
        Returns:
            PDF as bytes
        """
        buffer = io.BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Build story (content)
        story = []
        
        # Add header
        story.extend(self._build_header(report_data))
        
        # Add patient information
        story.extend(self._build_patient_info(report_data.get('patient', {})))
        
        # Add screening data
        story.extend(self._build_screening_data(report_data.get('screening', {})))
        
        # Add prediction results
        if 'predictions' in report_data:
            story.extend(self._build_predictions(report_data['predictions']))
        
        # Add SHAP explanation
        if 'explanation' in report_data:
            story.extend(self._build_explanation(report_data['explanation']))

        # Add LIME explanation
        if 'lime_explanation' in report_data:
            story.extend(self._build_lime_explanation(report_data['lime_explanation']))
        
        # Add Global Feature Importance
        if 'global_feature_importance' in report_data:
            story.extend(self._build_global_feature_importance(report_data['global_feature_importance']))
        
        # Add recommendations
        if 'recommendations' in report_data:
            story.extend(self._build_recommendations(report_data['recommendations']))
        
        # Add footer
        story.extend(self._build_footer(report_data))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        logger.info(f"PDF report generated, size: {len(pdf_bytes)} bytes")
        return pdf_bytes
    
    def _build_header(self, report_data: Dict[str, Any]) -> List:
        """Build report header section."""
        story = []
        
        # Title
        story.append(Paragraph(
            "Patient Screening Report",
            self.styles['CustomTitle']
        ))
        
        # Report metadata
        report_id = report_data.get('report_id', 'N/A')
        generated_at = report_data.get('generated_at', datetime.now().isoformat())
        model_version = report_data.get('model_version', 'N/A')
        
        meta_data = [
            f"<b>Report ID:</b> {report_id}",
            f"<b>Generated:</b> {generated_at[:19] if generated_at else 'N/A'}",
            f"<b>Model Version:</b> {model_version}",
        ]
        
        story.append(Paragraph(" | ".join(meta_data), self.styles['CustomBody']))
        story.append(Spacer(1, 12))
        
        # Separator line
        story.append(self._create_separator())
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_patient_info(self, patient: Dict[str, Any]) -> List:
        """Build patient information section."""
        story = []
        
        story.append(Paragraph("Patient Information", self.styles['CustomHeading']))
        
        # Patient info table
        data = [
            ["<b>Full Name</b>", patient.get('full_name', 'N/A')],
            ["<b>Patient ID</b>", patient.get('patient_id', 'N/A')],
            ["<b>Date of Birth</b>", patient.get('date_of_birth', 'N/A')],
            ["<b>Age</b>", f"{patient.get('age', 'N/A')} years"],
            ["<b>Sex</b>", patient.get('sex', 'N/A')],
            ["<b>Contact</b>", patient.get('contact_info', 'N/A') or 'Not provided'],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ECF0F1')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_screening_data(self, screening: Dict[str, Any]) -> List:
        """Build screening data section."""
        story = []
        
        story.append(Paragraph("Screening Measurements", self.styles['CustomHeading']))
        
        # Fix physical activity display - convert boolean to readable text
        physical_activity = screening.get('physical_activity')
        if isinstance(physical_activity, bool):
            physical_activity_text = "Yes" if physical_activity else "No"
        else:
            physical_activity_text = str(physical_activity) if physical_activity is not None else "N/A"
        
        # Screening data table
        data = [
            ["<b>Measurement</b>", "<b>Value</b>"],
            ["Weight", f"{screening.get('weight_kg', 'N/A')} kg"],
            ["Height", f"{screening.get('height_m', 'N/A')} m"],
            ["BMI", f"{screening.get('bmi', 'N/A')}"],
            ["BMI Category", screening.get('bmi_category', 'N/A')],
            ["Physically Active", physical_activity_text],  
            ["Family History Diabetes", "Yes" if screening.get('family_history_diabetes') else "No"],
            ["Previous GDM", "Yes" if screening.get('previous_gdm') else "No"],
            ["Has Hypertension", "Yes" if screening.get('has_hypertension') else "No"],
            ["Is Pregnant", "Yes" if screening.get('is_pregnant') else "No"],
            ["Residence", screening.get('residence', 'N/A')],
        ]

        # Add optional fields if present
        if screening.get('notes'):
            data.append(["Notes", screening['notes']])
        
        table = Table(data, colWidths=[2.5*inch, 3.5*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2C3E50')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#2C3E50')),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_predictions(self, predictions: Dict[str, Any]) -> List:
        """Build predictions section with risk visualizations."""
        story = []
        
        story.append(Paragraph("Risk Prediction Results", self.styles['CustomHeading']))
        
        # Diabetes prediction
        diabetes = predictions.get('diabetes', {})
        if diabetes:
            story.append(Paragraph("Diabetes Risk", self.styles['CustomSubHeading']))
            
            prob = diabetes.get('probability', 0)
            risk_class = diabetes.get('risk_class', 'Low')
            class_label = diabetes.get('class_label', 'Normal')
            
            # Risk color
            risk_color = get_risk_color(risk_class)
            
            # Probability bar
            story.extend(self._create_probability_bar(
                probability=prob,
                label=f"{risk_class} Risk",
                color=risk_color,
                class_label=f"Class: {class_label}"
            ))
        
        # Obesity prediction
        obesity = predictions.get('obesity', {})
        if obesity:
            story.append(Paragraph("Obesity Risk", self.styles['CustomSubHeading']))
            
            bmi = obesity.get('bmi', 0)
            bmi_category = obesity.get('bmi_category', 'Normal')
            risk_class = obesity.get('risk_class', 'Low')
            class_label = obesity.get('class_label', 'Normal')
            
            # Risk color
            risk_color = get_risk_color(risk_class)
            
            # BMI information
            story.append(Paragraph(
                f"<b>BMI:</b> {bmi} ({bmi_category})",
                self.styles['CustomBody']
            ))
            
            # Risk indicator
            story.extend(self._create_risk_indicator(
                risk_class=risk_class,
                risk_color=risk_color,
                class_label=f"Class: {class_label}"
            ))
        
        story.append(Spacer(1, 12))
        
        return story
    
    def _create_probability_bar(self, probability: float, label: str, color: str, class_label: str) -> List:
        """Create a probability bar visualization."""
        story = []
        
        # Show probability
        story.append(Paragraph(
            f"<b>Probability:</b> {probability:.1%}",
            self.styles['CustomBody']
        ))
        
        # Create bar (using table with colored cell)
        bar_data = [
            [
                f"<font color='{color}'><b>{label}</b></font>",
                f"<font color='{color}'><b>{class_label}</b></font>",
            ]
        ]
        
        # Calculate bar width based on probability
        pct = min(max(probability * 100, 0), 100)
        
        bar_table = Table(bar_data, colWidths=[2*inch, 4*inch])
        bar_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor(color)),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F0F0')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor(color)),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.white),
            ('BORDER', (1, 0), (1, -1), 1, colors.HexColor(color)),
        ]))
        
        story.append(bar_table)
        story.append(Spacer(1, 6))
        
        return story
    
    def _create_risk_indicator(self, risk_class: str, risk_color: str, class_label: str) -> List:
        """Create a risk indicator visualization."""
        story = []
        
        # Risk indicator
        indicator_data = [
            [
                f"<b>Risk Level:</b>",
                f"<font color='{risk_color}'><b>{risk_class}</b></font>",
                f"<font color='{risk_color}'><b>{class_label}</b></font>",
            ]
        ]
        
        indicator_table = Table(indicator_data, colWidths=[1.5*inch, 2*inch, 2.5*inch])
        indicator_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor(risk_color)),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.HexColor(risk_color)),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor(risk_color)),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.white),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor(risk_color)),
            ('TEXTCOLOR', (2, 0), (2, 0), colors.white),
        ]))
        
        story.append(indicator_table)
        story.append(Spacer(1, 6))
        
        return story
    
    def _build_explanation(self, explanation: Dict[str, Any]) -> List:
        """Build SHAP explanation section."""
        story = []
        
        story.append(Paragraph("Feature Contributions (SHAP)", self.styles['CustomHeading']))
        
        # Base value
        base_value = explanation.get('base_value', 0)
        story.append(Paragraph(
            f"<b>Base Probability:</b> {base_value:.1%}",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 6))
        
        # Feature contributions
        contributions = explanation.get('feature_contributions', {})
        if contributions:
            # Sort by absolute value
            sorted_features = sorted(
                contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            # Create table
            data = [["<b>Feature</b>", "<b>Contribution</b>", "<b>Impact</b>"]]
            for feature, value in sorted_features[:10]:
                impact = "⬆ Increases Risk" if value > 0 else "⬇ Decreases Risk"
                color = "#E74C3C" if value > 0 else "#2ECC71"
                data.append([
                    feature,
                    f"{value:+.3f}",
                    f"<font color='{color}'>{impact}</font>",
                ])
            
            table = Table(data, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_lime_explanation(self, lime_data: Dict[str, Any]) -> List:
        """Build LIME explanation section."""
        story = []
        
        story.append(Paragraph("LIME Explanation (Model-Agnostic)", self.styles['CustomHeading']))
        story.append(Paragraph(
            "LIME provides a complementary view by explaining the prediction locally.",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 6))
        
        # Feature contributions
        contributions = lime_data.get('feature_contributions', {})
        if contributions:
            # Sort by absolute value
            sorted_features = sorted(
                contributions.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            # Create table
            lime_data_table = [["<b>Feature</b>", "<b>Contribution</b>", "<b>Impact</b>"]]
            for feature, value in sorted_features[:10]:
                impact = "⬆ Increases Risk" if value > 0 else "⬇ Decreases Risk"
                color = "#E74C3C" if value > 0 else "#2ECC71"
                lime_data_table.append([
                    feature,
                    f"{value:+.3f}",
                    f"<font color='{color}'>{impact}</font>",
                ])
            
            table = Table(lime_data_table, colWidths=[2.5*inch, 1.5*inch, 2.5*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 12))
        
        return story

    def _build_global_feature_importance(self, global_importance: Dict[str, Any]) -> List:
        """Build global feature importance section."""
        story = []
        
        story.append(Paragraph("Global Feature Importance", self.styles['CustomHeading']))
        story.append(Paragraph(
            f"Method: {global_importance.get('method', 'N/A')} | Model Version: {global_importance.get('model_version', 'N/A')}",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 6))
        
        # Feature importance
        importance = global_importance.get('feature_importance', {})
        if importance:
            # Sort by importance descending
            sorted_features = sorted(
                importance.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Create table
            data = [["<b>Rank</b>", "<b>Feature</b>", "<b>Importance</b>", "<b>Bar</b>"]]
            max_importance = sorted_features[0][1] if sorted_features else 1
            
            for rank, (feature, value) in enumerate(sorted_features[:10], 1):
                # Calculate bar width (percentage of max)
                bar_width = (value / max_importance) * 100
                
                # Create bar
                bar_data = [[""]]  # Empty cell for bar
                bar_table = Table(bar_data, colWidths=[3*inch])
                bar_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2ECC71')),
                    ('FONTSIZE', (0, 0), (-1, -1), 1),
                    ('BORDER', (0, 0), (-1, -1), 0, colors.white),
                ]))
                
                data.append([
                    str(rank),
                    feature,
                    f"{value:.2f}",
                    bar_table
                ])
            
            table = Table(data, colWidths=[0.5*inch, 2*inch, 1*inch, 3*inch])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BDC3C7')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C3E50')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('PADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#F8F9FA')),
                ('BACKGROUND', (0, 2), (0, -2), colors.HexColor('#FFFFFF')),
                ('BACKGROUND', (0, 3), (0, -3), colors.HexColor('#F8F9FA')),
            ]))
            
            story.append(table)
        
        story.append(Spacer(1, 12))
        
        return story
    def _build_recommendations(self, recommendations: Dict[str, Any]) -> List:
        """Build clinical recommendations section."""
        story = []
        
        story.append(Paragraph("Clinical Recommendations", self.styles['CustomHeading']))
        
        # Priority
        priority = recommendations.get('priority', 'Low')
        priority_color = {
            'High': '#E74C3C',
            'Medium': '#F39C12',
            'Low': '#2ECC71'
        }.get(priority, '#95A5A6')
        
        story.append(Paragraph(
            f"<b>Priority:</b> <font color='{priority_color}'><b>{priority}</b></font>",
            self.styles['CustomBody']
        ))
        story.append(Spacer(1, 6))
        
        # Action text
        action_text = recommendations.get('action_text', '')
        if action_text:
            story.append(Paragraph(
                f"<b>Action:</b> {action_text}",
                self.styles['CustomBody']
            ))
            story.append(Spacer(1, 6))
        
        # Patient advice
        patient_advice = recommendations.get('patient_advice', '')
        if patient_advice:
            story.append(Paragraph(
                f"<b>Patient Advice:</b>",
                self.styles['CustomBody']
            ))
            # Convert bullet points to proper list
            for line in patient_advice.split('\n'):
                if line.strip():
                    story.append(Paragraph(
                        line.strip(),
                        self.styles['CustomBody']
                    ))
            story.append(Spacer(1, 6))
        
        # Follow-up
        follow_up = recommendations.get('follow_up_interval_days')
        if follow_up:
            story.append(Paragraph(
                f"<b>Follow-up:</b> {follow_up} days",
                self.styles['CustomBody']
            ))
        
        # Referral
        referral = recommendations.get('referral_required')
        if referral:
            story.append(Paragraph(
                f"<b>Referral:</b> {referral}",
                self.styles['CustomBody']
            ))
        
        story.append(Spacer(1, 12))
        
        return story
    
    def _build_footer(self, report_data: Dict[str, Any]) -> List:
        """Build report footer."""
        story = []
        
        story.append(self._create_separator())
        story.append(Spacer(1, 6))
        
        footer_text = (
            "This report was generated automatically by the "
            "Intelligent Decision Support System for Early Risk Prediction of "
            "Type 2 Diabetes and Obesity. "
            "For clinical use only. Please consult with a healthcare professional "
            "for interpretation of results."
        )
        
        story.append(Paragraph(footer_text, self.styles['Footer']))
        story.append(Spacer(1, 3))
        
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Page 1",
            self.styles['Footer']
        ))
        
        return story
    
    def _create_separator(self) -> Table:
        """Create a horizontal separator line."""
        data = [[""]]
        table = Table(data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#BDC3C7')),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        return table


# Singleton instance
pdf_generator = PDFGenerator()