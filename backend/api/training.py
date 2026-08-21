"""Dataset preparation endpoints for fine-tuning."""

from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from core.errors import ChatServiceError, ValidationError
from services.dataset_service import DatasetService

router = APIRouter()
service = DatasetService()


class DatasetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    examples: list[dict] = Field(..., min_length=1, max_length=DatasetService.MAX_EXAMPLES)


@router.get("/training/datasets", status_code=status.HTTP_200_OK)
def list_datasets():
    return {"datasets": service.list_datasets()}


@router.post("/training/datasets", status_code=status.HTTP_201_CREATED)
def create_dataset(request: DatasetRequest):
    try:
        return service.create_dataset(request.name, request.examples)
    except ValidationError:
        raise
    except Exception as exc:
        raise ChatServiceError("Failed to prepare training dataset") from exc