from typing import Any

from pytest_httpx import HTTPXMock
from pytest_mock import MockerFixture

from fico.api import FFCOpsClient
from fico.app import Fico
from tests.types import ConfigMocker, ListsMocker, SnapCompare


def test_login_layout(
    config_mocker: ConfigMocker,
    snap_compare: SnapCompare,
):
    config_mocker()

    async def run_before(pilot):
        await pilot.press("\t")
        await pilot.press(*list("test@example.com"))
        await pilot.press("\t")
        await pilot.press(*list("mypassword"))

    assert snap_compare(Fico(), run_before=run_before, terminal_size=(120, 35))


async def test_login_ok(
    config_mocker: ConfigMocker,
    httpx_mock: HTTPXMock,
    mock_lists: ListsMocker,
):
    config = config_mocker()
    httpx_mock.add_response(
        method="POST",
        url="https://localhost/ops/v1/auth/tokens",
        json={
            "user": {"id": "FUSR-1234", "name": "Test user"},
            "account": {"id": "FACC-5678", "name": "Test account", "type": "operations"},
            "access_token": "access_token",
            "refresh_token": "refresh_token",
        },
    )
    mock_lists()

    app = Fico()

    async with app.run_test() as pilot:
        await pilot.press("\t")
        await pilot.press(*list("test@example.com"))
        await pilot.press("\t")
        await pilot.press(*list("mypassword"))
        await pilot.click("#login")

    assert config.config == {
        "credentials": {
            "FACC-5678": "access_token",
            "refresh_token": "refresh_token",
        },
        "user": {"id": "FUSR-1234", "name": "Test user"},
        "last_used_account": {"id": "FACC-5678", "name": "Test account", "type": "operations"},
    }


async def test_login_cancel(
    mocker: MockerFixture, config_mocker: ConfigMocker, httpx_mock: HTTPXMock
):
    config_mocker()
    mocked_login = mocker.patch.object(FFCOpsClient, "login")
    app = Fico()

    async with app.run_test() as pilot:
        await pilot.click("#cancel")

    mocked_login.assert_not_awaited()
