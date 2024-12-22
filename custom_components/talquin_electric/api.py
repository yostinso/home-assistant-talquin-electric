"""Sample API Client."""

from __future__ import annotations

import socket
from datetime import datetime
from typing import Any

import aiohttp
import async_timeout

from custom_components.talquin_electric.const import BASE_URL, TOKEN_URL, USER_AGENT
from custom_components.talquin_electric.usage_entry import TalquinElectricUsageEntry


class TalquinElectricApiClientError(Exception):
    """Exception to indicate a general API error."""


class TalquinElectricApiClientCommunicationError(
    TalquinElectricApiClientError,
):
    """Exception to indicate a communication error."""


class TalquinElectricApiClientAuthenticationError(
    TalquinElectricApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise TalquinElectricApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


def _handle_exception(exception: Exception) -> None:
    match exception:
        case TimeoutError():
            msg = f"Timeout error fetching information - {exception}"
            raise TalquinElectricApiClientCommunicationError(
                msg,
            ) from exception
        case aiohttp.ClientError() | socket.gaierror():
            msg = f"Error fetching information - {exception}"
            raise TalquinElectricApiClientCommunicationError(
                msg,
            ) from exception
        case _:
            msg = f"Something really wrong happened! - {exception}"
            raise TalquinElectricApiClientError(
                msg,
            ) from exception


class TalquinElectricApiClient:
    """Very simple API client for Talquin Electric energy data."""

    def __init__(self, username: str, password: str) -> None:
        """Talquin Electric API Client."""
        self._username = username
        self._password = password

    def _default_headers(self) -> dict:
        """Get the default headers."""
        """Talquin Electric requires a User-Agent at minimum."""
        return {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    async def async_get_access_token(self) -> str:
        """Get an access token."""
        return await self._api_wrapper(
            method="post",
            headers=self._default_headers(),
            url=TOKEN_URL,
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
        )

    async def async_get_usage_data(
        self, account_id: str, start_date: datetime, end_date: datetime
    ) -> list[TalquinElectricUsageEntry]:
        """Get the usage data."""
        access_token = await self.async_get_access_token()
        response = await self._api_wrapper(
            method="get",
            headers={
                **self._default_headers(),
                "Authorization": f"Bearer {access_token}",
            },
            url=f"{BASE_URL}accounts/{account_id}/usage",
            params={
                "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "interval": "DAILY",
            },
        )
        return [
            TalquinElectricUsageEntry(
                date=datetime.fromisoformat(entry["date_time"]),
                usage=entry["value"],
            )
            for entry in response
        ]

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Make an actual API request."""
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    response = await session.request(
                        method=method,
                        url=url,
                        headers=headers,
                        data=data,
                        params=params,
                    )
                _verify_response_or_raise(response)
                return await response.json()
        except Exception as exception:  # pylint: disable=broad-except # noqa: BLE001
            _handle_exception(exception)
