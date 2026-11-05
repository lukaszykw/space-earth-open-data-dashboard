import pytest
from fastapi import HTTPException
from pydantic import SecretStr

from app.core.config import settings
from app.core.security import require_admin_token


@pytest.mark.asyncio
async def test_admin_token_rejects_invalid_and_accepts_valid_value(monkeypatch) -> None:
    monkeypatch.setattr(settings, "admin_api_token", SecretStr("expected-token"))

    with pytest.raises(HTTPException) as error:
        await require_admin_token("wrong-token")
    assert error.value.status_code == 401

    await require_admin_token("expected-token")
