# 📊 Proyecto EDA: Análisis Exploratorio de Datos

¡Bienvenido al repositorio del proyecto **ai_project_EDA**! 

Este proyecto simula un caso real de consultoría de datos donde se realiza un **Análisis Exploratorio de Datos (EDA)** exhaustivo sobre un dataset del mundo real. El objetivo no es únicamente procesar y limpiar datos, sino descubrir la historia oculta tras ellos y transformar números en **información estratégica y accionable**, comunicada mediante visualizaciones claras y un informe ejecutivo orientado a la toma de decisiones.

> 📌 **Nota sobre la guía docente:** La especificación y pautas académicas originales se encuentran intactas en el archivo [`docs/Briefing.md`](docs/Briefing.md).

---

## ⚙️ Entorno de Ejecución

Para garantizar la reproducibilidad completa del análisis, el proyecto utiliza un entorno virtual de Python aislado:

* **Nombre del entorno:** `EDA`
* **Versión de Python:** `Python 3.12` (específicamente `3.12.10` / rama `3.12.x`)

### 🔌 Activación del entorno virtual

Antes de ejecutar o instalar cualquier librería, asegúrate de activar el entorno según tu sistema operativo y terminal:

#### En Windows:
* **PowerShell:**
  ```powershell
  .\EDA\Scripts\Activate.ps1
  ```
  *(Si el sistema bloquea la ejecución de scripts, puedes habilitarla temporalmente con: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`)*

* **Símbolo del sistema (CMD):**
  ```cmd
  .\EDA\Scripts\activate.bat
  ```

#### En Linux / macOS (si aplica):
```bash
source EDA/bin/activate
```

Una vez activado, verás el prefijo `(EDA)` al inicio de tu línea de comandos.

### 📦 Dependencias
Para instalar las librerías necesarias del proyecto (una vez activado el entorno):
```bash
pip install -r requirements.txt
```

---

## 🔀 Flujo de Trabajo: GitHub Flow Adaptado

Para este proyecto adoptamos **GitHub Flow**, un modelo de ramas ágil, limpio y centrado en la revisión continua. Dado que el desarrollo lo realiza un **único autor** pero existe un **profesor revisor**, el modelo oficial *GitFlow* (con ramas `develop`, `release` y `hotfix`) generaría una sobrecarga burocrática innecesaria (*matar pulgas a cañonazos*).

### 📐 Principios de la estrategia

1. **Rama `main` siempre estable:** Contiene código probado, limpio y reproducible. Nunca se trabaja directamente sobre `main`.
2. **Ramas de etapa (Feature Branches):** Se crea una rama específica para cada hito del análisis exploratorio (ej. limpieza de datos, análisis univariado/bivariado, ingeniería de variables, informe ejecutivo).
3. **Revisión por Pull Request (PR):** Toda integración hacia `main` se realiza mediante un Pull Request en GitHub utilizando la plantilla oficial, permitiendo al profesor revisar el avance, comentar el código y evaluar el trabajo.
4. **⚠️ Conservación de Ramas (Regla académica):** A diferencia del GitHub Flow estándar donde las ramas se eliminan tras el merge, **en este proyecto las ramas remotas NO se eliminan tras fusionarse en `main`**. Se conservan en GitHub como evidencia histórica y trazabilidad del proceso de aprendizaje para el profesor.

---

### 💻 Ciclo de trabajo con comandos de Git

#### 1. Partir siempre de `main` actualizado
```bash
git checkout main
git pull origin main
```

#### 2. Crear y cambiar a la rama de la etapa correspondiente
Nombra tus ramas con prefijos descriptivos de la fase en curso:
```bash
# Ejemplos de ramas por etapa:
git checkout -b feature/01-data-cleaning
# git checkout -b feature/02-univariate-bivariate-analysis
# git checkout -b feature/03-feature-engineering
# git checkout -b feature/04-visualizations-insights
```

#### 3. Realizar cambios y commitear con mensajes claros
```bash
git status
git add .
git commit -m "feat(cleaning): imputar valores nulos y estandarizar formatos de fecha"
```

#### 4. Publicar la rama en el repositorio remoto de GitHub
```bash
git push -u origin feature/01-data-cleaning
```

#### 5. Abrir Pull Request en GitHub
1. Ve a la pestaña **Pull Requests** en GitHub y haz clic en **New Pull Request**.
2. Selecciona `base: main` $\leftarrow$ `compare: feature/01-data-cleaning`.
3. Completa la plantilla de PR que se cargará automáticamente explicando los cambios y las conclusiones parciales.
4. Notifica o solicita revisión al profesor.

#### 6. Integración (Merge) y continuidad
Una vez aprobado el Pull Request:
* Realiza el merge hacia `main`.
* **NO marques la opción de borrar la rama** ("Delete branch").
* En tu entorno local, vuelve a `main` para preparar la siguiente fase:
  ```bash
  git checkout main
  git pull origin main
  git checkout -b feature/02-univariate-bivariate-analysis
  ```

---

## 📂 Estructura del Proyecto

```text
ai_project_EDA_Levi_Flores/
│
├── .github/                      # Automatización y gestión de GitHub
│   ├── ISSUE_TEMPLATE/           # Plantillas guiadas para tickets y tareas
│   ├── workflows/                # Acciones automatizadas de CI (pruebas, linting, notebooks)
│   └── pull_request_template.md  # Plantilla de entrega y revisión de Pull Requests
│
├── assets/                       # Recursos multimedia, logos y gráficos exportados
│   └── minidatathon.PNG          # Banner/recurso visual del proyecto
│
├── docs/                         # Documentación de referencia
│   └── Briefing.md               # Guía académica original del profesor (INALTERADA)
│
├── EDA/                          # Entorno virtual aislado de Python (ignorado en Git)
│
├── .gitignore                    # Reglas de exclusión para Git (temporales, caches, entorno)
└── README.md                     # Documentación principal del proyecto
```
