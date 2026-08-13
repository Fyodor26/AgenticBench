from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.user_settings import UserSettingsResponse, UserSettingsUpdate
from app.services.user_settings_service import UserSettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=UserSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the current user's provider configuration / benchmark defaults."""
    settings = UserSettingsService.get_or_create(db, current_user.id)
    return UserSettingsService.to_response(settings)


@router.put("", response_model=UserSettingsResponse)
def update_settings(
    data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update the current user's provider configuration / benchmark defaults.

    Previously the Settings page in the frontend didn't call any backend
    endpoint at all - clicking "Save" just showed an alert() and the values
    were lost on refresh. This persists them (API keys encrypted at rest).
    """
    settings = UserSettingsService.update(db, current_user.id, data)
    return UserSettingsService.to_response(settings)
