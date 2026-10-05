import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.asyncio
async def test_failed_diff_can_be_requested_again(monkeypatch):
    for key in (
        "CLOUD_SQL_INSTANCE",
        "DB_USER",
        "DB_PASS",
        "DB_NAME",
        "EXTERNAL_API_KEY",
        "INTERNAL_API_KEY",
        "CLOUD_TASKS_PROJECT",
        "CLOUD_TASKS_LOCATION",
        "CLOUD_TASKS_QUEUE",
        "WORKER_URL",
        "PHABRICATOR_URL",
        "PHABRICATOR_API_KEY",
        "BUGZILLA_URL",
        "BUGZILLA_API_KEY",
    ):
        monkeypatch.setenv(key, "test")

    from app.enums import ReviewStatus
    from app.routers import request as request_router
    from app.schemas.review_request import ReviewRequestCreate

    existing = SimpleNamespace(id=50, diff_id=6640, status=ReviewStatus.FAILED)
    db = AsyncMock()
    db.scalar.return_value = existing
    db.execute.return_value = SimpleNamespace(rowcount=1)
    db.add = Mock()
    enqueue = AsyncMock()
    monkeypatch.setattr(request_router, "create_review_task", enqueue)

    response = await request_router.create_or_get_review_request(
        ReviewRequestCreate(
            revision_id=4232,
            diff_id=6640,
            user_id=1,
            user_name="tester",
        ),
        db,
    )

    assert response.status_code == 202
    assert json.loads(response.body)["status"] == "pending"
    db.commit.assert_awaited_once()
    db.add.assert_not_called()
    enqueue.assert_awaited_once_with(50)
