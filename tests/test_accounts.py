from typing import Any

from textual.keys import Keys
from textual.pilot import Pilot
from textual.widgets import Input, Select

from fico.app import Fico
from tests.types import (
    AccountFactory,
    ConfigMocker,
    ListsMocker,
    PageFactory,
    SnapCompare,
)


def test_lists_operations_account(
    config_mocker: ConfigMocker,
    default_config: dict[str, Any],
    mock_check_user: Any,
    page_factory: PageFactory,
    account_factory: AccountFactory,
    snap_compare: SnapCompare,
    mock_lists: ListsMocker,
):
    config_mocker(default_config)
    mock_lists(accounts=[page_factory(account_factory, total=10)])
    assert snap_compare(Fico(), terminal_size=(120, 35))


def test_lists_second_page_operations_account_next(
    config_mocker: ConfigMocker,
    default_config: dict[str, Any],
    mock_check_user: Any,
    page_factory: PageFactory,
    account_factory: AccountFactory,
    snap_compare: SnapCompare,
    mock_lists: ListsMocker,
):
    config_mocker(default_config)
    mock_lists(
        accounts=[
            page_factory(account_factory, total=20),
            page_factory(account_factory, total=20, offset=10),
        ]
    )

    async def run_before(pilot: Pilot):
        await pilot.click("#btn-next")

    assert snap_compare(Fico(), terminal_size=(120, 35), run_before=run_before)


def test_lists_second_page_operations_account_page_number(
    config_mocker: ConfigMocker,
    default_config: dict[str, Any],
    mock_check_user: Any,
    page_factory: PageFactory,
    account_factory: AccountFactory,
    snap_compare: SnapCompare,
    mock_lists: ListsMocker,
):
    config_mocker(default_config)
    mock_lists(
        accounts=[
            page_factory(account_factory, total=20),
            page_factory(account_factory, total=20, offset=10),
        ]
    )

    async def run_before(pilot: Pilot):
        await pilot.pause()
        pilot.app.query_one("#current-page", Input).value = "2"
        pilot.app.query_one("#current-page", Input).focus()
        await pilot.press(Keys.Enter)
        await pilot.pause()

    assert snap_compare(Fico(), terminal_size=(120, 35), run_before=run_before)


def test_lists_operations_account_change_rows_per_page(
    config_mocker: ConfigMocker,
    default_config: dict[str, Any],
    mock_check_user: Any,
    page_factory: PageFactory,
    account_factory: AccountFactory,
    snap_compare: SnapCompare,
    mock_lists: ListsMocker,
):
    config_mocker(default_config)
    mock_lists(
        accounts=[
            page_factory(account_factory, total=20),
            page_factory(account_factory, total=20, offset=0, limit=5),
        ]
    )

    async def run_before(pilot: Pilot):
        await pilot.pause()
        pilot.app.query_one("#rows-per-page", Select).value = 5
        await pilot.pause()

    assert snap_compare(Fico(), terminal_size=(120, 35), run_before=run_before)
