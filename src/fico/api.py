from __future__ import annotations

import asyncio
import functools
import logging
from asyncio import Semaphore
from collections.abc import AsyncGenerator
from typing import Any

from httpx import AsyncClient, Auth, HTTPError, HTTPStatusError, Request, Response, codes
from textual import log

from fico.config import Config

logger = logging.getLogger(__name__)

CONCURRENCY = 5
ITEMS_PER_PAGE = 100


class APIError(Exception):
    def __init__(self, message: str):
        self.message = message

    @classmethod
    def from_exception(cls, error: HTTPError):
        if isinstance(error, HTTPStatusError):
            status = error.response.status_code
            if status == codes.BAD_REQUEST:
                return cls(error.response.json()["detail"])

        return cls(str(error))


def api_error_formatter():
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                raise APIError.from_exception(e) from e

        return wrapper

    return decorator


class FFCOpsAuth(Auth):
    requires_response_body = True

    def __init__(self, refresh_url: str, client: FFCOpsClient):
        self.refresh_url = refresh_url
        self.client = client

    async def async_auth_flow(self, request: Request) -> AsyncGenerator[Request, Response]:
        request.headers["Authorization"] = f"Bearer {self.client.get_access_token()}"
        response = yield request

        if response.status_code == 401:
            log("Access token has expired, try to refresh it")
            refresh_request = self.build_refresh_request()
            refresh_response = yield refresh_request
            await refresh_response.aread()
            self.update_tokens(refresh_response)

            # Retry the original request with the new token
            request.headers["Authorization"] = f"Bearer {self.client.get_access_token()}"
            yield request

    def build_refresh_request(self) -> Request:
        """Builds the token refresh request."""
        return Request(
            "POST",
            self.refresh_url,
            json={
                "account": {"id": self.client.get_current_account()["id"]},
                "refresh_token": self.client.get_refresh_token(),
            },
        )

    def update_tokens(self, response: Response) -> None:
        """Updates tokens after a successful refresh."""
        if response.status_code == 200:
            data = response.json()
            self.client.set_credentials(data["access_token"], data["refresh_token"])


class FFCOpsClient:
    def __init__(self) -> None:
        self.config = Config()
        self.limit = 10
        self.specs: dict = {}
        if not self.config.is_configured():
            return
        self.client = AsyncClient(
            base_url=self.config.get_url(),
            auth=FFCOpsAuth(f"{self.config.get_url()}/auth/tokens", self),
        )

    def get_url(self) -> str:
        return self.config.get_url()

    def get_current_account(self) -> dict[str, Any]:
        return self.config.get_last_used_account()

    def get_current_user(self) -> dict[str, Any]:
        return self.config.get_user()

    def get_access_token(self) -> str | None:
        return self.config.get_access_token()

    def get_refresh_token(self) -> str | None:
        return self.config.get_refresh_token()

    def set_credentials(self, access_token, refresh_token) -> None:
        self.config.set_credentials(access_token, refresh_token)

    async def logout(self) -> None:
        await self.client.aclose()
        self.config.delete()

    async def fetch_specs(self) -> None:
        response = await self.client.get("/openapi.json", auth=None)
        response.raise_for_status()
        self.specs = response.json()

    async def can_connect(self) -> bool:
        if not self.config.is_configured():
            return False
        user = self.config.get_user()
        response = await self.client.get(
            f"/users/{user['id']}",
        )
        if response.status_code == 200:
            await self.fetch_specs()
            return True
        return False

    async def change_current_account(self, account: dict[str, Any]) -> None:
        self.config.set_last_used_account(account)
        response = await self.client.post(
            "/auth/tokens",
            json={"account": {"id": account}, "refresh_token": self.get_refresh_token()},
        )
        response.raise_for_status()
        data = response.json()
        self.set_credentials(data["access_token"], data["refresh_token"])

    async def login(self, base_url: str, email: str, password: str) -> None:
        self.client = AsyncClient(
            base_url=base_url,
            auth=FFCOpsAuth(f"{base_url}/auth/tokens", self),
        )
        await self.fetch_specs()
        response = await self.client.post(
            "/auth/tokens",
            json={"email": email, "password": password},
            auth=None,  # type: ignore
        )
        response.raise_for_status()
        data = response.json()
        self.config.set_url(base_url)
        self.config.set_user(data["user"])
        self.config.set_last_used_account(data["account"])
        self.set_credentials(data["access_token"], data["refresh_token"])

    async def get_current_user_accounts(self) -> list[dict[str, Any]]:
        user = self.config.get_user()
        return await self.get_all_objects(f"users/{user['id']}/accounts")

    def get_rql_help(self, collection: str) -> str:
        return self.specs["paths"][f"/{collection}"]["get"]["description"]

    @api_error_formatter()
    async def list_objects(
        self, collection: str, limit: int, offset: int, rql: str | None = None
    ) -> dict[str, Any]:
        qs = f"limit={limit}&offset={offset}"
        if rql:
            qs = f"{rql}&{qs}"
        response = await self.client.get(
            f"/{collection}?{qs}",
        )
        response.raise_for_status()
        return response.json()

    @api_error_formatter()
    async def create_object(self, collection: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(
            f"/{collection}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @api_error_formatter()
    async def get_object(self, collection: str, id: str) -> dict[str, Any]:
        response = await self.client.get(f"/{collection}/{id}")
        response.raise_for_status()
        return response.json()

    @api_error_formatter()
    async def update_object(
        self, collection: str, id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        response = await self.client.put(
            f"/{collection}/{id}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @api_error_formatter()
    async def delete_object(self, collection: str, id: str) -> None:
        response = await self.client.delete(f"/{collection}/{id}")
        response.raise_for_status()

    @api_error_formatter()
    async def execute_object_action(
        self,
        collection: str,
        method: str,
        id: str,
        action: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        response = await self.client.request(
            method.upper(),
            f"/{collection}/{id}/{action}",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    @api_error_formatter()
    async def switch_account(self, account_id: str) -> None:
        response = await self.client.post(
            "/auth/tokens",
            json={
                "account": {"id": account_id},
                "refresh_token": self.config.get_refresh_token(),
            },
            auth=None,  # type: ignore
        )
        log(response.json())
        response.raise_for_status()
        data = response.json()
        self.config.set_last_used_account(data["account"])
        self.set_credentials(data["access_token"], data["refresh_token"])

    async def get_user_accounts(
        self, id: str, limit: int, offset: int, rql: str | None = None
    ) -> dict[str, Any]:
        return await self.list_objects(
            f"users/{id}/accounts",
            limit,
            offset,
            rql=rql,
        )

    async def get_employee(self, email):
        response = await self.client.get(
            f"/employees/{email}",
        )
        if response.status_code == 404:
            return
        return response.json()

    async def get_organization_employees(self, id: str, limit: int, offset: int):
        response = await self.client.get(
            f"/organizations/{id}/employees?limit={limit}&offset={offset}",
        )
        if response.status_code == 404:
            return
        items = response.json()
        return {
            "total": len(items),
            "items": items,
        }

    async def create_employee(self, payload):
        response = await self.client.post(
            "/employees",
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def get_all_objects(
        self, collection: str, rql: str | None = None
    ) -> list[dict[str, Any]]:
        semaphore = Semaphore(CONCURRENCY)

        async def fetch_page(offset):
            async with semaphore:
                response = await self.list_objects(collection, ITEMS_PER_PAGE, offset, rql)
                return response["items"]

        response = await self.list_objects(collection, 0, 0, rql)
        total = response["total"]
        offset = 0
        tasks = []
        while offset < total:
            tasks.append(asyncio.create_task(fetch_page(offset)))
            offset += ITEMS_PER_PAGE

        all_items = []
        pages = await asyncio.gather(*tasks)
        for page in pages:
            all_items.extend(page)
        return all_items
