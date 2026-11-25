# Plan Técnico 004: Proyectos, Persistencia SQLite, Exportación y Fachada

**Spec de origen:** [spec.md](./spec.md) (Aprobada)  
**Constitución:** [constitution.md](../constitution.md)

---

## 1. Arquitectura y Decisiones Técnicas

### 1.1. Dependencias (`pyproject.toml`)
- `sqlalchemy>=2.0.0` (persistencia relacional desacoplada sobre SQLite).
- `python-docx>=1.1.0` (generación de documentos Word `.docx`).
- `fpdf2>=2.7.0` (generación de `.pdf` en Python puro sin binarios externos).

### 1.2. Capa de Persistencia — Puerto y Adaptador SQLite (`src/persistence/`)
- **`src/persistence/models.py` (SQLAlchemy 2.0 ORM):**
  - `ProyectoORM`: `proyecto_id` (PK), `nombre`, `descripcion`, `fecha_creacion`.
  - `AnalisisORM`: `analisis_id` (PK), `proyecto_id` (FK → `proyectos.proyecto_id`), `version` (int), `analisis_origen_id` (str | None), `estado`, `modalidad_modelado`, `texto_usuario`, `estrategia_ingesta`, `advertencias_json`, `rf_json`, `rnf_json`, `inconsistencias_json`, `cus_json`, `hu_json`, `respuestas_json`, `comentarios_analista`, `trazas_json`, `errores_json`, `reporte_json`, `fecha_creacion`, `fecha_aprobacion`.
- **`src/persistence/repository.py`:**
  - Modelos de lectura/dominio `ProyectoInfo`, `AnalisisRegistro`.
  - Puerto `RepositorioAnalisis(Protocol)`: `crear_proyecto`, `obtener_proyecto`, `listar_proyectos`, `guardar_analisis`, `obtener_analisis`, `listar_analisis`, `crear_nueva_version`.
  - Adaptador `RepositorioSQLite(db_url: str = "sqlite:///analisis.db")`:
    - `guardar_analisis`: verifica si ya existe en BD con `estado == "APROBADO"`; si es así, lanza `ValueError` (**`RN09` inmutabilidad**).
    - `crear_nueva_version(analisis_id)`: exige que el origen esté en `APROBADO`, calcula `siguiente_version = max(version) + 1` dentro del proyecto/origen y crea un nuevo registro en `PENDIENTE_APROBACION` (o `EN_PROCESO`) copiando los artefactos base para edición sin alterar el original.

### 1.3. Exportación Multiformato (`src/services/exportador.py`)
- `exportar_reporte(reporte: ReporteConsolidado, formato: Literal["md", "json", "pdf", "docx"], directorio_salida: Path, nombre_proyecto: str = "", version: int = 1) -> Path`:
  - Valida `reporte.estado == "APROBADO"`.
  - `.md`: plantilla estructurada con resumen, RF (con citas), RNF (ISO 25010), inconsistencias (severidad + respuesta), CUS/HU y comentarios.
  - `.json`: `reporte.model_dump_json(indent=2)` enriquecido con `nombre_proyecto` y `version`.
  - `.docx`: documento Word generado con `python-docx` con encabezados y listas/tablas.
  - `.pdf`: documento PDF generado con `fpdf2` (normalizando caracteres fuera de Latin-1 en la fuente estándar para evitar errores en acentos/símbolos).

### 1.4. Fachada de Orquestación (`src/services/orchestrator.py`)
- `OrquestadorService(cliente: ClienteEstructurado, repositorio: RepositorioAnalisis, checkpointer: BaseCheckpointSaver, directorio_reportes: Path)`:
  - `crear_proyecto(nombre, descripcion="") -> ProyectoInfo`
  - `listar_proyectos() -> list[ProyectoInfo]`
  - `iniciar_analisis(proyecto_id, modalidad_modelado, texto=None, ruta_archivo=None) -> AnalisisRegistro`
  - `obtener_analisis(analisis_id) -> AnalisisRegistro`
  - `listar_analisis(proyecto_id=None) -> list[AnalisisRegistro]`
  - `enviar_revision(analisis_id, decision: DecisionRevision) -> AnalisisRegistro`
  - `crear_nueva_version(analisis_id) -> AnalisisRegistro`
  - `exportar_analisis(analisis_id, formatos: list[FormatoExportacion]) -> dict[str, Path]`

---

## 2. Plan de Commits Progresivos ($\le 300$ líneas por commit, 1 dominio)
1. **`chore(deps): agregar sqlalchemy, python-docx y fpdf2 para persistencia y exportacion`** (`pyproject.toml`, ~5 líneas).
2. **`feat(persistence): implementar modelos orm, puerto repositorio y adaptador sqlite`** (`src/persistence/__init__.py`, `models.py`, `repository.py`, `tests/unit/test_persistence_spec004.py`, ~250 líneas).
3. **`feat(export): implementar exportacion consolidada en md, json, pdf y docx`** (`src/services/exportador.py`, `tests/unit/test_exportador_spec004.py`, ~190 líneas).
4. **`feat(facade): implementar OrquestadorService integrando proyectos, grafo y exportacion`** (`src/services/orchestrator.py`, `tests/unit/test_orchestrator_spec004.py`, ~260 líneas).
