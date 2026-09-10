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
