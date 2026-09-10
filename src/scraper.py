import hashlib
from typing import List, Optional, Tuple
from pydantic import BaseModel
from playwright.async_api import Page

class JobListing(BaseModel):
    job_id: str
    title: str
    company: str
    location: Optional[str] = "No especificada"
    summary: str = ""
    full_description: str = ""
    apply_selector: Optional[str] = None

class PortalScraper:
    def __init__(self):
        # Selectores comunes en portales de empleo universitarios y ATS
        self.card_selectors = [
            ".job-card", ".card-vacante", ".offer-item", "article.job",
            "[data-job-id]", "tr.job-row", ".list-group-item"
        ]
        self.apply_button_selectors = [
            "button:has-text('Postularme')",
            "button:has-text('Postular')",
            "a:has-text('Postularme')",
            "a:has-text('Postular')",
            "button:has-text('Aplicar')",
            ".btn-postular", "#btn-postular"
        ]

    def _generate_id(self, title: str, company: str) -> str:
        text = f"{title.strip().lower()}_{company.strip().lower()}"
        return hashlib.md5(text.encode("utf-8")).hexdigest()[:12]

    async def get_visible_jobs(self, page: Page) -> List[JobListing]:
        """Detecta las tarjetas de empleo visibles en la página actual."""
        jobs: List[JobListing] = []
        
        # Estrategia 1: Buscar por selectores de tarjeta conocidos
        for card_sel in self.card_selectors:
            cards = page.locator(card_sel)
            count = await cards.count()
            if count > 0:
                for i in range(count):
                    card = cards.nth(i)
                    text = (await card.inner_text()).strip()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    title = lines[0] if lines else "Puesto sin título"
                    company = lines[1] if len(lines) > 1 else "Empresa no identificada"
                    job_id = await card.get_attribute("data-job-id") or self._generate_id(title, company)
                    
                    jobs.append(JobListing(
                        job_id=job_id,
                        title=title,
                        company=company,
                        summary="\n".join(lines[:4]),
                        full_description=text
                    ))
                return jobs

        # Estrategia 2: Fallback semántico si la página usa links o encabezados directos
        headings = page.locator("h2, h3, h4")
        h_count = await headings.count()
        for i in range(min(h_count, 15)):
            h = headings.nth(i)
            text = (await h.inner_text()).strip()
            if len(text) > 4:
                jobs.append(JobListing(
                    job_id=self._generate_id(text, "USAL"),
                    title=text,
                    company="Portal USAL",
                    summary=text,
                    full_description=text
                ))
        return jobs

    async def extract_active_job_description(self, page: Page) -> str:
        """Extrae la descripción completa del panel o modal activo."""
        detail_selectors = [
            ".job-details", ".offer-description", "#detalle-vacante",
            ".modal-body", ".job-description-content", "main article"
        ]
        for sel in detail_selectors:
            loc = page.locator(sel)
            if await loc.count() > 0 and await loc.first.is_visible():
                return await loc.first.inner_text()
        return await page.inner_text("body")

    async def click_apply_button(self, page: Page) -> Tuple[bool, str]:
        """Localiza el botón de postulación y hace clic seguro."""
        for sel in self.apply_button_selectors:
            btn = page.locator(sel)
            if await btn.count() > 0 and await btn.first.is_visible():
                await btn.first.click()
                await page.wait_for_timeout(1000)
                return True, "Clic ejecutado con éxito en el botón de postulación."
        return False, "No se localizó un botón visible de 'Postularse' o 'Aplicar'."
