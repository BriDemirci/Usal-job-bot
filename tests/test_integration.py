import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.evaluator import JobEvaluation
from src.scraper import JobListing
from src.storage import StorageRepository

def test_full_pipeline_mock(tmp_path):
    # Validar que almacenamiento + evaluación estructurada procesan y guardan correctamente
    db_file = tmp_path / "integration_history.db"
    storage = StorageRepository(db_file)
    storage.init_db()

    job = JobListing(
        job_id="test-job-int",
        title="Desarrollador Trainee",
        company="USAL Tech",
        summary="Oportunidad inicial",
        full_description="Buscamos trainee para aprender Python."
    )

    eval_mock = JobEvaluation(
        job_title=job.title,
        company=job.company,
        fit_score=88,
        recommendation="APPLY",
        matching_skills=["Python"],
        missing_skills=[],
        pros=["Excelente para aprender"],
        cons=[],
        summary_reason="Ideal para perfil trainee."
    )

    storage.record_job_evaluation(
        job_id=job.job_id,
        title=job.title,
        company=job.company,
        score=eval_mock.fit_score,
        recommendation=eval_mock.recommendation,
        reason=eval_mock.summary_reason
    )
    assert storage.is_job_seen(job.job_id) is True

    storage.mark_as_applied(job.job_id)
    assert storage.get_applied_jobs_count() == 1
