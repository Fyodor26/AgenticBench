from sqlalchemy.orm import Session

from app.core.security import encrypt_secret
from app.models.user_settings import UserSettings
from app.schemas.user_settings import UserSettingsUpdate, UserSettingsResponse


class UserSettingsService:
    @staticmethod
    def get_or_create(db: Session, user_id: int) -> UserSettings:
        settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not settings:
            settings = UserSettings(user_id=user_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @staticmethod
    def update(db: Session, user_id: int, data: UserSettingsUpdate) -> UserSettings:
        settings = UserSettingsService.get_or_create(db, user_id)

        update_data = data.model_dump(exclude_unset=True)

        if "gemini_api_key" in update_data:
            settings.gemini_api_key_encrypted = encrypt_secret(update_data.pop("gemini_api_key"))
        if "openai_api_key" in update_data:
            settings.openai_api_key_encrypted = encrypt_secret(update_data.pop("openai_api_key"))

        for key, value in update_data.items():
            setattr(settings, key, value)

        db.commit()
        db.refresh(settings)
        return settings

    @staticmethod
    def to_response(settings: UserSettings) -> UserSettingsResponse:
        return UserSettingsResponse(
            ollama_base_url=settings.ollama_base_url,
            gemini_api_key_set=bool(settings.gemini_api_key_encrypted),
            openai_api_key_set=bool(settings.openai_api_key_encrypted),
            judge_model=settings.judge_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
