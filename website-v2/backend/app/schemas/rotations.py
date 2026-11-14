from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RotationWeights(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    land: float = Field(ge=0, strict=True)
    water: float = Field(ge=0, strict=True)
    practice: float = Field(ge=0, strict=True)

    @model_validator(mode="after")
    def require_positive_total(self) -> "RotationWeights":
        values = (self.land, self.water, self.practice)
        if not all(isfinite(value) for value in values) or not any(value > 0 for value in values):
            raise ValueError("weights must be finite, nonnegative, and have a positive total")
        return self


class RotationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cell_id: int = Field(gt=0, strict=True)
    weights: RotationWeights
