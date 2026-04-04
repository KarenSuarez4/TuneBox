from __future__ import annotations

from datetime import datetime, timedelta

from access_control import MotorAcceso
from models import Accion, ClasificacionMAC, Recurso, Rol, Usuario


def construir_escenario():
    """Construye usuarios y recursos del mundo TuneBox."""
    motor = MotorAcceso()
    fecha_embargo = datetime.now() + timedelta(days=10)

    usuarios = {
        "sofia": Usuario(
            id="u001",
            nombre="Sofia Ramos",
            rol=Rol.ARTISTA,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
        ),
        "carlos": Usuario(
            id="u002",
            nombre="Carlos Vega",
            rol=Rol.ARTISTA,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
        ),
        "manager_a": Usuario(
            id="u003",
            nombre="Laura Mendez",
            rol=Rol.MANAGER,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
            artistas_representados=["u001"],
        ),
        "marketing": Usuario(
            id="u004",
            nombre="Pedro Torres",
            rol=Rol.MARKETING,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL,
        ),
        "legal": Usuario(
            id="u005",
            nombre="Ana Rios",
            rol=Rol.LEGAL_COMPLIANCE,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
        ),
        "analitica": Usuario(
            id="u006",
            nombre="Luis Parra",
            rol=Rol.ANALITICA,
            nivel_autorizacion=ClasificacionMAC.PUBLICO,
        ),
        "admin": Usuario(
            id="u007",
            nombre="Maria Gil",
            rol=Rol.ADMINISTRATIVO,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL,
        ),
        "spotify_api": Usuario(
            id="u008",
            nombre="Spotify API",
            rol=Rol.PLATAFORMA_EXTERNA,
            nivel_autorizacion=ClasificacionMAC.PUBLICO,
            plataforma_id="u001",
        ),
        "contador": Usuario(
            id="u009",
            nombre="Rodrigo Salas (Contador externo)",
            rol=Rol.ADMINISTRATIVO,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
        ),
        "prod_editorial": Usuario(
            id="u010",
            nombre="Diana Cruz",
            rol=Rol.PRODUCTOR_EDITORIAL,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL,
        ),
    }

    recursos = {
        "cancion_sofia": Recurso(
            id="r001",
            nombre="Track 'Noche Eterna' - Sofia",
            tipo="cancion",
            clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="u001",
        ),
        "ganancias_sofia": Recurso(
            id="r002",
            nombre="Ganancias Q1-2026 - Sofia",
            tipo="ganancia",
            clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u001",
        ),
        "lanzamiento_futuro_sofia": Recurso(
            id="r003",
            nombre="Album 'Eclipse' (PRELANZAMIENTO) - Sofia",
            tipo="metrica",
            clasificacion=ClasificacionMAC.CONFIDENCIAL,
            propietario_id="u001",
            fecha_embargo=fecha_embargo,
        ),
        "ganancias_carlos": Recurso(
            id="r004",
            nombre="Ganancias Q1-2026 - Carlos",
            tipo="ganancia",
            clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u002",
        ),
        "cancion_carlos": Recurso(
            id="r005",
            nombre="Track 'Solar' - Carlos",
            tipo="cancion",
            clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="u002",
        ),
        "metricas_agregadas": Recurso(
            id="r006",
            nombre="Metricas Agregadas Plataforma",
            tipo="metrica",
            clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="sistema",
        ),
        "contrato_sofia": Recurso(
            id="r007",
            nombre="Contrato Distribucion - Sofia",
            tipo="contrato",
            clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u001",
        ),
    }

    return usuarios, recursos, motor


def ejecutar_simulacion():
    """Ejecuta todos los casos de uso del enunciado."""

    def sep(titulo):
        print(f"\n{'=' * 70}\n  CASO: {titulo}\n{'=' * 70}")

    usuarios, recursos, motor = construir_escenario()

    print(
        """
+----------------------------------------------------------------------+
|       TUNEBOX - Simulacion de Control de Acceso RBAC + DAC + MAC     |
+----------------------------------------------------------------------+
"""
    )

    motor.imprimir_matriz_rbac()

    sep("1. Artista accede a sus propios datos [esperado: PERMITIDO]")
    motor.solicitar_acceso(usuarios["sofia"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["sofia"], recursos["cancion_sofia"], Accion.ESCRIBIR)

    sep("2. Artista intenta ver datos de artista rival [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["carlos"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["sofia"], recursos["cancion_carlos"], Accion.LEER)

    sep("3. Manager accede a datos de SU artista [esperado: PERMITIDO]")
    motor.solicitar_acceso(usuarios["manager_a"], recursos["ganancias_sofia"], Accion.LEER)

    sep("4. CONFLICTO: Manager accede a artista NO representado [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["manager_a"], recursos["ganancias_carlos"], Accion.LEER)

    sep("5. CONFLICTO EMBARGO: Marketing lee antes de fecha oficial [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["marketing"], recursos["lanzamiento_futuro_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["marketing"], recursos["metricas_agregadas"], Accion.LEER)
    motor.solicitar_acceso(usuarios["marketing"], recursos["ganancias_sofia"], Accion.LEER)

    sep("6. Legal audita datos SECRETOS [esperado: PERMITIDO + registrado]")
    motor.solicitar_acceso(usuarios["legal"], recursos["ganancias_sofia"], Accion.AUDITAR)
    motor.solicitar_acceso(usuarios["legal"], recursos["lanzamiento_futuro_sofia"], Accion.AUDITAR)
    motor.solicitar_acceso(usuarios["legal"], recursos["contrato_sofia"], Accion.AUDITAR)

    sep("7. Analitica accede a metricas [esperado: PERMITIDO solo publicas]")
    motor.solicitar_acceso(usuarios["analitica"], recursos["metricas_agregadas"], Accion.LEER)
    motor.solicitar_acceso(usuarios["analitica"], recursos["ganancias_sofia"], Accion.LEER)

    sep("8. Spotify API - acceso solo a sus artistas [esperado: mixto]")
    motor.solicitar_acceso(usuarios["spotify_api"], recursos["cancion_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["spotify_api"], recursos["cancion_carlos"], Accion.LEER)

    sep("9. DAC: Artista delega acceso temporal a contador externo")
    motor.delegar_permiso(
        propietario=usuarios["sofia"],
        recurso=recursos["ganancias_sofia"],
        beneficiario=usuarios["contador"],
        acciones=[Accion.LEER],
        dias=30,
    )
    motor.solicitar_acceso(usuarios["contador"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["contador"], recursos["ganancias_carlos"], Accion.LEER)

    sep("10. Nuevo Rol: Productor Editorial accede a canciones y ganancias")
    motor.solicitar_acceso(usuarios["prod_editorial"], recursos["cancion_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["prod_editorial"], recursos["ganancias_sofia"], Accion.LEER)

    motor.imprimir_log()

    print("=" * 70)
    print("  CLASIFICACION DE DATOS SEGUN MAC - TuneBox")
    print("=" * 70)
    clasificaciones = [
        (
            "PUBLICO (nivel 1)",
            "Metricas agregadas, nombres artistas, info publica de lanzamientos",
            "Todos los roles autenticados, APIs externas, Analitica",
        ),
        (
            "CONFIDENCIAL (nivel 2)",
            "Datos de lanzamientos futuros (embargo), campanas de marketing",
            "Marketing (con restriccion embargo), Admin, Manager, Artista propietario",
        ),
        (
            "SECRETO (nivel 3)",
            "Ganancias individuales, contratos de distribucion, datos fiscales",
            "Artista (propios), Manager (representados), Legal, Admin agregado, DAC",
        ),
    ]
    for nivel, desc, acceso in clasificaciones:
        print(f"\n  [*] {nivel}")
        print(f"      Datos  : {desc}")
        print(f"      Acceso : {acceso}")
    print("\n" + "=" * 70)
    print("\n  Simulacion completada. Revise el log de auditoria para el informe.\n")
