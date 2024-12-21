"""Custom types for talquin_electric."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import TalquinElectricApiClient
    from .coordinator import BlueprintDataUpdateCoordinator


type TalquinElectricConfigEntry = ConfigEntry[TalquinElectricData]


@dataclass
class TalquinElectricData:
    """Data for the Blueprint integration."""

    client: TalquinElectricApiClient
    coordinator: BlueprintDataUpdateCoordinator
    integration: Integration
