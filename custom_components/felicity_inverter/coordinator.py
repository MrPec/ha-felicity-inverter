"""Data coordinator for the Felicity inverter."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import FelicityClient, FelicityError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type FelicityConfigEntry = ConfigEntry["FelicityCoordinator"]


class FelicityCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the stick."""

    config_entry: FelicityConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: FelicityConfigEntry,
        client: FelicityClient,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.stick_info: dict[str, Any] = {}

    async def _async_setup(self) -> None:
        try:
            self.stick_info = await self.client.async_get_info()
        except FelicityError as err:
            _LOGGER.debug("Could not read stick info: %s", err)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_get_realtime()
        except FelicityError as err:
            raise UpdateFailed(str(err)) from err
