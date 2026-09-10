import pytest
from unittest.mock import MagicMock, patch
from src.evaluator import JobEvaluator, JobEvaluation

@pytest.fixture
def mock_profile():
    return {
        "full_name": "Estudiante Test",
        "career": "Sistemas",
        "skills": ["Python", "SQL"],
        "cv_summary": "Estudiante junior de programación."
    }

@pytest.fixture
def mock_criteria():
    return {
        "min_fit_score": 70,
        "target_roles": ["Desarrollador", "Junior"],
        "excluded_keywords": ["Senior"]
    }

def test_job_evaluation_schema():
    eval_res = JobEvaluation(
        job_title="Desarrollador Python Junior",
        company="Tech Corp",
        fit_score=85,
        recommendation="APPLY",
        matching_skills=["Python", "SQL"],
        missing_skills=[],
        pros=["Excelente ambiente"],
        cons=[],
        summary_reason="Coincide con perfil"
    )
    assert eval_res.fit_score == 85
    assert eval_res.recommendation == "APPLY"

def test_evaluator_structured_response(mock_profile, mock_criteria):
    mock_response = MagicMock()
    mock_response.text = '''{
        "job_title": "Desarrollador Python Junior",
        "company": "Empresa Mock",
        "fit_score": 85,
        "recommendation": "APPLY",
        "matching_skills": ["Python", "SQL"],
        "missing_skills": ["Docker"],
        "pros": ["Aceptan estudiantes"],
        "cons": ["Requiere presencialidad un día"],
        "summary_reason": "Se ajusta perfectamente a tus habilidades en Python."
    }'''

    with patch("src.evaluator.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.models.generate_content.return_value = mock_response

        evaluator = JobEvaluator(
            api_key="test-key",
            profile=mock_profile,
            criteria=mock_criteria
        )

        result = evaluator.evaluate_job(
            title="Desarrollador Python Junior",
            company="Empresa Mock",
            description="Buscamos estudiante de sistemas con conocimientos en Python y SQL."
        )

        assert isinstance(result, JobEvaluation)
        assert result.fit_score == 85
        assert result.recommendation == "APPLY"
        assert "Python" in result.matching_skills
        assert "SQL" in result.matching_skills
