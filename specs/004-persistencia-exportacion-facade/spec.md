# Spec 004: Proyectos, Persistencia de Negocio, Exportación y Fachada

**Estado:** Aprobada  
**Constitución aplicable:** [constitution.md](../constitution.md)

---

## User Story

**COMO** analista de requisitos y consumidor del núcleo del sistema  
**QUIERO** organizar múltiples corridas de análisis bajo proyectos separados, operar todo el ciclo mediante una fachada de negocio unificada con almacenamiento persistente e inmutable tras aprobación y exportar el reporte en múltiples formatos  
**PARA QUE** cada proyecto conserve su historial versionado sin riesgo de sobrescritura y los reportes finales puedan descargarse en formatos estándar y ofimáticos.

---

## Requirements

- **REQ-01 (Gestión de Proyectos como entidad separada):** El sistema debe permitir crear proyectos con identificador único, nombre y fecha de creación, listar proyectos existentes y asociar múltiples corridas de análisis a un mismo proyecto, rechazando iniciar análisis sobre un proyecto inexistente.
- **REQ-02 (Operaciones unificadas de ciclo de vida — Fachada):** El sistema debe proveer operaciones de negocio simples para crear/listar proyectos, iniciar un análisis (generando identificador único y versión inicial `1`), consultar su estado y artefactos, enviar decisiones de revisión (`regenerar` o `aprobar`), listar el historial (total o filtrado por proyecto) y exportar el reporte final, ocultando los detalles internos del motor de flujo.
- **REQ-03 (Persistencia integral e historial consultable — `RF12`, `RF13`):** El sistema debe almacenar de forma persistente cada análisis (identificador, proyecto asociado, número de versión, fecha de creación, modalidad fijada, estado, texto original, RF, RNF, inconsistencias con respuestas, CUS, HU, comentarios y trazas de ejecución), permitiendo listar el historial y recuperar el detalle completo por identificador.
- **REQ-04 (Inmutabilidad tras aprobación y nueva versión — `RN09`):** Una vez que un análisis alcanza el estado `APROBADO`, el sistema debe rechazar cualquier modificación o sobrescritura directa sobre ese registro; ante una solicitud explícita de crear una nueva versión a partir de un análisis aprobado, debe generar un nuevo registro con versión correlativa (`versión + 1`) vinculado al mismo proyecto y al análisis origen, manteniendo intacta la versión anterior.
- **REQ-05 (Bloqueo de exportación sin aprobación — `RN10`):** El sistema debe rechazar toda solicitud de exportación del reporte final cuando el análisis se encuentre en estado `EN_PROCESO`, `PENDIENTE_APROBACION` o `FALLIDO`.
- **REQ-06 (Exportación multiformato — `RF14`):** Para todo análisis en estado `APROBADO`, el sistema debe generar archivos descargables en los formatos obligatorios (**Markdown** `.md` y **JSON** `.json`) y en los formatos opcionales (**PDF** `.pdf` y **Word** `.docx`) conteniendo identificador, proyecto, versión, fecha, modalidad elegida, RF con citas textuales, RNF ISO 25010, inconsistencias con severidad y respuesta del analista, CUS y/o HU aprobados y comentarios finales.

---

## Acceptance Scenarios

### Escenarios para REQ-01 y REQ-02
- **Escenario REQ-01.1 (Proyecto con múltiples corridas):**  
  **DADO** un proyecto creado en el sistema  
  **CUANDO** se inician dos análisis distintos asociados a ese proyecto  
  **ENTONCES** ambos análisis quedan vinculados al mismo proyecto y al listar el historial del proyecto aparecen ambos registros; si se intenta iniciar con un proyecto inexistente, el sistema rechaza la operación.
- **Escenario REQ-02.1 (Ciclo completo vía Fachada):**  
  **DADO** un proyecto existente y una solicitud válida con modalidad `HU`  
  **CUANDO** se inicia el análisis, se consulta por identificador y se aprueba mediante la fachada  
  **ENTONCES** el análisis transiciona de `PENDIENTE_APROBACION` a `APROBADO` con `versión = 1` sin que el consumidor gestione detalles internos de ejecución.

### Escenarios para REQ-03
- **Escenario REQ-03.1 (Persistencia y recuperación entre instancias):**  
  **DADO** un proyecto y un análisis almacenados en el repositorio persistente  
  **CUANDO** se consulta el historial o se recupera el detalle desde una nueva instancia del repositorio  
  **ENTONCES** los datos del proyecto, requisitos, inconsistencias, respuestas, modelado y trazas coinciden exactamente con los guardados.

### Escenarios para REQ-04
- **Escenario REQ-04.1 (Rechazo de mutación sobre análisis aprobado):**  
  **DADO** un análisis almacenado en estado `APROBADO`  
  **CUANDO** se intenta actualizar directamente sus datos o volver a enviar una aprobación sobre ese mismo identificador  
  **ENTONCES** el sistema rechaza la operación indicando que el análisis aprobado es inmutable.
- **Escenario REQ-04.2 (Nueva versión correlativa):**  
  **DADO** un análisis en estado `APROBADO` (`versión = 1`)  
  **CUANDO** se solicita crear una nueva versión editable a partir de él  
  **ENTONCES** se crea un nuevo análisis (`versión = 2`) vinculado al mismo proyecto y al análisis origen, preservando la `versión = 1` intacta en `APROBADO`.

### Escenarios para REQ-05 y REQ-06
- **Escenario REQ-05.1 (Bloqueo de exportación sin aprobación):**  
  **DADO** un análisis en estado `PENDIENTE_APROBACION` o `FALLIDO`  
  **CUANDO** se solicita exportar el reporte en cualquiera de los 4 formatos  
  **ENTONCES** el sistema rechaza la exportación exigiendo aprobación humana previa.
- **Escenario REQ-06.1 (Exportación válida en MD, JSON, PDF y DOCX):**  
  **DADO** un análisis en estado `APROBADO` con RF, RNF, inconsistencias respondidas y CUS/HU  
  **CUANDO** se solicita exportar en `.md`, `.json`, `.pdf` y `.docx`  
  **ENTONCES** se generan 4 archivos no vacíos y válidos en su formato respectivo conteniendo la información aprobada completa.

---

## Out of Scope
- Exposición de rutas HTTP / servicio web REST ni interfaz gráfica visual (`Spec 005`).
- Autenticación multiusuario o control de acceso por roles.
- Despliegue en servidores o bases de datos remotas gestionadas en la nube.

---

## Decisiones Cerradas (antes Open Questions)
- **OQ-01 resuelta:** Se incluyen los 4 formatos de exportación definidos en `RF14` de `documento_maestro_propuesta.md`: `.md`, `.json`, `.pdf` y `.docx`.
- **OQ-02 resuelta:** `Proyecto` se modela como entidad separada (`1..N` con `Analisis`) con creación, listado y asociación obligatoria por `proyecto_id`.

## Open Questions
Ninguna.
