"""E2E tests for the API. Only run if non-default credentials are provided."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
import pytest_socket


def credentials_provided() -> bool:
    """Check if non-default credentials are provided."""
    return (
        "TALQUIN_ELECTRIC_USERNAME" in os.environ
        and "TALQUIN_ELECTRIC_PASSWORD" in os.environ
    )


@contextmanager
def socket_enabled() -> Iterator[None]:
    """Enable socket access for the test."""
    pytest_socket.enable_socket()
    pytest_socket.socket_allow_hosts(["api.talquinelectric.com", "127.0.0.1"])
    try:
        yield
    finally:
        pytest_socket.disable_socket(allow_unix_socket=True)
        pytest_socket.socket_allow_hosts(["127.0.0.1"])


@pytest.mark.asyncio
@pytest.mark.skipif(
    not credentials_provided(),
    reason="No credentials provided in TALQUIN_ELECTRIC_USERNAME/PASSWORD.",
)
async def test_e2e_access_token() -> None:
    """Test the API client's ability to fetch an access token."""
    from custom_components.talquin_electric.api import TalquinElectricApiClient

    username = os.environ["TALQUIN_ELECTRIC_USERNAME"]
    password = os.environ["TALQUIN_ELECTRIC_PASSWORD"]

    with socket_enabled():
        client = TalquinElectricApiClient(username=username, password=password)
        access_token = await client.async_get_access_token()

    assert access_token is not None
    assert len(access_token) > 0
