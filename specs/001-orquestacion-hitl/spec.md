# Spec 001: Ingesta Dual, Orquestación Multiagente y Revisión Humana (HITL)

**Estado:** Aprobada  
**Constitución aplicable:** [constitution.md](../constitution.md)

---

## User Story

**COMO** analista de requisitos de software  
**QUIERO** ingresar una especificación textual o archivo compatible para que el sistema valide sus límites, ajuste el procesamiento si el texto es breve o extenso, coordine la extracción de requisitos, la detección de inconsistencias y el modelado preliminar de casos de uso antes de pausar para mi revisión  
**PARA QUE** pueda corregir hallazgos, responder preguntas de clarificación, regenerar casos de uso bajo mi decisión si modifiqué requisitos y aprobar formalmente un análisis completo y trazable.

---

## Requirements

- **REQ-01 (Validación de entrada y límites):** El sistema debe rechazar toda solicitud nula, vacía o con menos de 20 caracteres significativos, así como entradas que no correspondan a formatos permitidos (`.txt`, `.md`, `.pdf` o texto directo) o que superen los **10 MB** o **10,000 palabras**, registrando el motivo del rechazo antes de iniciar cualquier análisis.
- **REQ-02 (Ingesta con camino dual por extensión):** El sistema debe procesar solicitudes válidas menores a **1,000 palabras** en una sola pasada directa, y dividir solicitudes de **1,000 a 10,000 palabras** en fragmentos con solapamiento por lotes antes de extraer requisitos, consolidando luego los resultados sin duplicar requisitos equivalentes.
- **REQ-03 (Extracción concurrente y acumulación de errores):** El sistema debe ejecutar de forma independiente la extracción de requisitos funcionales (RF) y no funcionales (RNF); si una o ambas extracciones fallan, debe conservar y reportar todos los errores ocurridos sin sobrescribir ni perder ninguno.
- **REQ-04 (Detección de inconsistencias tras extracciones):** Una vez completadas las extracciones de RF y RNF, el sistema debe contrastarlas contra el texto original para registrar inconsistencias tipadas (`ambigüedad`, `contradicción`, `vacío`) con severidad (`Alta`, `Media`, `Baja`) y una pregunta de clarificación por hallazgo.
- **REQ-05 (Modelado preliminar y regeneración explícita de casos de uso):** El sistema debe generar casos de uso preliminares usando los RF extraídos sin exigir aprobación humana previa para esa primera pasada; durante la revisión humana, solo si el analista modifica RF y ejecuta explícitamente la acción de regenerar casos de uso, el sistema debe recalcularlos usando exclusivamente los RF confirmados por el analista.
- **REQ-06 (Pausa de revisión humana al cierre del análisis):** Al finalizar los cuatro análisis especializados (RF, RNF, inconsistencias y casos de uso), el sistema debe pausar el flujo en estado `PENDIENTE_APROBACION` permitiendo editar requisitos o casos de uso, responder preguntas de clarificación y registrar comentarios.
- **REQ-07 (Aprobación explícita, inmutabilidad y bloqueo de exportación):** Solo cuando el analista confirme explícitamente la aprobación, el sistema debe pasar el análisis a estado `APROBADO`, preservar respuestas y comentarios, volver inmutables los registros aprobados e impedir emitir el reporte consolidado final mientras el estado sea distinto de `APROBADO`.
- **REQ-08 (Resiliencia, trazabilidad y reanudación sin reejecución):** Ante fallos externos transitorios el sistema debe aplicar hasta 2 reintentos; si el fallo persiste, debe detener el flujo en estado `FALLIDO` preservando los resultados parciales ya completados, registrar la traza de cada etapa (identificador, estado y marcas de tiempo) y permitir reanudar desde el último punto guardado (incluyendo desde `PENDIENTE_APROBACION`) sin reejecutar etapas previas ya completadas.

---

## Acceptance Scenarios

### Escenarios para REQ-01
- **Escenario REQ-01.1 (Texto nulo, vacío o insuficiente):**  
  **DADO** una solicitud con texto nulo, solo espacios o con 19 caracteres significativos  
  **CUANDO** se inicia el análisis  
  **ENTONCES** el sistema rechaza la solicitud indicando el mínimo de 20 caracteres y cero etapas de extracción ejecutadas.
- **Escenario REQ-01.2 (Exceso de palabras o archivo inválido):**  
  **DADO** una solicitud que supera las 10,000 palabras, supera los 10 MB o usa una extensión no permitida (ej. `.exe`)  
  **CUANDO** se valida la entrada  
  **ENTONCES** el sistema rechaza la solicitud registrando la causa exacta antes de invocar extracción.

### Escenarios para REQ-02
- **Escenario REQ-02.1 (Camino directo < 1,000 palabras):**  
  **DADO** una solicitud válida de 200 palabras  
  **CUANDO** ingresa al flujo de análisis  
  **ENTONCES** se selecciona el procesamiento directo en un único bloque sin fragmentación.
- **Escenario REQ-02.2 (Camino por lotes 1,000 a 10,000 palabras):**  
  **DADO** una solicitud válida de 2,500 palabras (en texto o archivo `.txt`/`.md`/`.pdf`)  
  **CUANDO** ingresa al flujo de análisis  
  **ENTONCES** el contenido se divide en fragmentos con solapamiento, se extraen requisitos por lote y se consolidan sin duplicados equivalentes.

### Escenarios para REQ-03
- **Escenario REQ-03.1 (Fallo concurrente sin pérdida de errores):**  
  **DADO** una solicitud válida donde tanto la extracción de RF como la de RNF fallan durante la ejecución concurrente  
  **CUANDO** concluye la etapa de extracción  
  **ENTONCES** el registro de errores del análisis conserva ambos mensajes de fallo intactos.

### Escenarios para REQ-04
- **Escenario REQ-04.1 (Cruce tras sincronización):**  
  **DADO** una solicitud válida con listas de RF y RNF ya extraídas  
  **CUANDO** se ejecuta la detección de inconsistencias  
  **ENTONCES** cada hallazgo registrado incluye tipo, severidad (`Alta`, `Media` o `Baja`), descripción de evidencia y pregunta de clarificación no vacía.

### Escenarios para REQ-05
- **Escenario REQ-05.1 (Primera pasada sin aprobación previa):**  
  **DADO** un análisis con RF extraídos y sin revisión humana previa  
  **CUANDO** avanza al modelado de casos de uso  
  **ENTONCES** genera casos de uso preliminares a partir de los RF extraídos sin emitir error por falta de aprobación.
- **Escenario REQ-05.2 (Regeneración explícita bajo decisión del analista):**  
  **DADO** un análisis pausado en `PENDIENTE_APROBACION` donde el analista editó los RF  
  **CUANDO** el analista solicita explícitamente la acción de regenerar casos de uso  
  **ENTONCES** se recalculan los casos de uso usando exclusivamente los RF confirmados y vuelve a pausar en `PENDIENTE_APROBACION`; si el analista aprueba sin pedir regeneración, los casos de uso no se recalculan automáticamente.

### Escenarios para REQ-06
- **Escenario REQ-06.1 (Pausa posterior a los 4 análisis):**  
  **DADO** una solicitud válida cuyos análisis de RF, RNF, inconsistencias y casos de uso concluyeron sin fallo  
  **CUANDO** alcanza la etapa de revisión humana  
  **ENTONCES** el flujo se detiene en estado `PENDIENTE_APROBACION` exponiendo propuestas, preguntas de clarificación y campos editables.

### Escenarios para REQ-07
- **Escenario REQ-07.1 (Bloqueo de exportación sin aprobación):**  
  **DADO** un análisis en estado `EN_PROCESO`, `PENDIENTE_APROBACION` o `FALLIDO`  
  **CUANDO** se solicita consolidar o exportar el reporte final  
  **ENTONCES** el sistema rechaza la operación indicando que requiere aprobación humana explícita.
- **Escenario REQ-07.2 (Aprobación e inmutabilidad):**  
  **DADO** un análisis en estado `PENDIENTE_APROBACION`  
  **CUANDO** el analista envía respuestas a preguntas, comentarios y confirmación de aprobación  
  **ENTONCES** el análisis pasa a `APROBADO`, conserva respuestas y comentarios, rechaza modificaciones posteriores sobre esa versión y habilita el reporte final.

### Escenarios para REQ-08
- **Escenario REQ-08.1 (Reintentos y detención en FALLIDO):**  
  **DADO** una falla externa persistente en una etapa de extracción que supera 2 reintentos  
  **CUANDO** se agotan los reintentos  
  **ENTONCES** el flujo se detiene en estado `FALLIDO` (sin avanzar a inconsistencias), conservando el resultado de la otra extracción si sí completó y registrando la traza del fallo.
- **Escenario REQ-08.2 (Reanudación desde checkpoint sin reejecución):**  
  **DADO** un análisis detenido en `PENDIENTE_APROBACION` o en `FALLIDO` tras completar una etapa previa  
  **CUANDO** el analista reanuda el flujo  
  **ENTONCES** las etapas ya completadas no vuelven a ejecutarse y la traza de ejecución conserva el historial completo con marcas de tiempo.

---

## Out of Scope
- Generación de archivos exportables en formatos finales específicos (Markdown, JSON, PDF o Word), que se especificará en una spec dedicada de exportación.
- Diseño visual de pantallas e interfaz de usuario o exposición de endpoints web externos (spec posterior de API/UI).
- Autenticación multiusuario, permisos, roles o facturación.

---

## Decisiones Cerradas (antes Open Questions)
- **OQ-01 resuelta:** Se adopta regeneración explícita de casos de uso (`regenerar_cus`) bajo responsabilidad del analista durante `PENDIENTE_APROBACION`, evitando sobrescribir cambios manuales o disparar inferencias no solicitadas.
- **OQ-02 resuelta:** Conforme a [documento_maestro_propuesta.md](../../docs/documento_maestro_propuesta.md) (`RN11`, `RF15`, Secciones 7 y 17), tras agotar hasta 2 reintentos el flujo se detiene limpiamente en estado `FALLIDO` conservando checkpoints parciales para reanudar solo lo pendiente.

## Open Questions
Ninguna.
