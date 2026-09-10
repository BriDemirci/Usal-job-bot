import pytest
from main import parse_args
from src.ui import print_welcome, print_job_card
from src.evaluator import JobEvaluation

def test_default_args():
    args = parse_args([])
    assert args.mode == "interactive"
    assert args.cdp_url == "http://localhost:9222"

def test_custom_flags():
    args = parse_args(["--auto", "--cdp-url", "http://localhost:9333"])
    assert args.mode == "auto"
    assert args.cdp_url == "http://localhost:9333"

def test_dry_run_flag():
    args = parse_args(["--dry-run"])
    assert args.mode == "dry-run"

def test_ui_components_render():
    print_welcome()
    eval_mock = JobEvaluation(
        job_title="Desarrollador Junior",
        company="Banco USAL",
        fit_score=90,
        recommendation="APPLY",
        matching_skills=["Python"],
        missing_skills=[],
        pros=["Excelente salario"],
        cons=[],
        summary_reason="Gran oportunidad"
    )
    print_job_card(eval_mock, 1, 5)
