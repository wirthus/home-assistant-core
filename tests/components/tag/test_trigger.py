"""Tests for tag triggers."""

import pytest

import homeassistant.components.automation as automation
from homeassistant.components.tag import async_scan_tag
from homeassistant.components.tag.const import DOMAIN, TAG_ID
from homeassistant.setup import async_setup_component

from tests.common import async_mock_service
from tests.components.blueprint.conftest import stub_blueprint_populate  # noqa


@pytest.fixture
def tag_setup(hass, hass_storage):
    """Tag setup."""

    async def _storage(items=None):
        if items is None:
            hass_storage[DOMAIN] = {
                "key": DOMAIN,
                "version": 1,
                "data": {"items": [{"id": "test tag"}]},
            }
        else:
            hass_storage[DOMAIN] = items
        config = {DOMAIN: {}}
        return await async_setup_component(hass, DOMAIN, config)

    return _storage


@pytest.fixture
def calls(hass):
    """Track calls to a mock service."""
    return async_mock_service(hass, "test", "automation")


async def test_triggers(hass, tag_setup, calls):
    """Test tag triggers."""
    assert await tag_setup()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": DOMAIN, TAG_ID: "abc123"},
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )

    await hass.async_block_till_done()

    await async_scan_tag(hass, "abc123", None)
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data["message"] == "service called"


async def test_exception_bad_trigger(hass, calls, caplog):
    """Test for exception on event triggers firing."""

    await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"trigger": {"platform": DOMAIN, "oops": "abc123"}},
                    "action": {
                        "service": "test.automation",
                        "data": {"message": "service called"},
                    },
                }
            ]
        },
    )
    await hass.async_block_till_done()
    assert "Invalid config for [automation]" in caplog.text
