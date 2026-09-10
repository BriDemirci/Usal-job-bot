import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.browser import ChromeConnector

@pytest.mark.asyncio
async def test_find_target_tab():
    connector = ChromeConnector(cdp_url="http://localhost:9222")
    
    mock_page_1 = MagicMock()
    mock_page_1.url = "https://www.google.com"
    mock_page_1.title = AsyncMock(return_value="Google")
    
    mock_page_2 = MagicMock()
    mock_page_2.url = "https://usal.edu.ar/empleo/vacantes"
    mock_page_2.title = AsyncMock(return_value="Portal de Empleo USAL")
    mock_page_2.bring_to_front = AsyncMock()

    mock_context = MagicMock()
    mock_context.pages = [mock_page_1, mock_page_2]

    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]
    connector.browser = mock_browser

    target_page = await connector.find_target_tab(["usal", "empleo"])
    assert target_page == mock_page_2
    mock_page_2.bring_to_front.assert_awaited_once()

@pytest.mark.asyncio
async def test_safe_click_success():
    connector = ChromeConnector(cdp_url="http://localhost:9222")
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.count = AsyncMock(return_value=1)
    mock_locator.first = MagicMock()
    mock_locator.first.scroll_into_view_if_needed = AsyncMock()
    mock_locator.first.click = AsyncMock()

    mock_page.locator.return_value = mock_locator
    connector.active_page = mock_page

    success = await connector.safe_click("button.apply")
    assert success is True
    mock_locator.first.click.assert_awaited_once()

@pytest.mark.asyncio
async def test_safe_click_not_found():
    connector = ChromeConnector(cdp_url="http://localhost:9222")
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_locator.count = AsyncMock(return_value=0)

    mock_page.locator.return_value = mock_locator
    connector.active_page = mock_page

    success = await connector.safe_click("button.missing")
    assert success is False
