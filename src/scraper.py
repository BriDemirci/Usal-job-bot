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
    already_applied: bool = False

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
        
        # Estrategia 1: Portal USAL específico (.listado_ofertas_item_alumno)
        usal_cards = page.locator(".listado_ofertas_item_alumno")
        usal_count = await usal_cards.count()
        if usal_count > 0:
            import re
            for i in range(usal_count):
                card = usal_cards.nth(i)
                title_loc = card.locator(".title_alumno")
                title = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else "Puesto sin título"
                
                loc_loc = card.locator(".location_alumno")
                location = (await loc_loc.inner_text()).strip() if await loc_loc.count() > 0 else "No especificada"
                
                tipo_loc = card.locator(".tipo_empleo_alumno")
                tipo = (await tipo_loc.inner_text()).strip() if await tipo_loc.count() > 0 else ""
                
                fecha_loc = card.locator(".fecha_publicacion_alumno")
                fecha = (await fecha_loc.inner_text()).strip() if await fecha_loc.count() > 0 else ""
                
                empresa_loc = card.locator(".empresa_interes_alumno, .nombre_empresa")
                company = (await empresa_loc.inner_text()).strip() if await empresa_loc.count() > 0 else "Empresa USAL"
                
                # Extraer id de la oferta si está presente en shareLink o href
                full_card_html = await card.inner_html()
                id_match = re.search(r'id=(\d+)', full_card_html)
                job_id = f"usal-{id_match.group(1)}" if id_match else self._generate_id(title, company)
                
                # Detectar si el alumno ya se postuló previamente desde el portal
                has_applied = await card.locator(".button_alumno_aplicaste").count() > 0

                card_text = (await card.inner_text()).strip()
                summary = f"{title} | {company} | {location} | {tipo} | Publicado: {fecha}"
                
                jobs.append(JobListing(
                    job_id=job_id,
                    title=title,
                    company=company,
                    location=location,
                    summary=summary,
                    full_description=card_text,
                    already_applied=has_applied
                ))
            return jobs

        # Estrategia 2: Buscar por selectores de tarjeta genéricos conocidos
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

    async def apply_to_offer_by_id(self, page: Page, offer_id: str) -> Tuple[bool, str]:
        """Aplica a una oferta específica enviando la solicitud autenticada y registrándola en el portal USAL."""
        numeric_id = offer_id.replace("usal-", "")
        try:
            result = await page.evaluate("""
                async (id) => {
                    function getRandomString(length = 20) {
                        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
                        let res = '';
                        for (let i = 0; i < length; i++) res += chars.charAt(Math.floor(Math.random() * chars.length));
                        return res;
                    }

                    // Paso 1: Enviar notificación de postulación al backend
                    const formData = new URLSearchParams();
                    formData.append('oferta', id);
                    const res1 = await fetch('/site/include/php/mod/aplicar.oferta.php', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                        body: formData
                    });
                    
                    let data1 = null;
                    try {
                        data1 = await res1.json();
                    } catch (e) {
                        return { success: false, error: "Respuesta inválida del servidor USAL." };
                    }

                    if (!data1 || !data1.emailSent) {
                        return { success: false, error: data1 ? data1.error_msg : "El portal no envió la postulación." };
                    }

                    // Paso 2: Ejecutar la confirmación que persiste la postulación en la BD del alumno
                    const confirmUrl = `/ofertas-detalle?aplicado=OK&aplicar=1&id=${id}&c=${getRandomString(20)}`;
                    const res2 = await fetch(confirmUrl);
                    
                    return {
                        success: res2.ok,
                        status: res2.status
                    };
                }
            """, numeric_id)
            if result.get("success"):
                return True, "Postulación confirmada y registrada exitosamente en el portal USAL."
            return False, f"El portal USAL no confirmó la postulación: {result.get('error', result)}"
        except Exception as e:
            return False, f"Error al ejecutar postulación: {e}"

