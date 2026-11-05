# 🗺️ Plan de Trabajo — Proyecto EDA

Documento de referencia para las siguientes sesiones. Resume **qué se hace**, **en qué orden** y **en qué rama**, con un único colaborador y una profesora que revisa cada Pull Request.

- **Proyecto:** EDA sobre datos de clientes con calidad deficiente.
- **Plazo:** 1 semana (6–7 sesiones de trabajo + margen de buffer).
- **Fuente de verdad del alcance:** [`docs/Briefing.md`](Briefing.md).

---

## 1. Dataset

| Elemento | Definición |
|---|---|
| Fuente principal | Kaggle — **"Customer Messy Data"** |
| Archivo | `messy_customer_data.csv` |
| Ubicación local | `data/raw/messy_customer_data.csv` (sin modificar) |
| Datos derivados | `data/processed/` (generados por el pipeline, nunca editados a mano) |
| Motivación | Cumple los requisitos del briefing: volumen suficiente, mezcla de variables numéricas, categóricas y de fecha, y datos sucios reales (nulos, duplicados, formatos inconsistentes). |

**Reglas de uso**

1. El CSV original es de solo lectura: toda limpieza se aplica en el notebook o en el pipeline y se guarda como nuevo archivo.
2. Registrar en el `README.md` el enlace al dataset, la fecha de descarga y la licencia/atribución.
3. No subir el CSV al repositorio si su tamaño o licencia no lo permiten; en ese caso, documentar la descarga y dejar el archivo en `.gitignore`.

---

## 2. Reparto de tareas

Tareas secuenciales, agrupadas por nivel. Cada tarea termina en un commit (o varios) dentro de su rama y en un PR revisable. La columna **Salida** indica el artefacto que debe existir al cerrarla.

### 🟢 Nivel Esencial

| # | Tarea | Descripción | Salida |
|---|---|---|---|
| E1 | Carga e inspección inicial | Descargar el CSV, cargarlo con pandas y revisar `shape`, `info()`, `head()`, `describe()`. Anotar las **3 preguntas de negocio** que guiarán el análisis. | Notebook `01_eda_clientes.ipynb` con sección de contexto y preguntas. |
| E2 | Diagnóstico de calidad | Cuantificar nulos y duplicados por columna; decidir y documentar qué se elimina, imputa o conserva. | Tabla de decisiones de limpieza en el notebook. |
| E3 | Corrección de tipos y columnas | Convertir fechas y numéricos mal tipados, normalizar texto, renombrar columnas a `snake_case` y eliminar las que no aporten. | Bloque de limpieza ejecutado sin errores. |
| E4 | Análisis univariado | Al menos 3 variables (histograma, conteo y boxplot) con título, ejes y lectura interpretativa. | ≥3 visualizaciones comentadas. |
| E5 | Análisis bivariado | Al menos 3 relaciones entre pares de variables (numérica–numérica, categórica–numérica, etc.). | ≥3 visualizaciones + interpretación. |
| E6 | Respuestas y cierre del esencial | Responder por escrito las 3 preguntas iniciales; verificar que el notebook se ejecuta de arriba abajo. | Notebook reproducible y conclusiones preliminares. |

### 🟡 Nivel Medio

| # | Tarea | Descripción | Salida |
|---|---|---|---|
| M1 | Justificación de la limpieza | Documentar el *porqué* de cada decisión (criterio de imputación, columnas descartadas, tratamiento de duplicados). | Sección "Decisiones de limpieza" con criterio explícito. |
| M2 | Valores atípicos | Detectar outliers con boxplots e IQR; decidir si se eliminan, acotan o mantienen y justificarlo. | Análisis de outliers + regla aplicada. |
| M3 | Agregaciones | Resumir con `groupby`, `agg` y `pivot_table` por los segmentos relevantes del dataset. | Tablas resumen interpretadas. |
| M4 | Feature engineering | Crear al menos 3 variables nuevas (rangos, ratios, partes de fecha, porcentajes) y explicar su utilidad. | Variables derivadas y su lectura. |
| M5 | Correlación | Matriz de correlación con heatmap, selección de variables y interpretación de relaciones (sin confundir correlación con causalidad). | Heatmap + conclusiones. |
| M6 | Evolución temporal | Si hay fechas: tendencias con gráficos de líneas. Si no: comparación de comportamiento entre grupos. | 1–2 gráficos de tendencia/comparación. |
| M7 | Informe ejecutivo | Documento de 1–2 páginas para el CEO, con conclusiones claras respaldadas por los gráficos clave. | `reports/informe_ejecutivo.md` (o PDF). |

### 🟠 Nivel Avanzado

| # | Tarea | Descripción | Salida |
|---|---|---|---|
| A1 | Normalización | Comparar con justicia usando ratios, porcentajes o valores por cada 100/1.000 unidades en lugar de totales. | Métricas normalizadas + gráficos comparables. |
| A2 | Segunda fuente de datos | Incorporar una fuente auxiliar pública (catálogo de países/regiones o calendario) y enriquecer con `merge`. | Merge documentado y validado. |
| A3 | Calidad dudosa | Detectar valores imposibles, correcciones e inconsistencias entre columnas; documentar el tratamiento. | Registro de incidencias y reglas aplicadas. |
| A4 | Transformación justificada | Aplicar y explicar una transformación: escala logarítmica para distribuciones sesgadas, escalado o media móvil si hay serie temporal. | Antes/después comentado. |
| A5 | Comparación de segmentos | Visualizar diferencias entre grupos/regiones/periodos con gráficos claros. | Comparativa por segmento. |
| A6 | Gráficos interactivos | Añadir al menos un gráfico con `plotly` que aporte valor exploratorio. | Visual interactiva exportada al notebook. |
| A7 | Código reutilizable | Extraer la limpieza repetida a funciones o a un módulo `.py` documentado. | `src/cleaning.py` (o similar) usado por el notebook. |

### 🔴 Nivel Experto

| # | Tarea | Descripción | Salida |
|---|---|---|---|
| X1 | Pipeline reproducible | Script único que descarga/carga, limpia y guarda el dataset procesado; ejecutable con un comando. | `python -m src.pipeline` → CSV en `data/processed/`. |
| X2 | Dashboard interactivo | App en Streamlit con filtros para que el CEO explore los datos sin tocar código. | `app/dashboard.py` funcional en local. |
| X3 | Tests | Tests de `pytest` para las funciones de limpieza, escritos **antes** de la implementación (TDD). | `tests/test_cleaning.py` en verde. |
| X4 | Informe de calidad | Resumen de qué faltaba, qué se corrigió, qué quedó pendiente y por qué. | `reports/calidad_datos.md`. |
| X5 | Presentación | Guion de 5 minutos con storytelling para público no técnico, apoyado en 3–4 gráficos. | `reports/presentacion.md` + diapositivas. |
| X6 | Publicación y cierre | Publicar dashboard o informe en un enlace accesible; actualizar README y `requirements.txt` con todo lo nuevo. | Enlace público + documentación final. |

### Orden y tiempo estimado

| Sesión | Contenido | Nivel |
|---|---|---|
| 1 | E1–E3 | Esencial |
| 2 | E4–E6 | Esencial |
| 3 | M1–M4 | Medio |
| 4 | M5–M7 | Medio |
| 5 | A1–A3 | Avanzado |
| 6 | A4–A7 | Avanzado |
| 7 | X1–X6 | Experto |

> Regla de avance: **no se abre la rama del nivel siguiente hasta que el PR del nivel actual esté fusionado**. Es preferible un nivel bien cerrado que dos a medias.

---

## 3. Plan de ramas (GitHub Flow simplificado)

### Reglas del modelo

1. **`main` protegida:** siempre estable y ejecutable. Nunca se commitea directamente; solo recibe merges vía PR.
2. **Ramas cortas:** una por nivel o feature, con vida máxima de 1–2 sesiones.
3. **Pull Request obligatorio:** base `main` ← rama de trabajo, usando la plantilla del repositorio y solicitando revisión de la profesora.
4. **Squash merge:** un único commit limpio por PR en `main`, con mensaje en formato Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`).
5. **Borrado de rama:** tras fusionar, se elimina la rama remota y la local. El historial queda en `main` y en el PR.
6. **CI en verde** antes de pedir revisión; el notebook debe ejecutarse de arriba abajo.
7. **Definición de hecho (DoD):** PR aprobado por la profesora + CI verde + documentación actualizada + rama borrada.

> Nota: el borrado de ramas sustituye la regla anterior del `README.md` (conservarlas). El flujo definitivo se reflejará en el README dentro de la rama `feature/01-data-loading-and-inspection`.

### Ramas y orden de creación

| Orden | Rama | Propósito | Tareas |
|---|---|---|---|
| 0 | `feature/work-plan` | Redactar y revisar este plan de trabajo. | — |
| 1 | `feature/01-data-loading-and-inspection` | Carga del dataset, inspección inicial y preguntas de negocio; actualizar README con el flujo de ramas definitivo. | E1 |
| 2 | `feature/02-data-cleaning` | Diagnóstico, limpieza, tipos y columnas. | E2–E3 |
| 3 | `feature/03-univariate-bivariate-analysis` | Análisis univariado y bivariado con visualizaciones. | E4–E5 |
| 4 | `feature/04-essential-insights` | Respuestas a las preguntas y cierre del nivel esencial. | E6 |
| 5 | `feature/05-outliers-and-feature-engineering` | Justificación de limpieza, outliers, agregaciones y nuevas variables. | M1–M4 |
| 6 | `feature/06-correlation-and-trends` | Correlación y evolución temporal o comparación entre grupos. | M5–M6 |
| 7 | `feature/07-executive-report` | Informe ejecutivo de 1–2 páginas. | M7 |
| 8 | `feature/08-normalization-and-enrichment` | Normalización, segunda fuente y análisis de calidad dudosa. | A1–A3 |
| 9 | `feature/09-transformations-and-interactive` | Transformación justificada, comparación de segmentos, plotly y refactor a funciones. | A4–A7 |
| 10 | `feature/10-reproducible-pipeline` | Pipeline de un solo comando. | X1 |
| 11 | `feature/11-dashboard` | Dashboard interactivo en Streamlit. | X2 |
| 12 | `feature/12-tests-and-quality-report` | Tests con `pytest` e informe de calidad. | X3–X4 |
| 13 | `feature/13-presentation-and-release` | Presentación, publicación del enlace y cierre documental. | X5–X6 |

### Ciclo de trabajo por rama

```bash
# 1. Partir de main actualizada
git checkout main
git pull origin main

# 2. Crear la rama del siguiente bloque
git checkout -b feature/02-data-cleaning

# 3. Trabajar con commits pequeños y claros
git add .
git commit -m "feat(cleaning): normalizar tipos y documentar nulos"

# 4. Publicar y abrir PR
git push -u origin feature/02-data-cleaning
```

5. Completar la plantilla del PR (qué se hizo, hallazgos, cómo revisarlo) y asignar a la profesora.
6. Tras la aprobación: **Squash and merge** → **Delete branch**.
7. Actualizar el entorno local:

```bash
git checkout main
git pull origin main
git branch -d feature/02-data-cleaning
```

---

## 4. Checklist rápido antes de cada PR

- [ ] La rama sale de `main` actualizada y tiene un nombre de la tabla anterior.
- [ ] El notebook se ejecuta completo sin errores.
- [ ] Los gráficos tienen título, ejes con nombre y leyenda cuando aplica.
- [ ] Las decisiones de limpieza están justificadas por escrito.
- [ ] CI en verde.
- [ ] PR con descripción y hallazgos; revisión solicitada a la profesora.
- [ ] Tras el merge: squash, rama borrada y `main` descargada en local.
