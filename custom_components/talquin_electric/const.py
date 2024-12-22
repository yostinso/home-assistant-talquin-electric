"""Constants for talquin_electric."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "talquin_electric"
ATTRIBUTION = "Data provided by https://talquinelectric.com/"

# Common URLs
BASE_URL = "https://api.talquinelectric.com/v1/"
TOKEN_URL = f"{BASE_URL}oauth2/token"
USER_AGENT = "Home Assistant - Talquin Electric Integration"
