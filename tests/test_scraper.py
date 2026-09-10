import pytest
from unittest.mock import AsyncMock, MagicMock
from src.scraper import PortalScraper, JobListing

@pytest.mark.asyncio
async def test_job_listing_model():
    job = JobListing(
        job_id="usal-9988",
        title="Desarrollador Backend",
        company="Banco Ciudad",
        summary="Puesto junior remoto",
        apply_selector="button.postular"
    )
    assert job.job_id == "usal-9988"
    assert job.company == "Banco Ciudad"
    assert job.location == "No especificada"

def test_generate_id():
    scraper = PortalScraper()
    id1 = scraper._generate_id("Desarrollador Junior", "Empresa A")
    id2 = scraper._generate_id("Desarrollador Junior", "Empresa A")
    id3 = scraper._generate_id("Desarrollador Senior", "Empresa A")
    assert id1 == id2
    assert id1 != id3

@pytest.mark.asyncio
async def test_click_apply_button_found():
    scraper = PortalScraper()
    mock_page = MagicMock()
    mock_btn = MagicMock()
    mock_btn.count = AsyncMock(return_value=1)
    mock_btn.first = MagicMock()
    mock_btn.first.is_visible = AsyncMock(return_value=True)
    mock_btn.first.click = AsyncMock()
    mock_page.locator.return_value = mock_btn
    mock_page.wait_for_timeout = AsyncMock()

    success, msg = await scraper.click_apply_button(mock_page)
    assert success is True
    assert "éxito" in msg

@pytest.mark.asyncio
async def test_click_apply_button_not_found():
    scraper = PortalScraper()
    mock_page = MagicMock()
    mock_btn = MagicMock()
    mock_btn.count = AsyncMock(return_value=0)
    mock_page.locator.return_value = mock_btn

    success, msg = await scraper.click_apply_button(mock_page)
    assert success is False
    assert "No se localizó" in msg
