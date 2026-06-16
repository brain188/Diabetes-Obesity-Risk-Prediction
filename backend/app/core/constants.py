"""
Application-wide constants.
Centralised here so magic strings/numbers never appear inline in business logic.
"""

DIABETES_THRESH_LOW_MODERATE: float = 0.3472   # P(Diabetic) >= this → Moderate
DIABETES_THRESH_MODERATE_HIGH: float = 0.5472  # P(Diabetic) >= this → High

# =============================================================================
# Risk Band Labels
# =============================================================================
RISK_LOW = "Low"
RISK_MODERATE = "Moderate"
RISK_HIGH = "High"

# Diabetes-specific risk labels (for detailed classification)
DIABETES_RISK_NORMAL = "Normal"
DIABETES_RISK_PREDIABETES = "Prediabetes"
DIABETES_RISK_DIABETIC = "Diabetic"

# Risk band colours (used in API response for the frontend)
RISK_COLORS = {
    RISK_LOW: "#2ECC71",      # Green
    RISK_MODERATE: "#F39C12", # Amber
    RISK_HIGH: "#E74C3C",     # Red
}


# =============================================================================
# BMI Classification (WHO standards)
# =============================================================================
BMI_NORMAL_MAX = 25.0
BMI_OVERWEIGHT_MAX = 30.0
BMI_OBESE_I_MAX = 35.0
# >= 35 → Obese II+

# BMI category labels
BMI_CAT_NORMAL = "Normal"
BMI_CAT_OVERWEIGHT = "Overweight"
BMI_CAT_OBESE_I = "Obese I"
BMI_CAT_OBESE_II = "Obese II+"   

# BMI categories list for validation
BMI_CATEGORIES = [
    BMI_CAT_NORMAL,
    BMI_CAT_OVERWEIGHT,
    BMI_CAT_OBESE_I,
    BMI_CAT_OBESE_II,
]

# BMI to risk mapping
BMI_TO_RISK = {
    BMI_CAT_NORMAL: RISK_LOW,
    BMI_CAT_OVERWEIGHT: RISK_MODERATE,
    BMI_CAT_OBESE_I: RISK_HIGH,
    BMI_CAT_OBESE_II: RISK_HIGH,
}

# =============================================================================
# Diabetes Classification
# =============================================================================
# Target class labels (diabetes model output)
DIABETES_CLASSES = {
    0: "Normal",
    1: "Prediabetes",
    2: "Diabetic",
}

# Reverse mapping for encoding
DIABETES_CLASSES_ENCODE = {v: k for k, v in DIABETES_CLASSES.items()}

# =============================================================================
# Obesity Classification
# =============================================================================
OBESITY_CLASSES = {
    "Normal": "Normal",
    "Overweight": "Overweight",
    "Obese": "Obese",
}

OBESITY_RISK_LEVELS = {
    "Normal": RISK_LOW,
    "Overweight": RISK_MODERATE,
    "Obese": RISK_HIGH,
}

# =============================================================================
# Feature Encoding Values
# =============================================================================
# Sex encoding
SEX_MALE = "Male"
SEX_FEMALE = "Female"
SEX_ENCODE = {SEX_MALE: 0, SEX_FEMALE: 1}

# Residence encoding
RESIDENCE_URBAN = "Urban"
RESIDENCE_RURAL = "Rural"
RESIDENCE_ENCODE = {RESIDENCE_URBAN: 1, RESIDENCE_RURAL: 0}

# Boolean encoding
BOOL_TRUE = 1
BOOL_FALSE = 0
BOOL_ENCODE = {False: 0, True: 1}

# =============================================================================
# Audit Log Event Types
# =============================================================================
AUDIT_LOGIN = "LOGIN"
AUDIT_LOGOUT = "LOGOUT"
AUDIT_LOGIN_FAILED = "LOGIN_FAILED"
AUDIT_REGISTER = "REGISTER"
AUDIT_PATIENT_CREATED = "PATIENT_CREATED"
AUDIT_PATIENT_UPDATED = "PATIENT_UPDATED"
AUDIT_PATIENT_VIEWED = "PATIENT_VIEWED"
AUDIT_SCREENING_DONE = "SCREENING_DONE"
AUDIT_PREDICTION_RUN = "PREDICTION_RUN"
AUDIT_REPORT_GENERATED = "REPORT_GENERATED"
AUDIT_REPORT_DOWNLOADED = "REPORT_DOWNLOADED"
AUDIT_PASSWORD_RESET = "PASSWORD_RESET"
AUDIT_PASSWORD_RESET_REQUEST = "PASSWORD_RESET_REQUEST"
AUDIT_SESSION_EXPIRED = "SESSION_EXPIRED"
AUDIT_CLINICAL_NOTE_ADDED = "CLINICAL_NOTE_ADDED"

# All audit event types for validation
AUDIT_EVENT_TYPES = [
    AUDIT_LOGIN,
    AUDIT_LOGOUT,
    AUDIT_LOGIN_FAILED,
    AUDIT_REGISTER,
    AUDIT_PATIENT_CREATED,
    AUDIT_PATIENT_UPDATED,
    AUDIT_PATIENT_VIEWED,
    AUDIT_SCREENING_DONE,
    AUDIT_PREDICTION_RUN,
    AUDIT_REPORT_GENERATED,
    AUDIT_REPORT_DOWNLOADED,
    AUDIT_PASSWORD_RESET,
    AUDIT_PASSWORD_RESET_REQUEST,
    AUDIT_SESSION_EXPIRED,
    AUDIT_CLINICAL_NOTE_ADDED,
]

# =============================================================================
# Pagination Defaults
# =============================================================================
DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# =============================================================================
# Report Configuration
# =============================================================================
REPORT_FORMAT_PDF = "PDF"
REPORT_FORMAT_JSON = "JSON"
REPORT_FORMATS = [REPORT_FORMAT_PDF, REPORT_FORMAT_JSON]

# Report file extensions
REPORT_EXTENSIONS = {
    REPORT_FORMAT_PDF: ".pdf",
    REPORT_FORMAT_JSON: ".json",
}

# =============================================================================
# Session Configuration
# =============================================================================
SESSION_TIMEOUT_HEADER = "X-Session-Timeout"
SESSION_TOKEN_TYPE = "Bearer"

# =============================================================================
# Medical Input Validation Ranges
# =============================================================================
# Used by the screening data validation layer
WEIGHT_MIN_KG = 20.0
WEIGHT_MAX_KG = 300.0
HEIGHT_MIN_M = 1.0
HEIGHT_MAX_M = 2.5
AGE_MIN = 18
AGE_MAX = 100

# BMI valid range (calculated)
BMI_MIN = 10.0
BMI_MAX = 70.0


# =============================================================================
# API Response Messages
# =============================================================================
MSG_AUTHENTICATION_SUCCESS = "Authentication successful"
MSG_AUTHENTICATION_FAILED = "Invalid email or password"
MSG_TOKEN_INVALID = "Invalid or expired token"
MSG_TOKEN_REFRESHED = "Token refreshed successfully"
MSG_LOGOUT_SUCCESS = "Logout successful"
MSG_PASSWORD_RESET_EMAIL_SENT = "Password reset email sent if account exists"
MSG_PASSWORD_RESET_SUCCESS = "Password reset successful"
MSG_REGISTRATION_SUCCESS = "User registered successfully"
MSG_REGISTRATION_FAILED_EMAIL_EXISTS = "Email already registered"

# Patient related
MSG_PATIENT_CREATED = "Patient registered successfully"
MSG_PATIENT_UPDATED = "Patient updated successfully"
MSG_PATIENT_DELETED = "Patient deleted successfully"
MSG_PATIENT_NOT_FOUND = "Patient not found"

# Screening related
MSG_SCREENING_DATA_SAVED = "Screening data saved successfully"
MSG_SCREENING_DATA_VALIDATION_ERROR = "Screening data validation failed"

# Prediction related
MSG_PREDICTION_SUCCESS = "Risk prediction completed successfully"
MSG_PREDICTION_FAILED = "Risk prediction failed"

# Report related
MSG_REPORT_GENERATED = "Report generated successfully"
MSG_REPORT_DOWNLOADED = "Report downloaded"

# =============================================================================
# Database Defaults
# =============================================================================
DEFAULT_MODEL_VERSION = "1.0.0"
DEFAULT_REPORT_FORMAT = REPORT_FORMAT_PDF

# =============================================================================
# API Rate Limiting
# =============================================================================
RATE_LIMIT_AUTH = "5 per minute"      # Login attempts
RATE_LIMIT_PREDICTION = "30 per minute"
RATE_LIMIT_REPORT = "20 per minute"
RATE_LIMIT_PATIENT_SEARCH = "60 per minute"

# =============================================================================
# Cache Keys
# =============================================================================
CACHE_KEY_MODEL = "ml_model"
CACHE_KEY_PREPROCESSOR = "preprocessor"
CACHE_KEY_SHAP_EXPLAINER = "shap_explainer"
CACHE_KEY_PATIENT_PREFIX = "patient:"
CACHE_KEY_USER_PREFIX = "user:"

# Cache TTL (seconds)
CACHE_TTL_MODEL = 3600      # 1 hour
CACHE_TTL_PATIENT = 300     # 5 minutes
CACHE_TTL_USER = 600        # 10 minutes

# =============================================================================
# Helper Functions
# =============================================================================
def get_risk_color(risk_level: str) -> str:
    """Get the color code for a risk level."""
    return RISK_COLORS.get(risk_level, "#95A5A6")  # Default gray


def get_bmi_category(bmi: float) -> str:
    """Get BMI category based on WHO classification."""
    if bmi < BMI_NORMAL_MAX:
        return BMI_CAT_NORMAL
    elif bmi < BMI_OVERWEIGHT_MAX:
        return BMI_CAT_OVERWEIGHT
    elif bmi < BMI_OBESE_I_MAX:
        return BMI_CAT_OBESE_I
    else:
        return BMI_CAT_OBESE_II


def get_obesity_risk_from_bmi(bmi: float) -> str:
    """Get obesity risk level from BMI value."""
    category = get_bmi_category(bmi)
    return BMI_TO_RISK.get(category, RISK_LOW)


def get_diabetes_class_name(class_id: int) -> str:
    """Get diabetes class name from class ID."""
    return DIABETES_CLASSES.get(class_id, "Unknown")


def get_diabetes_class_id(class_name: str) -> int:
    """Get diabetes class ID from class name."""
    return DIABETES_CLASSES_ENCODE.get(class_name, -1)


def is_valid_bmi(bmi: float) -> bool:
    """Check if BMI is within valid range."""
    return BMI_MIN <= bmi <= BMI_MAX


def is_valid_age(age: int) -> bool:
    """Check if age is within valid range."""
    return AGE_MIN <= age <= AGE_MAX


def is_valid_weight(weight: float) -> bool:
    """Check if weight is within valid range."""
    return WEIGHT_MIN_KG <= weight <= WEIGHT_MAX_KG


def is_valid_height(height: float) -> bool:
    """Check if height is within valid range."""
    return HEIGHT_MIN_M <= height <= HEIGHT_MAX_M