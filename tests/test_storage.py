import pytest
from pathlib import Path
from src.storage import StorageRepository

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_jobs.db"
    repo = StorageRepository(db_path=db_file)
    repo.init_db()
    return repo

def test_init_and_empty_check(temp_db):
    assert temp_db.is_job_seen("job-123") is False
    assert temp_db.get_applied_jobs_count() == 0

def test_record_and_check_job(temp_db):
    temp_db.record_job_evaluation(
        job_id="job-123",
        title="Desarrollador Junior",
        company="Tech Corp",
        score=85,
        recommendation="APPLY",
        reason="Buen perfil técnico"
    )
    assert temp_db.is_job_seen("job-123") is True
    assert temp_db.get_applied_jobs_count() == 0

def test_mark_as_applied(temp_db):
    temp_db.record_job_evaluation(
        job_id="job-456",
        title="Pasantía Sistemas",
        company="Banco USAL",
        score=90,
        recommendation="APPLY",
        reason="Pasantía universitaria ideal"
    )
    temp_db.mark_as_applied("job-456")
    assert temp_db.get_applied_jobs_count() == 1

def test_mark_as_rejected(temp_db):
    temp_db.record_job_evaluation(
        job_id="job-789",
        title="Soporte Técnico",
        company="Global IT",
        score=60,
        recommendation="SKIP",
        reason="No coincide con intereses actuales"
    )
    temp_db.mark_as_rejected("job-789", "Descartado manualmente")
    assert temp_db.is_job_seen("job-789") is True
    assert temp_db.get_applied_jobs_count() == 0
