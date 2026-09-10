import json
from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

class JobEvaluation(BaseModel):
    job_title: str
    company: str
    fit_score: int = Field(ge=0, le=100, description="Puntaje de 0 a 100 de compatibilidad")
    recommendation: Literal["APPLY", "SKIP"]
    matching_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    summary_reason: str

class JobEvaluator:
    def __init__(self, api_key: str, profile: Dict[str, Any], criteria: Dict[str, Any]):
        self.api_key = api_key
        self.profile = profile
        self.criteria = criteria
        self.client = genai.Client(api_key=self.api_key)

    def _build_prompt(self, title: str, company: str, description: str) -> str:
        return f"""
Actúa como un asesor de carreras y reclutador técnico experto.
Tu objetivo es analizar la siguiente oferta de trabajo del portal universitario USAL y determinar si el candidato debe postularse.

--- PERFIL DEL CANDIDATO ---
{json.dumps(self.profile, indent=2, ensure_ascii=False)}

--- CRITERIOS Y PREFERENCIAS ---
{json.dumps(self.criteria, indent=2, ensure_ascii=False)}

--- OFERTA DE EMPLEO A EVALUAR ---
Puesto: {title}
Empresa: {company}
Descripción completa y requisitos:
{description}

--- INSTRUCCIONES ---
1. Revisa si el puesto requiere un seniority inalcanzable (ej: Senior, Lead) o tecnologías incompatibles.
2. Compara los requisitos con las habilidades y carrera del candidato.
3. Asigna un `fit_score` numérico entre 0 y 100.
4. Si el score es mayor o igual a {self.criteria.get('min_fit_score', 75)} y el perfil es apto, recomienda "APPLY", de lo contrario "SKIP".
5. Extrae habilidades coincidentes, faltantes, pros, contras y un resumen claro de 1 a 2 oraciones.
Responde estrictamente en formato JSON según el esquema solicitado.
"""

    def evaluate_job(self, title: str, company: str, description: str) -> JobEvaluation:
        prompt = self._build_prompt(title, company, description)
        response = self.client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=JobEvaluation,
                temperature=0.2
            )
        )
        data = json.loads(response.text)
        return JobEvaluation(**data)
