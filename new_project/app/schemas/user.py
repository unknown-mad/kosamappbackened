from pydantic import BaseModel, model_validator


class UpdateMobileRequest(BaseModel):
    newMobile: str


class MarkStepCompleteRequest(BaseModel):
    """Accepts either 'step' or 'stepName' (camelCase) in the JSON body."""
    step: str | None = None
    stepName: str | None = None

    @model_validator(mode="before")
    @classmethod
    def step_from_either(cls, data):
        if isinstance(data, dict):
            step = data.get("step") or data.get("stepName")
            if step and isinstance(step, str):
                return {"step": step, "stepName": step}
        return data

    @model_validator(mode="after")
    def require_step(self):
        if not (self.step or self.stepName):
            raise ValueError("Either 'step' or 'stepName' is required")
        return self
