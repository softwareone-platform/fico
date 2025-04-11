from collections.abc import Awaitable, Callable, Iterable
from datetime import datetime
from pathlib import PurePath
from typing import Any, Protocol

from textual.app import App
from textual.pilot import Pilot

from fico.config import ConfigManager


class SnapCompare(Protocol):
    def __call__(
        self,
        app: str | PurePath | App,
        press: Iterable[str] = (),
        terminal_size: tuple[int, int] = (80, 24),
        run_before: Callable[[Pilot], Awaitable[None] | None] | None = None,
    ) -> bool: ...


class ConfigMocker(Protocol):
    def __call__(self, config: dict | None = None) -> ConfigManager: ...


class EventFactory(Protocol):
    def __call__(
        self,
        at: datetime | None = None,
        by_id: str | None = None,
        by_name: str | None = None,
        by_type: str | None = None,
    ) -> dict[str, Any]: ...


class EventsFactory(Protocol):
    def __call__(
        self,
        created: bool = True,
        updated: bool = True,
        deleted: bool = False,
        **kwargs: bool,
    ) -> dict[str, Any]: ...


class AccountFactory(Protocol):
    def __call__(
        self,
        index: int = 0,
        id: str | None = None,
        name: str | None = None,
        external_id: str | None = None,
        status: str | None = None,
        events: dict[str, dict] | None = None,
    ) -> dict[str, Any]: ...


ObjectFactory = AccountFactory


class PageFactory(Protocol):
    def __call__(
        self, object_factory: ObjectFactory, total: int = 1, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]: ...


class ListsMocker(Protocol):
    def __call__(
        self,
        accounts: list | None = None,
        organizations: list | None = None,
        entitlements: list | None = None,
        users: list | None = None,
        systems: list | None = None,
    ) -> None: ...
