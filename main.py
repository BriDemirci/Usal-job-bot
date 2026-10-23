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
from src.ui import (
    console,
    print_welcome,
    print_job_card,
    ask_user_confirmation,
    print_pending_approved_table,
    ask_batch_confirmation
)

def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Bot de búsqueda y postulación en portal USAL")
    parser.add_argument("--auto", action="store_const", const="auto", dest="mode", help="Modo 100% automático")
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="mode", help="Auditoría sin postular")
    parser.add_argument("--apply-approved", action="store_true", help="Postular directamente a las vacantes ya aprobadas")
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

    scraper = PortalScraper()

    # Si hay ofertas previamente aprobadas en el Dry Run y el usuario no está en dry-run
    pending_approved = storage.get_pending_approved_jobs()
    if pending_approved and (args.apply_approved or args.mode != "dry-run"):
        console.print(f"\n[bold green]Se encontraron {len(pending_approved)} vacantes previamente aprobadas listas para postulación.[/bold green]")
        print_pending_approved_table(pending_approved)

        should_run_batch = False
        if args.mode == "auto" or args.apply_approved:
            should_run_batch = True
        else:
            should_run_batch = ask_batch_confirmation(len(pending_approved))

        if should_run_batch:
            connector = ChromeConnector(cdp_url=args.cdp_url)
            try:
                console.print(f"\n[cyan]Conectando a Chrome en {args.cdp_url}...[/cyan]")
                page = await connector.connect()
                console.print(f"[bold cyan]Iniciando postulación automática a {len(pending_approved)} ofertas...[/bold cyan]\n")

                applied_count = 0
                for idx, job in enumerate(pending_approved, 1):
                    console.print(f"[cyan]Postulando ({idx}/{len(pending_approved)}):[/cyan] [bold]{job['title']}[/bold] (Score: {job['fit_score']})...")
                    success, msg = await scraper.apply_to_offer_by_id(page, job["job_id"])
                    if success:
                        storage.mark_as_applied(job["job_id"])
                        applied_count += 1
                        console.print(f"  [bold green]✓ {msg}[/bold green]")
                    else:
                        console.print(f"  [bold red]✗ {msg}[/bold red]")
                    await connector.human_delay(2.0, 3.5)

                await page.reload()
                console.print(f"\n[bold green]✓ ¡Lote finalizado! Se postularon {applied_count}/{len(pending_approved)} vacantes exitosamente.[/bold green]")
            except ConnectionError as e:
                console.print(f"[bold red]{e}[/bold red]")
            finally:
                await connector.close()
                console.print("[bold cyan]Historial actualizado en SQLite.[/bold cyan]")
            return

    evaluator = JobEvaluator(api_key=api_key, profile=profile, criteria=criteria)
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
                console.print(f"[dim]Oferta ya vista ({idx}/{len(jobs)}): {job.title} ({job.company}). Omitiendo...[/dim]")
                continue

            if getattr(job, "already_applied", False):
                console.print(f"[bold green]Ya postulaste previamente ({idx}/{len(jobs)}):[/bold green] {job.title} ({job.company}). Registrando...")
                storage.record_job_evaluation(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    score=100,
                    recommendation="APPLY",
                    reason="Postulación existente detectada en el portal"
                )
                storage.mark_as_applied(job.job_id)
                continue

            prefilter_reason = evaluator.should_prefilter_skip(job.title)
            if prefilter_reason:
                console.print(f"[dim]Omitida por pre-filtro ({idx}/{len(jobs)}): {job.title} - {prefilter_reason}[/dim]")
                storage.record_job_evaluation(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    score=15,
                    recommendation="SKIP",
                    reason=prefilter_reason
                )
                continue

            console.print(f"[cyan]Evaluando con Gemini ({idx}/{len(jobs)}): {job.title} - {job.company}...[/cyan]")
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
            if evaluation.recommendation == "APPLY" and evaluation.fit_score >= criteria.get("min_fit_score", 65):
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

            await connector.human_delay(3.5, 5.0)

    except ConnectionError as e:
        console.print(f"[bold red]{e}[/bold red]")
    finally:
        await connector.close()
        console.print("\n[bold cyan]Sesión finalizada. Historial actualizado en SQLite.[/bold cyan]")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
