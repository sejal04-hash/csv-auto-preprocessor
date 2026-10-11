from pydantic import BaseModel,Field
from typing import Any, Optional , Dict


class AnalysisResponse(BaseModel):

    file_id: str

    analysis: dict[str, Any]

    health: dict[str, Any]


class PreprocessingConfig(BaseModel):

    # ==========================================
    # TARGET
    # ==========================================

    target_column: Optional[str] = None

    # ==========================================
    # MISSING VALUES
    # ==========================================

    missing_value_strategy: str = "none"

    missing_value_constant: Any = 0

    missing_value_columns: Dict[str, str] = Field(
        default_factory=dict
    )

    missing_value_constants: Dict[str, Any] = Field(
        default_factory=dict
    )

    # ==========================================
    # DUPLICATES
    # ==========================================

    remove_duplicates: bool = False

    # ==========================================
    # OUTLIERS
    # ==========================================

    outlier_method: str = "none"

    outlier_action: str = "remove"

    # ==========================================
    # ENCODING
    # ==========================================

    encoding: str = "none"

    # ==========================================
    # SCALING
    # ==========================================

    scaling: str = "none"

    # ==========================================
    # TRAIN / TEST SPLIT
    # ==========================================

    test_size: float = 0.2

    random_state: int = 42

    stratify: bool = True