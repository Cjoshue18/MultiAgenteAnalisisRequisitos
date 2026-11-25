# Spec 002: Selección Previa y Modelado en Casos de Uso (CUS), Historias de Usuario (HU) o Ambos

**Estado:** Aprobada  
**Constitución aplicable:** [constitution.md](../constitution.md)

---

## User Story

**COMO** analista de requisitos de software  
**QUIERO** seleccionar antes de enviar mi solicitud si el modelado final debe generarse como **Casos de Uso (`CUS`)**, **Historias de Usuario (`HU`)** o **Ambos (`AMBOS`)**, recibiendo las advertencias correspondientes antes de confirmar  
**PARA QUE** el sistema genere exactamente los artefactos adecuados para mi metodología sin ambigüedad durante la corrida.

---

## Requirements

- **REQ-01 (Selección obligatoria y advertencias previas al envío):** El sistema debe exigir elegir explícitamente una modalidad entre `CUS`, `HU` o `AMBOS` antes de iniciar la solicitud (rechazando omisiones o valores inválidos), mostrar al momento de elegir la advertencia explícita de que el formato quedará fijo para toda la corrida, y cuando se elija `AMBOS` emitir además una notificación explícita advirtiendo que el proceso demorará más al generar ambos formatos.
- **REQ-02 (Generación acorde a la modalidad elegida):** A partir de los requisitos funcionales extraídos, el sistema debe generar únicamente `CUS` (y cero `HU`) cuando la modalidad sea `CUS`; únicamente `HU` (y cero `CUS`) cuando la modalidad sea `HU`; y ambas colecciones (`CUS` y `HU`) cuando la modalidad sea `AMBOS`.
- **REQ-03 (Contrato de Casos de Uso — `CUS`):** Cuando se generen `CUS`, cada elemento debe incluir identificador correlativo (`CUS-01`, `CUS-02`, ...), nombre, actor principal, precondiciones, flujo principal con pasos numerados correlativamente (`1.`, `2.`, ...), flujos alternativos, postcondiciones y códigos de requisitos funcionales vinculados.
- **REQ-04 (Contrato de Historias de Usuario — `HU`):** Cuando se generen `HU`, cada elemento debe incluir identificador correlativo (`HU-01`, `HU-02`, ...), título breve, narrativa ágil completa (`COMO <rol>`, `QUIERO <capacidad>`, `PARA QUE <beneficio>`), al menos un criterio de aceptación verificable en formato `DADO / CUANDO / ENTONCES` y códigos de requisitos funcionales vinculados (sin campo de prioridad obligatorio).
- **REQ-05 (Inmutabilidad de modalidad en revisión humana y regeneración):** Durante `PENDIENTE_APROBACION`, el analista puede editar los artefactos generados de la modalidad original, pero el sistema debe rechazar cualquier intento de cambiar la modalidad elegida al inicio; si el analista modifica RF y solicita regenerar, el sistema recalcula únicamente el o los formatos fijados al inicio de esa corrida.
- **REQ-06 (Consolidación e inmutabilidad del formato aprobado):** Al confirmar la aprobación (`APROBADO`), el reporte consolidado final debe registrar la modalidad fija (`CUS`, `HU` o `AMBOS`) junto con los artefactos aprobados, impidiendo modificaciones posteriores sobre esa versión.

---

## Acceptance Scenarios

### Escenarios para REQ-01
- **Escenario REQ-01.1 (Rechazo sin selección o con valor inválido):**  
  **DADO** una solicitud con texto válido sin modalidad de modelado o con un valor distinto de `CUS`, `HU` y `AMBOS`  
  **CUANDO** se intenta enviar la solicitud  
  **ENTONCES** el sistema rechaza el envío indicando las opciones válidas (`CUS`, `HU`, `AMBOS`).
- **Escenario REQ-01.2 (Advertencia de modalidad fija y notificación de mayor demora para AMBOS):**  
  **DADO** una solicitud válida donde el usuario selecciona una modalidad antes del envío  
  **CUANDO** selecciona `CUS` o `HU`  
  **ENTONCES** el sistema muestra la advertencia de que el formato no podrá cambiarse durante la corrida; y **CUANDO** selecciona `AMBOS` **ENTONCES** muestra tanto la advertencia de formato fijo como la notificación de mayor tiempo de procesamiento.

### Escenarios para REQ-02
- **Escenario REQ-02.1 (Ruta exclusiva CUS o HU):**  
  **DADO** un análisis iniciado con modalidad `CUS` (o `HU`)  
  **CUANDO** se ejecuta la etapa de modelado  
  **ENTONCES** se generan únicamente elementos del formato elegido y cero elementos del formato opuesto.
- **Escenario REQ-02.2 (Ruta dual AMBOS):**  
  **DADO** un análisis iniciado con modalidad `AMBOS` y RF extraídos  
  **CUANDO** se ejecuta la etapa de modelado  
  **ENTONCES** se generan tanto la lista de `CUS` como la lista de `HU` vinculadas a los RF.

### Escenarios para REQ-03
- **Escenario REQ-03.1 (Integridad de Casos de Uso):**  
  **DADO** una salida generada de tipo `CUS`  
  **CUANDO** se valida su estructura  
  **ENTONCES** cada elemento posee código `CUS-xx`, actor principal, precondiciones, flujo principal numerado desde `1.`, flujos alternativos, postcondiciones y lista de RF relacionados.

### Escenarios para REQ-04
- **Escenario REQ-04.1 (Integridad de Historias de Usuario):**  
  **DADO** una salida generada de tipo `HU`  
  **CUANDO** se valida su estructura  
  **ENTONCES** cada elemento posee código `HU-xx`, título, `como`, `quiero`, `para_que`, al menos un criterio `DADO/CUANDO/ENTONCES` y lista de RF relacionados.
- **Escenario REQ-04.2 (Rechazo de HU incompleta):**  
  **DADO** una historia de usuario sin criterios de aceptación o con narrativa `COMO/QUIERO/PARA QUE` incompleta  
  **CUANDO** se valida la salida del modelador  
  **ENTONCES** el sistema rechaza la salida como contrato inválido y registra el fallo controlado.

### Escenarios para REQ-05
- **Escenario REQ-05.1 (Bloqueo de cambio de modalidad en revisión y regeneración coherente):**  
  **DADO** un análisis pausado en `PENDIENTE_APROBACION` iniciado con modalidad `HU`  
  **CUANDO** el analista intenta cambiar la modalidad a `CUS` o `AMBOS` durante la revisión  
  **ENTONCES** el sistema rechaza el cambio indicando que la modalidad es fija por corrida; y **CUANDO** edita RF y solicita regenerar manteniendo `HU` **ENTONCES** regenera únicamente nuevas `HU` y vuelve a `PENDIENTE_APROBACION`.

### Escenarios para REQ-06
- **Escenario REQ-06.1 (Consolidación final con modalidad fija):**  
  **DADO** un análisis en `PENDIENTE_APROBACION` bajo modalidad `AMBOS` con `CUS` y `HU` editados  
  **CUANDO** el analista confirma la aprobación  
  **ENTONCES** el reporte consolidado queda en estado `APROBADO`, conserva `AMBOS` y ambas listas aprobadas de forma inmutable.

---

## Out of Scope
- Estimación numérica de esfuerzo (ej. *Story Points*), campo `prioridad` en `HU` o planificación de *sprints*.
- Conversión posterior de un análisis ya `APROBADO` hacia otra modalidad.
- Diseño visual de componentes de interfaz gráfica o exportación a archivos externos.

---

## Decisiones Cerradas (antes Open Questions)
- **OQ-01 resuelta:** Se habilitan tres opciones previas al envío (`CUS`, `HU` y `AMBOS`), notificando al usuario que elegir `AMBOS` incrementa el tiempo de procesamiento.
- **OQ-02 resuelta:** No se requiere campo `prioridad` en `HU`.
- **OQ-03 resuelta:** La modalidad elegida al inicio queda fija para toda la corrida y no puede cambiarse al revisar o regenerar, mostrando advertencia explícita al momento de elegir.

## Open Questions
Ninguna.
