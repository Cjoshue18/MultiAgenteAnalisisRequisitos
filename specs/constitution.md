# Constitución del Proyecto: Agente de Análisis de Requisitos de Software

Principios rectores derivados de [documento_maestro_propuesta.md](../docs/documento_maestro_propuesta.md) y [AGENTS.md](../AGENTS.md). Toda especificación (`spec.md`), plan (`plan.md`) y tarea (`tasks.md`) debe cumplir esta constitución.

---

## Principio I — Propósito y Rol de Asistencia
- El sistema asiste a analistas de requisitos extrayendo requisitos funcionales, requisitos no funcionales, inconsistencias y modelando **Casos de Uso (CUS)**, **Historias de Usuario (HU)** o **ambos (`AMBOS`)** según la modalidad seleccionada al inicio (fija durante la corrida).
- No sustituye el juicio del analista humano ni genera código fuente o modelos físicos de base de datos de la aplicación analizada.

## Principio II — Specification-Driven Development (SDD) Primero
- Ninguna funcionalidad pasa a diseño técnico ni a código sin una `spec.md` aprobada.
- Cada `spec.md` define exclusivamente el **qué** (User Story, Requirements binarios Sí/No, Acceptance Scenarios Dado/Cuando/Entonces, Out of Scope y Open Questions), libre de detalles tecnológicos.
- El **cómo** (arquitectura, contratos, almacenamiento, interfaces) se define únicamente en `plan.md` después de aprobar la `spec.md`.

## Principio III — Test-Driven Development (TDD) Estricto
- Las tareas en `tasks.md` deben ordenar siempre la escritura de pruebas antes que la implementación.
- Cada prueba deriva directamente de los Acceptance Scenarios de `spec.md` y lleva en su nombre el código del requisito correspondiente (ej. `test_req_01_*`).
- Las pruebas unitarias y de grafo se ejecutan de forma determinista con dobles/mocks locales y cero llamadas a servicios externos de IA.

## Principio IV — Rigor y Trazabilidad en Ingeniería de Requisitos
- **Requisitos Funcionales (RF):** Atómicos (IEEE 29148), con código correlativo único, al menos un actor y cita textual exacta del documento original (RN04, RN05, RNF08).
- **Requisitos No Funcionales (RNF):** Clasificados bajo las 8 categorías de **ISO/IEC 25010** con métrica cuantificable y umbral verificable (RN06).
- **Inconsistencias:** Catalogadas por tipo (`ambigüedad`, `contradicción`, `vacío`) y severidad (`Alta`, `Media`, `Baja`), siempre acompañadas de una pregunta de clarificación (RN07).
- **Casos de Uso (CUS) o Historias de Usuario (HU):** Según la selección previa del usuario, el modelado produce `CUS` formales (actor principal, precondiciones, flujo principal numerado secuencialmente, flujos alternativos y postcondiciones) o `HU` ágiles (`COMO/QUIERO/PARA QUE` y criterios de aceptación `DADO/CUANDO/ENTONCES`).

## Principio V — Validación Humana (Human-in-the-Loop) e Inmutabilidad
- Todo artefacto generado por agentes es un borrador preliminar hasta recibir aprobación explícita del analista humano (RN08).
- La revisión humana ocurre tras completarse los cuatro análisis especializados, permitiendo editar elementos, responder preguntas de clarificación y añadir comentarios.
- Una vez aprobado, el análisis adquiere estado inmutable (RN09) y solo entonces se habilita la exportación del reporte consolidado final (RN10).

## Principio VI — Seguridad, Resiliencia y Observabilidad
- Se rechazan solicitudes vacías o menores a 20 caracteres significativos (RN01) y entradas que superen 10 MB o 10,000 palabras (RN02).
- El texto del usuario se trata estrictamente como datos pasivos de análisis para neutralizar intentos de inyección de instrucciones (RNF02).
- Las credenciales residen fuera del código fuente (RNF04).
- Los errores externos aplican reintentos acotados (RN11), no provocan cierres abruptos y permiten reanudar desde el último punto guardado (RNF09), registrando trazas de estado, tiempos y resultado por etapa (RNF05).

## Principio VII — Disciplina de Commits
- Todo commit respeta `prefijo(contexto): descripcion` con la descripción en español y un único dominio lógico por commit, manteniéndose en ediciones acotadas ($\le 300$ líneas).
