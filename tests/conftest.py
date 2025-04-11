from collections.abc import Generator
from datetime import datetime
from typing import Any
from unittest.mock import patch

import pytest
from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture
from textual.app import App

from fico.config import ConfigManager
from tests.types import (
    AccountFactory,
    ConfigMocker,
    EventFactory,
    EventsFactory,
    ListsMocker,
    ObjectFactory,
    PageFactory,
)

SNAPSHOT_RESULTS = pytest.StashKey[dict[str, tuple[bool, App, str, str]]]()
EMPTY_COLLECTION = {"total": 0, "limit": 10, "offset": 0, "items": []}
NO_PAGES = [EMPTY_COLLECTION]


@pytest.fixture(scope="session", autouse=True)
def mock_base_url() -> Generator[None, None, None]:
    with patch("fico.app.API_BASE_URL", "https://localhost/ops/v1"):
        yield


@pytest.fixture()
def config_mocker(mocker: MockerFixture) -> ConfigMocker:
    def _mocker(config: dict | None = None) -> ConfigManager:
        config = config or {}
        mocker.patch.object(ConfigManager, "load_config")
        mocker.patch.object(ConfigManager, "save_config")
        manager = ConfigManager()
        manager.config = config
        mocker.patch("fico.api.ConfigManager", return_value=manager)
        return manager

    return _mocker


@pytest.fixture()
def default_config() -> dict[str, Any]:
    return {
        "credentials": {
            "FACC-5678": "access_token",
            "refresh_token": "refresh_token",
        },
        "user": {"id": "FUSR-1234", "name": "Test user"},
        "last_used_account": {"id": "FACC-5678", "name": "Test account", "type": "operations"},
    }


@pytest.fixture(autouse=True)
def mock_openapi_spec(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://localhost/ops/v1/openapi.json",
        json={"paths": {"/accounts": {"get": {"description": "rql help"}}}},
    )


@pytest.fixture()
def mock_check_user(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        method="GET",
        url="https://localhost/ops/v1/users/FUSR-1234",
        json={},
    )


@pytest.fixture()
def event_factory() -> EventFactory:
    def _event(
        at: datetime | None = None,
        by_id: str | None = None,
        by_name: str | None = None,
        by_type: str | None = None,
    ):
        return {
            "at": at or "2025-01-01T10:00:00+00:00",
            "by": {
                "id": by_id or "FUSR-1234-5678",
                "name": by_name or "John Doe",
                "type": by_type or "user",
            },
        }

    return _event


@pytest.fixture()
def events_factory(event_factory: EventFactory) -> EventsFactory:
    def _events(
        created: bool = True,
        updated: bool = True,
        deleted: bool = False,
        **kwargs: bool,
    ):
        required_events = {"created": created, "updated": updated, "deleted": deleted, **kwargs}
        return {name: event_factory() for name, enabled in required_events.items() if enabled}

    return _events


@pytest.fixture()
def account_factory(events_factory: EventsFactory) -> AccountFactory:
    def _account(
        index: int = 0,
        id: str | None = None,
        name: str | None = None,
        external_id: str | None = None,
        status: str | None = None,
        events: dict[str, dict] | None = None,
    ):
        return {
            "id": id or f"FACC-1234-{index:04}",
            "name": name or f"Stark Industries {index:04} Inc",
            "external_id": external_id or f"AGR-1234-5678-{index:04}",
            "status": status or "active",
            "events": events or events_factory(),
        }

    return _account


@pytest.fixture()
def page_factory() -> PageFactory:
    def _page(
        object_factory: ObjectFactory, total: int = 1, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        items = []
        for i in range(limit):
            items.append(object_factory(offset + i))

        return {"limit": limit, "offset": offset, "total": total, "items": items}

    return _page


@pytest.fixture()
def mock_lists(
    httpx_mock: HTTPXMock,
) -> ListsMocker:
    def _mock(
        accounts: list | None = None,
        organizations: list | None = None,
        entitlements: list | None = None,
        users: list | None = None,
        systems: list | None = None,
    ) -> None:
        accounts = accounts or NO_PAGES
        organizations = organizations or NO_PAGES
        entitlements = entitlements or NO_PAGES
        users = users or NO_PAGES
        systems = systems or NO_PAGES

        for name, pages in (
            ("accounts", accounts),
            ("organizations", organizations),
            ("entitlements", entitlements),
            ("users", users),
            ("systems", systems),
        ):
            for page in pages:
                httpx_mock.add_response(
                    method="GET",
                    url=f"https://localhost/ops/v1/{name}?limit={page['limit']}&offset={page['offset']}",
                    json=page,
                )
    return _mock
