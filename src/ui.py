from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from src.evaluator import JobEvaluation

console = Console()

def print_welcome():
    console.print(Panel.fit(
        "[bold cyan]USAL Job Automation Bot[/bold cyan]\n"
        "[dim]Navegación inteligente y postulación automatizada[/dim]",
        border_style="cyan"
    ))

def print_job_card(eval_res: JobEvaluation, index: int, total: int):
    score_color = "green" if eval_res.fit_score >= 75 else ("yellow" if eval_res.fit_score >= 50 else "red")
    
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_row("[bold]Puesto:[/bold]", eval_res.job_title)
    table.add_row("[bold]Empresa:[/bold]", eval_res.company)
    table.add_row("[bold]Score:[/bold]", f"[{score_color}]{eval_res.fit_score}/100[/{score_color}]")
    table.add_row("[bold]Recomendación:[/bold]", f"[bold {score_color}]{eval_res.recommendation}[/bold {score_color}]")
    if eval_res.matching_skills:
        table.add_row("[bold]Puntos a favor:[/bold]", ", ".join(eval_res.matching_skills))
    if eval_res.missing_skills:
        table.add_row("[bold]Requisitos faltantes:[/bold]", ", ".join(eval_res.missing_skills))
    table.add_row("[bold]Motivo:[/bold]", eval_res.summary_reason)

    console.print(Panel(
        table,
        title=f"[bold]Oferta {index}/{total}[/bold]",
        border_style=score_color
    ))

def ask_user_confirmation() -> str:
    console.print("\n[bold yellow]¿Deseas postularte a esta oferta?[/bold yellow]")
    choice = input("  [S] Sí / [n] No / [q] Salir: ").strip().lower()
    return choice

def print_pending_approved_table(jobs: list):
    """Muestra una tabla elegante con las vacantes aprobadas pendientes."""
    table = Table(title="[bold green]Vacantes Aprobadas Listas para Postulación[/bold green]", border_style="cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Puesto", style="bold white")
    table.add_column("Score", justify="center", style="bold green", width=8)
    table.add_column("Análisis IA", style="dim cyan")

    for i, j in enumerate(jobs, 1):
        reason = j.get("reason", "") or ""
        short_reason = (reason[:55] + "...") if len(reason) > 55 else reason
        table.add_row(str(i), j["title"], f"{j['fit_score']}/100", short_reason)
    console.print(table)

def ask_batch_confirmation(count: int) -> bool:
    console.print(f"\n[bold yellow]¿Deseas postularte automáticamente a estas {count} ofertas aprobadas?[/bold yellow]")
    choice = input("  [S] Sí, postularme a todas / [n] Cancelar: ").strip().lower()
    return choice in ("s", "", "y", "si", "sí")

