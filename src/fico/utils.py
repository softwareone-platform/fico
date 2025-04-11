import functools
from datetime import datetime
from typing import Any

import pycountry
from rich.text import Text


def format_by(event: dict[str, Any]) -> str:
    if "by" not in event:
        return "-"
    by = event["by"]
    return format_object_label(by)


def format_at(event: dict[str, Any]) -> str:
    if "at" not in event:
        return "-"
    date = datetime.fromisoformat(event["at"])
    return date.strftime("%d/%m/%Y %H:%M:%S")


def format_currency(currency_code: str) -> str:
    currency = pycountry.currencies.get(alpha_3=currency_code)
    return f"{currency.alpha_3} - {currency.name}"


def format_status(status: str) -> Text:
    if status == "active":
        return Text(f"[bold green]{status}[/]")
    elif status == "deleted":
        return Text(f"[bold red]{status}[/]")
    elif status == "disabled":
        return Text(f"[bold orange3]{status}[/]")
    else:
        return Text(f"[bold]{status}[/]")


def format_object_label(obj: dict[str, Any] | None) -> str:
    if not obj:
        return "-"
    return f"{obj["id"]} - {obj["name"]}"



def handle_error_notification(title: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                self.notify_error(title, e)

        return wrapper

    return decorator
