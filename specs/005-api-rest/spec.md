# Spec 005: Capa de Servicios Web para Gestión de Proyectos, Análisis y Exportación

**Estado:** Aprobada  
**Constitución aplicable:** [constitution.md](../constitution.md)

---

## User Story

**COMO** desarrollador de interfaz o integrador externo  
**QUIERO** consumir todas las capacidades de proyectos, análisis multiagente, revisión humana, versionado y descarga de reportes mediante operaciones web estandarizadas  
**PARA QUE** cualquier cliente (como la interfaz visual o herramientas de prueba) interactúe con el sistema de forma desacoplada y validada.

---

## Requirements

- **REQ-01 (Servicios de Proyectos):** El sistema debe exponer operaciones web para crear un proyecto (exigiendo nombre no vacío y descripción opcional), listar todos los proyectos y consultar un proyecto por identificador, devolviendo error `404` cuando el identificador no exista y `4xx` cuando el nombre esté vacío.
- **REQ-02 (Inicio síncrono de análisis por texto o archivo):** El sistema debe exponer dos operaciones web separadas: una en formato estructurado para texto directo y otra para carga de archivos (`.txt`, `.md`, `.pdf`), ambas exigiendo `proyecto_id` existente y modalidad (`CUS`, `HU` o `AMBOS`), ejecutando el flujo de forma síncrona y retornando identificador, versión, estado (`PENDIENTE_APROBACION` o `FALLIDO`), advertencias y artefactos; ante proyecto inexistente responde `404`, y ante entrada inválida o inyección responde `4xx`.
- **REQ-03 (Consulta de detalle e historial):** El sistema debe exponer operaciones web para listar análisis (totales o filtrados por `proyecto_id`) y obtener el detalle completo de un análisis por identificador, respondiendo `404` si el identificador no existe.
- **REQ-04 (Revisión humana HITL — regenerar o aprobar):** El sistema debe exponer una operación web para enviar la decisión del analista (`regenerar_cus` o `aprobar`, ediciones de RF/RNF/CUS/HU, respuestas a clarificaciones y comentarios), rechazando con `400` cualquier intento de cambiar la modalidad fija de la corrida y con `409` cualquier modificación sobre análisis ya `APROBADO`.
- **REQ-05 (Versionado de análisis aprobado):** El sistema debe exponer una operación web para generar una nueva versión editable (`versión + 1`) a partir de un análisis en estado `APROBADO`, rechazando con `409` si el análisis origen no está aprobado y con `404` si no existe.
- **REQ-06 (Descarga de reporte consolidado):** El sistema debe exponer una operación web para descargar el reporte consolidado en formato `md`, `json`, `pdf` o `docx`, bloqueando con `409` cuando el análisis no esté `APROBADO` y con `4xx` cuando el formato no sea válido.
- **REQ-07 (Salud del servicio y contratos autodescriptivos):** El sistema debe proveer una operación de verificación de disponibilidad (`health`) y documentación interactiva autodescriptiva de los contratos.

---

## Acceptance Scenarios

### Escenarios para REQ-01
- **Escenario REQ-01.1 (Crear, listar y consultar proyecto):**  
  **DADO** una petición válida con nombre `"Biblioteca Universitaria"`  
  **CUANDO** se invoca creación de proyecto, listado y consulta por identificador  
  **ENTONCES** retorna `201` al crear, `200` al listar/consultar, y `404` para un identificador inexistente.
- **Escenario REQ-01.2 (Rechazo de proyecto con nombre vacío):**  
  **DADO** una petición de creación de proyecto con nombre vacío  
  **CUANDO** se envía al servicio  
  **ENTONCES** responde con error `4xx`.

### Escenarios para REQ-02
- **Escenario REQ-02.1 (Inicio síncrono por texto y por archivo):**  
  **DADO** un proyecto existente, modalidad `HU` y texto válido (o archivo `.txt`)  
  **CUANDO** se invoca la operación de texto directo o la de carga de archivo  
  **ENTONCES** ambos responden `201` con estado `PENDIENTE_APROBACION`, advertencias y artefactos; y **CUANDO** el proyecto no existe responde `404`, o si hay inyección/entrada inválida responde `400`.

### Escenarios para REQ-03
- **Escenario REQ-03.1 (Historial y detalle):**  
  **DADO** análisis almacenados bajo un proyecto  
  **CUANDO** se consulta el historial filtrado por `proyecto_id` y luego el detalle por identificador  
  **ENTONCES** retorna los análisis correspondientes y `404` si el identificador no existe.

### Escenarios para REQ-04 y REQ-05
- **Escenario REQ-04.1 (Aprobación, cambio de modalidad bloqueado e inmutabilidad):**  
  **DADO** un análisis en `PENDIENTE_APROBACION` bajo modalidad `HU`  
  **CUANDO** se intenta cambiar la modalidad a `CUS` responde `400`; **CUANDO** se aprueba pasa a `APROBADO` (`200`); y **CUANDO** se intenta revisar nuevamente ese mismo identificador responde `409`.
- **Escenario REQ-05.1 (Nueva versión desde análisis aprobado):**  
  **DADO** un análisis en estado `APROBADO`  
  **CUANDO** se solicita crear una nueva versión  
  **ENTONCES** responde `201` con `versión = 2` en estado `PENDIENTE_APROBACION`; y si el origen no estaba aprobado responde `409`.

### Escenarios para REQ-06 y REQ-07
- **Escenario REQ-06.1 (Descarga bloqueada y descarga válida):**  
  **DADO** un análisis en `PENDIENTE_APROBACION`  
  **CUANDO** se solicita descargar en `md` responde `409`; y **CUANDO** está `APROBADO`, descarga exitosamente en `md`, `json`, `pdf` y `docx`.
- **Escenario REQ-07.1 (Salud y documentación):**  
  **DADO** el servicio web activo  
  **CUANDO** se consulta `health` y la especificación de contratos  
  **ENTONCES** ambos responden `200`.

---

## Out of Scope
- Interfaz gráfica visual de usuario (`Spec 006`).
- Autenticación de usuarios, sesiones web o autorización por roles.
- Ejecución en segundo plano con colas distribuidas externas.

---

## Decisiones Cerradas (antes Open Questions)
- **OQ-01 resuelta:** Inicio de análisis **síncrono** devolviendo directamente `PENDIENTE_APROBACION` (o `FALLIDO`).
- **OQ-02 resuelta:** **Dos endpoints separados**: JSON para texto directo y `multipart/form-data` para archivos (`.txt`, `.md`, `.pdf`).

## Open Questions
Ninguna.
