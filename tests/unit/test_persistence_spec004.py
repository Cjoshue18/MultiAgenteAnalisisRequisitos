from pathlib import Path
import pytest
from src.persistence.repository import AnalisisRegistro, RepositorioSQLite
from src.schemas.contracts import (
    CasoUso,
    Inconsistencia,
    RequisitoFuncional,
    RequisitoNoFuncional,
    TrazaEjecucion,
)

RF_1 = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RNF_1 = RequisitoNoFuncional(
    id="RNF-01",
    categoria_iso="Rendimiento",
    descripcion="Responder consultas en menos de 2 segundos.",
    metrica_objetiva="Tiempo de respuesta",
    valor_umbral="2 s",
)
INC_1 = Inconsistencia(
    tipo="vacío",
    severidad="Media",
    descripcion="No se indica límite de libros por alumno.",
    pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?",
    respuesta_analista="Hasta 3 libros",
)
CUS_1 = CasoUso(
    id="CUS-01",
    nombre="Consultar catálogo",
    actor_principal="Alumno",
    precondiciones=["Estar autenticado"],
    flujo_principal=["1. Ingresar búsqueda", "2. Mostrar resultados"],
    flujos_alternativos=[],
    postcondiciones=["Resultados mostrados"],
    rf_relacionados=["RF-01"],
)


def _registro_base(analisis_id: str, proyecto_id: str, estado: str = "PENDIENTE_APROBACION") -> AnalisisRegistro:
    return AnalisisRegistro(
        analisis_id=analisis_id,
        proyecto_id=proyecto_id,
        version=1,
        estado=estado,  # type: ignore[arg-type]
        modalidad_modelado="CUS",
        texto_usuario="El alumno debe consultar libros disponibles en la biblioteca.",
        estrategia_ingesta="directa",
        requisitos_funcionales=[RF_1],
        requisitos_no_funcionales=[RNF_1],
        inconsistencias=[INC_1],
        casos_uso=[CUS_1],
        historias_usuario=[],
        respuestas_clarificacion={"0": "Hasta 3 libros"},
        comentarios_analista="Validado",
        trazas=[
            TrazaEjecucion(
                nodo="nodo_rf",
                estado="COMPLETADO",
                inicio_iso="2026-11-25T18:00:00Z",
                fin_iso="2026-11-25T18:00:01Z",
                detalle="OK",
            )
        ],
        errores=[],
    )


def test_req_01_crea_lista_proyectos_y_asocia_multiples_analisis(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'test.db'}")
    p1 = repo.crear_proyecto("Biblioteca Universitaria", "Sistema de préstamos")
    p2 = repo.crear_proyecto("Clínica", "Citas médicas")

    proyectos = repo.listar_proyectos()
    assert {p.proyecto_id for p in proyectos} == {p1.proyecto_id, p2.proyecto_id}

    repo.guardar_analisis(_registro_base("ANA-1", p1.proyecto_id))
    repo.guardar_analisis(_registro_base("ANA-2", p1.proyecto_id))
    repo.guardar_analisis(_registro_base("ANA-3", p2.proyecto_id))

    assert len(repo.listar_analisis(proyecto_id=p1.proyecto_id)) == 2
    assert len(repo.listar_analisis()) == 3


def test_req_03_persiste_y_recupera_analisis_entre_instancias_sqlite(tmp_path: Path) -> None:
    db_url = f"sqlite:///{tmp_path / 'persist.db'}"
    repo1 = RepositorioSQLite(db_url)
    proy = repo1.crear_proyecto("Biblioteca")
    reg = _registro_base("ANA-10", proy.proyecto_id)
    repo1.guardar_analisis(reg)

    repo2 = RepositorioSQLite(db_url)
    recuperado = repo2.obtener_analisis("ANA-10")
    assert recuperado.proyecto_id == proy.proyecto_id
    assert recuperado.requisitos_funcionales == [RF_1]
    assert recuperado.inconsistencias[0].respuesta_analista == "Hasta 3 libros"
    assert recuperado.trazas[0].nodo == "nodo_rf"


def test_req_04_rechaza_sobrescritura_de_analisis_aprobado(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'inmut.db'}")
    proy = repo.crear_proyecto("Biblioteca")
    aprobado = _registro_base("ANA-20", proy.proyecto_id, estado="APROBADO")
    repo.guardar_analisis(aprobado)

    mutado = aprobado.model_copy(update={"comentarios_analista": "Cambio ilegal"})
    with pytest.raises(ValueError, match="inmutable"):
        repo.guardar_analisis(mutado)


def test_req_04_crea_nueva_version_correlativa_manteniendo_original_aprobada(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'ver.db'}")
    proy = repo.crear_proyecto("Biblioteca")
    v1 = _registro_base("ANA-30", proy.proyecto_id, estado="APROBADO")
    repo.guardar_analisis(v1)

    v2 = repo.crear_nueva_version("ANA-30")
    assert v2.version == 2
    assert v2.analisis_origen_id == "ANA-30"
    assert v2.proyecto_id == proy.proyecto_id
    assert v2.estado == "PENDIENTE_APROBACION"
    assert repo.obtener_analisis("ANA-30").estado == "APROBADO"
