import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from src.browser import ChromeConnector
from src.scraper import PortalScraper
from src.evaluator import JobEvaluator
from src.storage import StorageRepository
from src.ui import console, print_welcome, print_job_card, ask_user_confirmation

def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Bot de búsqueda y postulación en portal USAL")
    parser.add_argument("--auto", action="store_const", const="auto", dest="mode", help="Modo 100% automático")
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode", help="Auditoría sin postular")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="URL del puerto de depuración de Chrome")
    parser.set_defaults(mode="interactive")
    return parser.parse_args(args)

async def main_async():
    load_dotenv()
    args = parse_args(sys.argv[1:])
    print_welcome()

    base_dir = Path(__file__).parent
    profile_path = base_dir / "config" / "profile.json"
    criteria_path = base_dir / "config" / "criteria.json"

    if not profile_path.exists() or not criteria_path.exists():
        console.print("[bold red]ERROR:[/bold red] Archivos de configuración no encontrados en config/")
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)
    with open(criteria_path, "r", encoding="utf-8") as f:
        criteria = json.load(f)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "tu_api_key_aqui":
        console.print("[bold red]ERROR:[/bold red] GEMINI_API_KEY no está configurada válidamente en .env")
        return

    storage = StorageRepository(base_dir / "data" / "job_history.db")
    storage.init_db()

    evaluator = JobEvaluator(api_key=api_key, profile=profile, criteria=criteria)
    scraper = PortalScraper()
    connector = ChromeConnector(cdp_url=args.cdp_url)

    try:
        console.print(f"[cyan]Conectando a Chrome en {args.cdp_url}...[/cyan]")
        page = await connector.connect()
        page_title = await page.title() if hasattr(page, "title") else "Sin título"
        console.print(f"[green]Conectado con éxito a la pestaña:[/green] {page_title}")

        console.print("[cyan]Buscando ofertas de empleo visibles...[/cyan]")
        jobs = await scraper.get_visible_jobs(page)
        console.print(f"Se encontraron [bold]{len(jobs)}[/bold] vacantes en pantalla.\n")

        for idx, job in enumerate(jobs, 1):
            if storage.is_job_seen(job.job_id):
                console.print(f"[dim]Oferta ya vista: {job.title} ({job.company}). Omitiendo...[/dim]")
                continue

            console.print(f"[cyan]Evaluando ({idx}/{len(jobs)}): {job.title} - {job.company}...[/cyan]")
            evaluation = evaluator.evaluate_job(job.title, job.company, job.full_description)

            storage.record_job_evaluation(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                score=evaluation.fit_score,
                recommendation=evaluation.recommendation,
                reason=evaluation.summary_reason
            )

            print_job_card(evaluation, idx, len(jobs))

            should_apply = False
            if evaluation.recommendation == "APPLY" and evaluation.fit_score >= criteria.get("min_fit_score", 75):
                if args.mode == "auto":
                    console.print("[bold green]Modo automático: procediendo a postularse...[/bold green]")
                    should_apply = True
                elif args.mode == "interactive":
                    choice = ask_user_confirmation()
                    if choice == "q":
                        console.print("[yellow]Ejecución detenida por el usuario.[/yellow]")
                        break
                    elif choice in ("s", ""):
                        should_apply = True
                    else:
                        storage.mark_as_rejected(job.job_id, "Rechazado por el usuario en modo interactivo")
                elif args.mode == "dry-run":
                    console.print("[yellow][DRY-RUN] No se ejecuta clic de postulación.[/yellow]")

            if should_apply:
                success, msg = await scraper.click_apply_button(page)
                if success:
                    storage.mark_as_applied(job.job_id)
                    console.print(f"[bold green]✓ {msg}[/bold green]")
                else:
                    console.print(f"[bold red]✗ {msg}[/bold red]")

            await connector.human_delay(1.5, 3.0)

    except ConnectionError as e:
        console.print(f"[bold red]{e}[/bold red]")
    finally:
        await connector.close()
        console.print("\n[bold cyan]Sesión finalizada. Historial actualizado en SQLite.[/bold cyan]")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
