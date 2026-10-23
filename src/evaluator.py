import json
import time
import re
import warnings
from typing import List, Literal, Dict, Any, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Silenciar advertencias internas de la libreria google-genai para mantener limpia la consola
warnings.filterwarnings("ignore", category=UserWarning)

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
    def __init__(self, api_key: str, profile: Dict[str, Any], criteria: Dict[str, Any], model_name: str = "gemini-3.5-flash-lite"):
        self.api_key = api_key
        self.profile = profile
        self.criteria = criteria
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)

    def should_prefilter_skip(self, title: str) -> Optional[str]:
        """Verifica rápidamente si el título de la oferta coincide con alguna disciplina descartada."""
        title_lower = title.lower()
        excluded_disciplines = self.criteria.get("excluded_disciplines", [])
        for disc in excluded_disciplines:
            pattern = rf"\b{re.escape(disc.lower())}"
            if re.search(pattern, title_lower):
                return f"Disciplina no afín: '{disc}'"
        return None

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

--- INSTRUCCIONES ESPECÍFICAS DE EVALUACIÓN ---
1. REGLA CLAVE DE EXPERIENCIA: El candidato BUSCA SU PRIMER EMPLEO O PASANTÍA (SIN EXPERIENCIA LABORAL PREVIA).
   - Si la oferta es para pasantías, trainee, junior inicial, estudiantes universitarios o requisitos accesibles y aprendibles, dale un puntaje ELEVADO (>= 75 u 80).
   - Si la oferta dice 'sin experiencia', 'estudiante' o pide hasta 1 año pero las tareas son alcanzables en el rubro, recomienda "APPLY".
   - SOLO recomienda "SKIP" por experiencia si la vacante exige de forma excluyente 2 o más años de experiencia previa comprobable, o niveles Semi-Senior / Senior / Lead.
2. ABANICO AMPLIO DE ROLES Y SINÓNIMOS:
   - Sé flexible con la denominación del puesto: Desarrollador (Cualquier lenguaje/stack), Soporte Técnico, Mesa de Ayuda, Help Desk, QA / Testing, Analista Funcional Junior, Analista de Procesos, Analista de Datos / BI / SQL, Operador de Sistemas, Asistente IT, Consultor Jr de Software, etc. Todos son afines y muy deseables.
   - NO penalices severamente si la empresa usa herramientas propietarias o frameworks específicos secundarios, ya que el candidato tiene gran facilidad y disposición para aprender rápido.
3. Asigna un `fit_score` numérico entre 0 y 100 ponderando la accesibilidad del puesto y el potencial de aprendizaje.
4. Si el score es mayor o igual a {self.criteria.get('min_fit_score', 65)} y la vacante es una oportunidad razonable de inserción laboral o pasantía, recomienda "APPLY", de lo contrario "SKIP".
5. Extrae habilidades coincidentes, faltantes, pros, contras y un resumen claro de 1 a 2 oraciones.
Responde estrictamente en formato JSON según el esquema solicitado.
"""

    def evaluate_job(self, title: str, company: str, description: str, max_retries: int = 3) -> JobEvaluation:
        prompt = self._build_prompt(title, company, description)
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=JobEvaluation,
                        temperature=0.2
                    )
                )
                data = json.loads(response.text)
                return JobEvaluation(**data)
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str
                if is_rate_limit and attempt < max_retries:
                    wait_time = 20 * attempt
                    print(f"\n[Aviso Cuota] Límite por minuto alcanzado. Pausando {wait_time}s antes de reintentar (intento {attempt}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    raise e
