"""Tests for the API connectivity."""

import socket
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from pytest_mock import MockerFixture

from custom_components.talquin_electric.api import (
    TalquinElectricApiClient,
    TalquinElectricApiClientAuthenticationError,
    TalquinElectricApiClientCommunicationError,
    TalquinElectricApiClientError,
    _handle_exception,
    _verify_response_or_raise,
)
from custom_components.talquin_electric.usage_entry import TalquinElectricUsageEntry


@pytest.mark.asyncio
async def test_get_access_token() -> None:
    """Test getting an access token."""
    client = TalquinElectricApiClient(username="username", password="password")
    client._api_wrapper = AsyncMock()
    client._api_wrapper.return_value = "access token"

    token = await client.async_get_access_token()

    client._api_wrapper.assert_called_once_with(
        method="post",
        url="https://api.talquinelectric.com/v1/oauth2/token",
        data={
            "grant_type": "password",
            "username": "username",
            "password": "password",
        },
        headers={
            "User-Agent": "Home Assistant - Talquin Electric Integration",
            "Accept": "application/json",
        },
    )

    assert token == "access token"


@pytest.mark.asyncio
async def test_get_usage_data(mocker: MockerFixture) -> None:
    """Test getting usage data."""
    client = TalquinElectricApiClient(username="username", password="password")
    client._api_wrapper = AsyncMock()
    client._api_wrapper.return_value = [
        {"date_time": "2021-01-20T17:00:00Z", "value": 1.0},
        {"date_time": "2021-01-21T18:00:00Z", "value": 2.0},
    ]
    mocker.patch(
        "custom_components.talquin_electric.api.TalquinElectricApiClient.async_get_access_token",
        return_value="access_token",
    )

    usage_data = await client.async_get_usage_data(
        account_id="account_id",
        start_date=datetime.fromisoformat("2021-01-01T00:00:00Z"),
        end_date=datetime.fromisoformat("2021-01-30T00:00:00Z"),
    )

    client._api_wrapper.assert_called_once_with(
        method="get",
        url="https://api.talquinelectric.com/v1/accounts/account_id/usage",
        headers={
            "User-Agent": "Home Assistant - Talquin Electric Integration",
            "Accept": "application/json",
            "Authorization": "Bearer access_token",
        },
        params={
            "start_date": "2021-01-01T00:00:00Z",
            "end_date": "2021-01-30T00:00:00Z",
            "interval": "DAILY",
        },
    )

    assert usage_data == [
        TalquinElectricUsageEntry(datetime.fromisoformat("2021-01-20T17:00:00Z"), 1.0),
        TalquinElectricUsageEntry(datetime.fromisoformat("2021-01-21T18:00:00Z"), 2.0),
    ]


def test__handle_exception() -> None:
    """Test converting exceptions from aiohttp to API exceptions."""
    timeouterror = TimeoutError("error message")
    with pytest.raises(TalquinElectricApiClientCommunicationError) as commserror:
        _handle_exception(timeouterror)
    assert commserror.value.__cause__ == timeouterror
    assert str(commserror.value) == "Timeout error fetching information - error message"

    clienterror = aiohttp.ClientError("error message")
    with pytest.raises(TalquinElectricApiClientCommunicationError) as commserror:
        _handle_exception(clienterror)
    assert commserror.value.__cause__ == clienterror
    assert str(commserror.value) == "Error fetching information - error message"

    socketerror = socket.gaierror("error message")
    with pytest.raises(TalquinElectricApiClientCommunicationError) as commserror:
        _handle_exception(socketerror)
    assert commserror.value.__cause__ == socketerror
    assert str(commserror.value) == "Error fetching information - error message"

    othererror = ValueError("error message")
    with pytest.raises(TalquinElectricApiClientError) as apierror:
        _handle_exception(othererror)
    assert apierror.value.__cause__ == othererror
    assert str(apierror.value) == "Something really wrong happened! - error message"


def test__verify_response_or_raise() -> None:
    """Test that an exception is raised if credentials are bad (401, 403 responses)."""
    response = Mock()
    response.status = 401
    response.raise_for_status.assert_not_called()
    with pytest.raises(TalquinElectricApiClientAuthenticationError) as autherror:
        _verify_response_or_raise(response)
    assert str(autherror.value) == "Invalid credentials"

    response = Mock()
    response.status = 403
    response.raise_for_status.assert_not_called()
    with pytest.raises(TalquinElectricApiClientAuthenticationError) as autherror:
        _verify_response_or_raise(response)
    assert str(autherror.value) == "Invalid credentials"

    response = Mock()
    response.status = 200
    _verify_response_or_raise(response)
    response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
@patch(
    "custom_components.talquin_electric.api._verify_response_or_raise",
    new_callable=Mock,
)
@patch("aiohttp.ClientSession.request", new_callable=AsyncMock)
async def test__api_wrapper_success(mock_request: AsyncMock, mock_verify: Mock) -> None:
    """Test the API wrapper."""
    client = TalquinElectricApiClient(username="username", password="password")
    mock_response = Mock(name="MockResponse")
    mock_response.json = AsyncMock()
    mock_response.json.return_value = "ok"

    mock_request.return_value = mock_response

    await client._api_wrapper(
        method="post",
        url="url",
        data={"data": "data"},
        headers={"headers": "headers"},
        params={"params": "params"},
    )

    mock_verify.assert_called_once_with(mock_response)

    mock_request.assert_called_once_with(
        method="post",
        url="url",
        data={"data": "data"},
        headers={"headers": "headers"},
        params={"params": "params"},
    )


@pytest.mark.asyncio
@patch(
    "custom_components.talquin_electric.api._handle_exception",
    new_callable=Mock,
)
@patch(
    "custom_components.talquin_electric.api._verify_response_or_raise",
    new_callable=Mock,
)
@patch("aiohttp.ClientSession.request", new_callable=AsyncMock)
async def test__api_wrapper_failure(
    mock_request: AsyncMock, mock_verify: Mock, mock_handler: Mock
) -> None:
    """Test the API wrapper."""
    error = TalquinElectricApiClientError("error message")
    client = TalquinElectricApiClient(username="username", password="password")
    mock_response = Mock(name="MockResponse")
    mock_request.return_value = mock_response
    mock_verify.side_effect = error

    await client._api_wrapper(
        method="post",
        url="url",
        data={"data": "data"},
        headers={"headers": "headers"},
        params={"params": "params"},
    )
    mock_handler.assert_called_once_with(error)
