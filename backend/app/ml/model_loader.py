"""
Loads all ML artifacts produced by the Kedro pipelines ONCE at application
startup and keeps them in memory for the lifetime of the process.

Artifacts loaded
----------------
  trained_model    — data/06_models/trained_model.pkl   (CatBoost classifier)
  scaler           — data/06_models/scaler.pkl          (fitted MinMaxScaler)
  shap_explainer   — data/06_models/shap_explainer.pkl  (fitted SHAP TreeExplainer)
  model_metadata   — data/08_reporting/model_metadata.json
                      (feature_names, target_encoding, threshold, test_metrics)

"""

import json
import pickle
from pathlib import Path
from typing import Any, Optional

from app.core.config import settings
from app.core.exceptions import ModelNotLoadedError
from app.core.logging import get_logger

log = get_logger(__name__)


class ModelLoader:
    """
    Holds the trained model, scaler, SHAP explainer, and metadata.

    Usage
    -----
        loader = ModelLoader()
        loader.load_all()              # called once at startup

        model      = loader.get_model()
        scaler     = loader.get_scaler()
        explainer  = loader.get_shap_explainer()
        meta       = loader.get_metadata()
        background = loader.get_lime_backgroung()
    """

    def __init__(self) -> None:
        self._model: Optional[Any] = None
        self._scaler: Optional[Any] = None
        self._shap_explainer: Optional[Any] = None
        self._metadata: Optional[dict] = None
        self._loaded: bool = False

    # Loading

    def load_all(self) -> None:
        """
        Load every artifact from disk.

        Raises
        ------
        FileNotFoundError — if any artifact file is missing.
        Exception         — if any artifact fails to deserialize.

        Called once during the FastAPI lifespan startup event.
        A failure here should prevent the app from starting (fail fast —
        NFR-2 Reliability).
        """
        log.info("Loading ML artifacts...")

        self._model           = self._load_pickle(settings.TRAINED_MODEL_PATH, "trained model")
        self._scaler          = self._load_pickle(settings.SCALER_PATH, "scaler")
        self._shap_explainer  = self._load_pickle(settings.SHAP_EXPLAINER_PATH, "SHAP explainer")
        self._metadata        = self._load_json(settings.MODEL_METADATA_PATH, "model metadata")
        self._lime_background = self._load_pickle(settings.LIME_BACKGROUND_PATH, "LIME background")

        self._validate_metadata()
        self._loaded = True

        log.info(
            "ML artifacts loaded successfully. model=%s version=%s features=%d",
            self._metadata.get("model_name"),
            self._metadata.get("model_version"),
            len(self._metadata.get("feature_names", [])),
        )

    @staticmethod
    def _load_pickle(path: Path, label: str) -> Any:
        if not path.exists():
            log.error("%s file not found at %s", label, path)
            raise FileNotFoundError(f"{label} not found at {path}")
        with open(path, "rb") as f:
            obj = pickle.load(f)
        log.debug("%s loaded from %s", label, path)
        return obj

    @staticmethod
    def _load_json(path: Path, label: str) -> dict:
        if not path.exists():
            log.error("%s file not found at %s", label, path)
            raise FileNotFoundError(f"{label} not found at {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        log.debug("%s loaded from %s", label, path)
        return data

    def _validate_metadata(self) -> None:
        """
        Ensure model_metadata.json contains everything the prediction
        pipeline depends on. Fail fast if the training pipeline produced
        an incomplete metadata file.
        """
        required_keys = ["feature_names", "target_encoding", "threshold"]
        missing = [k for k in required_keys if k not in self._metadata]
        if missing:
            raise ValueError(
                f"model_metadata.json is missing required keys: {missing}"
            )

        threshold = self._metadata["threshold"]
        for key in ("thresh_low_high", "thresh_high"):
            if key not in threshold:
                raise ValueError(f"model_metadata.json['threshold'] missing '{key}'")

        if not self._metadata["feature_names"]:
            raise ValueError("model_metadata.json['feature_names'] is empty")

    # ── Accessors ─────────────────────────────────────────────────────────────
    # Every accessor raises ModelNotLoadedError if load_all() was not called,
    # so a programming error surfaces immediately as a 503 rather than a
    # confusing AttributeError deep in prediction logic.

    def get_model(self) -> Any:
        self._ensure_loaded()
        return self._model

    def get_scaler(self) -> Any:
        self._ensure_loaded()
        return self._scaler

    def get_shap_explainer(self) -> Any:
        self._ensure_loaded()
        return self._shap_explainer

    def get_metadata(self) -> dict:
        self._ensure_loaded()
        return self._metadata
    
    def get_background(self) -> Any:
        self._ensure_loaded()
        return self._lime_background

    @property
    def model_version(self) -> str:
        self._ensure_loaded()
        return self._metadata.get("model_version", "unknown")

    @property
    def feature_names(self) -> list[str]:
        self._ensure_loaded()
        return self._metadata["feature_names"]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _ensure_loaded(self) -> None:
        if not self._loaded:
            raise ModelNotLoadedError()

    def get_feature_importance_cached(self) -> tuple[list[dict], str]:
        """
        Compute and cache native feature importance on first call.
        Subsequent calls return the cached result — it never changes
        between requests since the model is fixed.
        """
        if not hasattr(self, "_feature_importance_cache"):
            from app.ml.explainers import get_feature_importance
            self._feature_importance_cache = get_feature_importance(self)
            log.info("Feature importance cached at startup.")
        return self._feature_importance_cache

    def get_shap_explainer_cached(self):
        """
        Build shap.TreeExplainer from the live model once and cache it.
        Avoids rebuilding the explainer (0.5–2 s) on every prediction request.
        Thread-safe: TreeExplainer is read-only during inference.
        """
        if not hasattr(self, "_cached_shap_explainer"):
            import shap
            self._cached_shap_explainer = shap.TreeExplainer(self.get_model())
            log.info("SHAP TreeExplainer built and cached.")
        return self._cached_shap_explainer

    def get_lime_explainer_cached(self):
        """
        Build LimeTabularExplainer from background data once and cache it.
        Avoids rebuilding the explainer (0.3–1 s) on every prediction request.
        Thread-safe: explain_instance does not mutate the explainer object.
        """
        if not hasattr(self, "_cached_lime_explainer"):
            from lime.lime_tabular import LimeTabularExplainer
            background = self.get_background()
            self._cached_lime_explainer = LimeTabularExplainer(
                training_data=background.values,
                feature_names=self.feature_names,
                class_names=["Normal", "Prediabetes", "Diabetic"],
                mode="classification",
                discretize_continuous=True,
                random_state=42,
            )
            log.info("LIME LimeTabularExplainer built and cached.")
        return self._cached_lime_explainer


# ── Module-level singleton ────────────────────────────────────────────────────
# One instance shared across the whole application, attached to app.state
# in main.py's lifespan handler. Importing this module never triggers loading.
model_loader = ModelLoader()