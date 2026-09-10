# USAL Job Bot 🎓🤖

Bot inteligente de búsqueda y postulación laboral para el portal de empleo de la **Universidad del Salvador (USAL)**.

---

## 🌟 Características
- 🚀 **Conexión a Chrome con sesión activa:** Utiliza tu navegador Chrome o Edge habitual con login institucional mediante Chrome DevTools Protocol (puerto `9222`), sin lidiar con captchas ni bloqueos.
- 🧠 **Evaluación con Gemini (LLM):** Analiza la descripción completa de cada vacante contra tu CV (`config/profile.json`) y tus reglas de corte (`config/criteria.json`).
- 🛡️ **Seguridad interactiva (Human-in-the-loop):** Muestra tarjetas visuales estilizadas en consola y pide confirmación `[S/n]` antes de hacer clic en postular.
- ⚡ **Modo Automático:** Flag `--auto` para postularte sin pausa a las vacantes que superen el puntaje configurado.
- 🔍 **Modo Dry-Run:** Flag `--dry-run` para auditar y ver los scores sin hacer clics reales.
- 💾 **Historial en SQLite (`data/job_history.db`):** Evita repetir postulaciones o analizar ofertas ya vistas en ejecuciones previas.

---

## 🛠️ Requisitos Previos
- Python 3.10+
- Google Chrome instalado
- Clave de API de Google Gemini ([Google AI Studio](https://aistudio.google.com/))

---

## 🚀 Guía de Inicio Rápido

### 1. Configurar el Entorno
Dentro de la carpeta `usal-job-bot`:
```bash
# Instalar dependencias
pip install -r requirements.txt

# Crear tu archivo .env
copy .env.example .env
```
Abre `.env` y coloca tu API Key:
```env
GEMINI_API_KEY=tu_clave_de_gemini_aqui
CDP_URL=http://localhost:9222
MIN_FIT_SCORE=75
```

### 2. Personalizar tu Perfil y Criterios
- Edita `config/profile.json` con tus datos, carrera, tecnologías y resumen de CV.
- Edita `config/criteria.json` con tus palabras clave, exclusiones y umbral de puntaje mínimo deseado.

### 3. Abrir Chrome en Modo Depuración
1. Cierra las ventanas normales de Chrome que tengas abiertas.
2. Haz doble clic en `launch_chrome.bat` (o ejecuta `.\launch_chrome.bat` en la terminal).
3. En esa ventana de Chrome, ingresa al portal de empleo de la USAL, inicia sesión normalmente con tus credenciales y ve a la página de ofertas de empleo.

### 4. Ejecutar el Bot

#### Modo Interactivo (Recomendado para empezar):
```bash
python main.py
```
El bot revisará cada vacante, te mostrará una tarjeta con los pros, contras y score, y te preguntará:
`¿Deseas postularte a esta oferta? [S/n/q]:`

#### Modo Auditoría (Sin hacer clic en postularse):
```bash
python main.py --dry-run
```

#### Modo 100% Automático:
```bash
python main.py --auto
```

---

## 🧪 Ejecutar Tests
```bash
pytest tests/ -v
```
