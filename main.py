"""
==============================================================================
  TUNEBOX - Sistema de Control de Acceso Integrado
  Simulación de Políticas RBAC + DAC + MAC
==============================================================================
  Autores : Equipo de Seguridad TuneBox
  Versión : 1.0
  Fecha   : 2026
------------------------------------------------------------------------------
  Modelos implementados:
    • RBAC  – Role-Based Access Control
    • DAC   – Discretionary Access Control
    • MAC   – Mandatory Access Control (niveles: PUBLICO, CONFIDENCIAL, SECRETO)
==============================================================================
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import uuid


# ══════════════════════════════════════════════════════════════════════════════
# 1.  ENUMERACIONES  (clasificaciones y acciones)
# ══════════════════════════════════════════════════════════════════════════════

class ClasificacionMAC(Enum):
    """Niveles de sensibilidad de datos según MAC."""
    PUBLICO       = 1   # Métricas agregadas, info de artistas pública
    CONFIDENCIAL  = 2   # Datos de lanzamientos futuros, campañas
    SECRETO       = 3   # Información financiera individual, contratos


class Rol(Enum):
    """Roles de la plataforma TuneBox."""
    ARTISTA             = "Artista/Productor"
    MANAGER             = "Manager"
    MARKETING           = "Equipo de Marketing"
    LEGAL_COMPLIANCE    = "Legal/Compliance"
    ANALITICA           = "Equipo de Analitica"
    ADMINISTRATIVO      = "Administrativo"
    PLATAFORMA_EXTERNA  = "Plataforma Externa (API)"
    PRODUCTOR_EDITORIAL = "Productor Editorial"   # rol futuro


class Accion(Enum):
    """Acciones posibles sobre un recurso."""
    LEER      = "leer"
    ESCRIBIR  = "escribir"
    ELIMINAR  = "eliminar"
    COMPARTIR = "compartir"
    AUDITAR   = "auditar"


# ══════════════════════════════════════════════════════════════════════════════
# 2.  ESTRUCTURAS DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class Recurso:
    """Representa cualquier activo de información dentro de TuneBox."""
    id: str
    nombre: str
    tipo: str                            # cancion | ganancia | metrica | metadato | contrato
    clasificacion: ClasificacionMAC
    propietario_id: str                  # ID del artista/entidad dueña
    fecha_embargo: Optional[datetime] = None   # para lanzamientos futuros

    def __str__(self) -> str:
        embargo = (f", embargo hasta {self.fecha_embargo.strftime('%Y-%m-%d')}"
                   if self.fecha_embargo else "")
        return (f"[{self.tipo.upper()}] '{self.nombre}' "
                f"({self.clasificacion.name}{embargo})")


@dataclass
class Usuario:
    """Representa a cualquier actor del sistema."""
    id: str
    nombre: str
    rol: Rol
    nivel_autorizacion: ClasificacionMAC  # nivel MAC maximo que puede ver
    artistas_representados: list = field(default_factory=list)  # para managers
    plataforma_id: Optional[str] = None   # para APIs externas

    def __str__(self) -> str:
        return f"{self.nombre} [{self.rol.value}]"


@dataclass
class PermisoDelegado:
    """DAC: permiso temporal que un propietario otorga a un tercero."""
    id: str
    recurso_id: str
    otorgado_por: str          # ID del propietario
    otorgado_a: str            # ID del beneficiario
    acciones: list
    expira: datetime
    activo: bool = True

    def esta_vigente(self) -> bool:
        return self.activo and datetime.now() < self.expira


@dataclass
class RegistroAcceso:
    """Entrada del log de auditoria."""
    timestamp: datetime
    usuario_id: str
    usuario_nombre: str
    usuario_rol: str
    recurso_id: str
    recurso_nombre: str
    accion: str
    resultado: str             # PERMITIDO | DENEGADO
    motivo: str
    modelo_aplicado: str       # RBAC | DAC | MAC | RBAC+MAC | etc.

    def __str__(self) -> str:
        icono = "OK " if self.resultado == "PERMITIDO" else "NO "
        return (f"{icono} [{self.timestamp.strftime('%H:%M:%S')}] "
                f"{self.usuario_nombre} ({self.usuario_rol}) -> "
                f"{self.accion.upper()} '{self.recurso_nombre}' | "
                f"{self.resultado} | {self.motivo} [{self.modelo_aplicado}]")


# ══════════════════════════════════════════════════════════════════════════════
# 3.  MATRIZ RBAC  (Rol x Tipo de Recurso x Acciones permitidas)
# ══════════════════════════════════════════════════════════════════════════════

RBAC_MATRIZ = {

    Rol.ARTISTA: {
        "cancion":    {Accion.LEER, Accion.ESCRIBIR, Accion.COMPARTIR},
        "ganancia":   {Accion.LEER},
        "metrica":    {Accion.LEER},
        "metadato":   {Accion.LEER, Accion.ESCRIBIR},
        "contrato":   {Accion.LEER},
    },

    Rol.MANAGER: {
        "cancion":    {Accion.LEER},
        "ganancia":   {Accion.LEER},          # solo de sus artistas (DAC check)
        "metrica":    {Accion.LEER},
        "metadato":   {Accion.LEER, Accion.ESCRIBIR},
        "contrato":   {Accion.LEER},
    },

    Rol.MARKETING: {
        "cancion":    {Accion.LEER},
        "ganancia":   set(),                  # SIN acceso a datos financieros
        "metrica":    {Accion.LEER},          # con restriccion de embargo MAC
        "metadato":   {Accion.LEER},
        "contrato":   set(),
    },

    Rol.LEGAL_COMPLIANCE: {
        "cancion":    {Accion.LEER, Accion.AUDITAR},
        "ganancia":   {Accion.LEER, Accion.AUDITAR},
        "metrica":    {Accion.LEER, Accion.AUDITAR},
        "metadato":   {Accion.LEER, Accion.AUDITAR},
        "contrato":   {Accion.LEER, Accion.AUDITAR},
    },

    Rol.ANALITICA: {
        "cancion":    {Accion.LEER},          # solo datos agregados
        "ganancia":   set(),                  # no accede a finanzas individuales
        "metrica":    {Accion.LEER},
        "metadato":   {Accion.LEER},
        "contrato":   set(),
    },

    Rol.ADMINISTRATIVO: {
        "cancion":    set(),
        "ganancia":   {Accion.LEER},          # nomina/impuestos agregados
        "metrica":    set(),
        "metadato":   {Accion.LEER},
        "contrato":   {Accion.LEER},
    },

    Rol.PLATAFORMA_EXTERNA: {
        "cancion":    {Accion.LEER},          # solo sus artistas via API
        "ganancia":   set(),
        "metrica":    {Accion.LEER},          # solo metricas de su plataforma
        "metadato":   {Accion.LEER},
        "contrato":   set(),
    },

    Rol.PRODUCTOR_EDITORIAL: {               # rol futuro - permisos basicos
        "cancion":    {Accion.LEER, Accion.ESCRIBIR},
        "ganancia":   {Accion.LEER},
        "metrica":    {Accion.LEER},
        "metadato":   {Accion.LEER, Accion.ESCRIBIR},
        "contrato":   {Accion.LEER},
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# 4.  MOTOR DE CONTROL DE ACCESO
# ══════════════════════════════════════════════════════════════════════════════

class MotorAcceso:
    """
    Evalua solicitudes de acceso aplicando RBAC -> MAC -> DAC en ese orden.
    Registra TODOS los intentos (permitidos y denegados) para auditoria.
    """

    def __init__(self):
        self.log = []
        self.permisos_dac = []

    # -- helpers --------------------------------------------------------------

    def _registrar(self, usuario, recurso, accion, resultado, motivo, modelo):
        entrada = RegistroAcceso(
            timestamp=datetime.now(),
            usuario_id=usuario.id,
            usuario_nombre=usuario.nombre,
            usuario_rol=usuario.rol.value,
            recurso_id=recurso.id,
            recurso_nombre=recurso.nombre,
            accion=accion.value,
            resultado=resultado,
            motivo=motivo,
            modelo_aplicado=modelo,
        )
        self.log.append(entrada)
        return entrada

    def _verificar_rbac(self, usuario, recurso, accion):
        """Comprueba si el rol tiene la accion sobre el tipo de recurso."""
        permisos_rol = RBAC_MATRIZ.get(usuario.rol, {})
        acciones_permitidas = permisos_rol.get(recurso.tipo, set())
        if accion in acciones_permitidas:
            return True, "Rol autorizado por RBAC"
        return False, (f"Rol '{usuario.rol.value}' sin permiso "
                       f"'{accion.value}' sobre '{recurso.tipo}'")

    def _verificar_mac(self, usuario, recurso, accion):
        """
        Comprueba que el nivel de autorizacion del usuario >= clasificacion del recurso.
        Regla adicional de embargo: datos CONFIDENCIAL/SECRETO con embargo activo
        solo accesibles por LEGAL o propietario.
        """
        if usuario.nivel_autorizacion.value < recurso.clasificacion.value:
            return False, (
                f"Nivel MAC insuficiente: usuario tiene "
                f"'{usuario.nivel_autorizacion.name}', recurso requiere "
                f"'{recurso.clasificacion.name}'"
            )

        # Regla de embargo
        if recurso.fecha_embargo and datetime.now() < recurso.fecha_embargo:
            if usuario.rol not in (Rol.LEGAL_COMPLIANCE,) and \
               usuario.id != recurso.propietario_id:
                return False, (
                    f"ALERTA EMBARGO: acceso restringido hasta "
                    f"{recurso.fecha_embargo.strftime('%Y-%m-%d')} "
                    f"(fecha oficial de lanzamiento)"
                )

        return True, "Nivel MAC autorizado"

    def _verificar_dac(self, usuario, recurso, accion):
        """Busca un permiso delegado vigente que cubra esta solicitud."""
        for p in self.permisos_dac:
            if (p.recurso_id == recurso.id and
                    p.otorgado_a == usuario.id and
                    accion in p.acciones and
                    p.esta_vigente()):
                dias = (p.expira - datetime.now()).days
                return True, f"Permiso DAC vigente (expira en {dias} dia(s))"
        return False, "Sin permiso DAC para este recurso/accion"

    def _es_propietario(self, usuario, recurso):
        return usuario.id == recurso.propietario_id

    def _manager_representa_artista(self, usuario, recurso):
        return recurso.propietario_id in usuario.artistas_representados

    def _api_tiene_acceso(self, usuario, recurso):
        return usuario.plataforma_id == recurso.propietario_id

    # -- punto de entrada principal -------------------------------------------

    def solicitar_acceso(self, usuario, recurso, accion):
        """
        Evalua una solicitud de acceso y retorna True/False.
        Evaluacion: RBAC -> contexto/propietario -> MAC -> DAC (fallback).
        """

        # Paso 1: RBAC
        rbac_ok, rbac_msg = self._verificar_rbac(usuario, recurso, accion)
        if not rbac_ok:
            # Excepcion: DAC puede conceder aunque RBAC lo niegue
            dac_ok, dac_msg = self._verificar_dac(usuario, recurso, accion)
            if dac_ok:
                e = self._registrar(usuario, recurso, accion, "PERMITIDO", dac_msg, "DAC")
                print(e)
                return True
            e = self._registrar(usuario, recurso, accion, "DENEGADO", rbac_msg, "RBAC")
            print(e)
            return False

        # Paso 2: Contexto de acceso
        es_propietario = self._es_propietario(usuario, recurso)

        if usuario.rol == Rol.ARTISTA and not es_propietario:
            motivo = "Artista sin acceso a datos de otro artista (privacidad)"
            e = self._registrar(usuario, recurso, accion, "DENEGADO", motivo, "RBAC+DAC")
            print(e)
            return False

        if usuario.rol == Rol.MANAGER and not self._manager_representa_artista(usuario, recurso):
            motivo = "Conflicto de interes: artista no representado por este manager"
            e = self._registrar(usuario, recurso, accion, "DENEGADO", motivo, "RBAC+DAC")
            print(e)
            return False

        # Administrativos externos (contador) solo acceden via DAC
        if usuario.rol == Rol.ADMINISTRATIVO and not es_propietario:
            dac_ok, dac_msg = self._verificar_dac(usuario, recurso, accion)
            if not dac_ok:
                motivo = "Administrativo externo requiere delegacion DAC del propietario"
                e = self._registrar(usuario, recurso, accion, "DENEGADO", motivo, "DAC")
                print(e)
                return False

        if usuario.rol == Rol.PLATAFORMA_EXTERNA and not self._api_tiene_acceso(usuario, recurso):
            motivo = "API externa sin acceso a datos de otra plataforma"
            e = self._registrar(usuario, recurso, accion, "DENEGADO", motivo, "RBAC")
            print(e)
            return False

        # Paso 3: MAC
        mac_ok, mac_msg = self._verificar_mac(usuario, recurso, accion)
        if not mac_ok:
            e = self._registrar(usuario, recurso, accion, "DENEGADO", mac_msg, "MAC")
            print(e)
            return False

        # Paso 4: TODO OK
        modelo = "RBAC+MAC(propietario)" if es_propietario else "RBAC+MAC"
        motivo = f"{rbac_msg} | {mac_msg}"
        e = self._registrar(usuario, recurso, accion, "PERMITIDO", motivo, modelo)
        print(e)
        return True

    # -- DAC: gestion de permisos delegados -----------------------------------

    def delegar_permiso(self, propietario, recurso, beneficiario, acciones, dias=30):
        """El propietario de un recurso delega acceso temporal a otro usuario."""
        if propietario.id != recurso.propietario_id:
            raise PermissionError(f"{propietario} no es propietario de '{recurso}'")
        permiso = PermisoDelegado(
            id=str(uuid.uuid4())[:8],
            recurso_id=recurso.id,
            otorgado_por=propietario.id,
            otorgado_a=beneficiario.id,
            acciones=acciones,
            expira=datetime.now() + timedelta(days=dias),
        )
        self.permisos_dac.append(permiso)
        print(f"\n  [DAC] '{propietario.nombre}' delega acceso a "
              f"'{beneficiario.nombre}' sobre '{recurso.nombre}' "
              f"({', '.join(a.value for a in acciones)}) por {dias} dias.\n")
        return permiso

    # -- reporte de auditoria -------------------------------------------------

    def imprimir_log(self):
        print("\n" + "=" * 80)
        print("  REGISTRO COMPLETO DE AUDITORIA - TUNEBOX")
        print("=" * 80)
        permitidos = sum(1 for e in self.log if e.resultado == "PERMITIDO")
        denegados  = sum(1 for e in self.log if e.resultado == "DENEGADO")
        print(f"  Total intentos: {len(self.log)}  |  "
              f"PERMITIDOS: {permitidos}  |  DENEGADOS: {denegados}\n")
        for entrada in self.log:
            print(f"  {entrada}")
        print("=" * 80 + "\n")

    def imprimir_matriz_rbac(self):
        """Imprime la matriz RBAC de forma legible."""
        print("\n" + "=" * 80)
        print("  MATRIZ RBAC - TuneBox  (Rol x Recurso x Acciones)")
        print("=" * 80)
        tipos = ["cancion", "ganancia", "metrica", "metadato", "contrato"]
        header = f"  {'ROL':<28}" + "".join(f"{t:<14}" for t in tipos)
        print(header)
        print("  " + "-" * 76)
        for rol, permisos in RBAC_MATRIZ.items():
            fila = f"  {rol.value:<28}"
            for t in tipos:
                acciones = permisos.get(t, set())
                siglas = "".join(sorted(a.value[0].upper() for a in acciones))
                fila += f"{siglas or '--':<14}"
            print(fila)
        print("\n  Leyenda: L=leer, E=escribir, C=compartir, A=auditar, D=eliminar")
        print("=" * 80 + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# 5.  ESCENARIO DE SIMULACION
# ══════════════════════════════════════════════════════════════════════════════

def construir_escenario():
    """Construye usuarios y recursos del mundo TuneBox."""
    motor = MotorAcceso()
    fecha_embargo = datetime.now() + timedelta(days=10)

    usuarios = {
        "sofia": Usuario(
            id="u001", nombre="Sofia Ramos", rol=Rol.ARTISTA,
            nivel_autorizacion=ClasificacionMAC.SECRETO),
        "carlos": Usuario(
            id="u002", nombre="Carlos Vega", rol=Rol.ARTISTA,
            nivel_autorizacion=ClasificacionMAC.SECRETO),
        "manager_a": Usuario(
            id="u003", nombre="Laura Mendez", rol=Rol.MANAGER,
            nivel_autorizacion=ClasificacionMAC.SECRETO,
            artistas_representados=["u001"]),   # representa a Sofia, NO a Carlos
        "marketing": Usuario(
            id="u004", nombre="Pedro Torres", rol=Rol.MARKETING,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL),
        "legal": Usuario(
            id="u005", nombre="Ana Rios", rol=Rol.LEGAL_COMPLIANCE,
            nivel_autorizacion=ClasificacionMAC.SECRETO),
        "analitica": Usuario(
            id="u006", nombre="Luis Parra", rol=Rol.ANALITICA,
            nivel_autorizacion=ClasificacionMAC.PUBLICO),
        "admin": Usuario(
            id="u007", nombre="Maria Gil", rol=Rol.ADMINISTRATIVO,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL),
        "spotify_api": Usuario(
            id="u008", nombre="Spotify API", rol=Rol.PLATAFORMA_EXTERNA,
            nivel_autorizacion=ClasificacionMAC.PUBLICO,
            plataforma_id="u001"),   # solo accede a datos de Sofia
        "contador": Usuario(
            id="u009", nombre="Rodrigo Salas (Contador externo)",
            rol=Rol.ADMINISTRATIVO,
            nivel_autorizacion=ClasificacionMAC.SECRETO),
        "prod_editorial": Usuario(
            id="u010", nombre="Diana Cruz", rol=Rol.PRODUCTOR_EDITORIAL,
            nivel_autorizacion=ClasificacionMAC.CONFIDENCIAL),
    }

    recursos = {
        "cancion_sofia": Recurso(
            id="r001", nombre="Track 'Noche Eterna' - Sofia",
            tipo="cancion", clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="u001"),
        "ganancias_sofia": Recurso(
            id="r002", nombre="Ganancias Q1-2026 - Sofia",
            tipo="ganancia", clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u001"),
        "lanzamiento_futuro_sofia": Recurso(
            id="r003", nombre="Album 'Eclipse' (PRELANZAMIENTO) - Sofia",
            tipo="metrica", clasificacion=ClasificacionMAC.CONFIDENCIAL,
            propietario_id="u001", fecha_embargo=fecha_embargo),
        "ganancias_carlos": Recurso(
            id="r004", nombre="Ganancias Q1-2026 - Carlos",
            tipo="ganancia", clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u002"),
        "cancion_carlos": Recurso(
            id="r005", nombre="Track 'Solar' - Carlos",
            tipo="cancion", clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="u002"),
        "metricas_agregadas": Recurso(
            id="r006", nombre="Metricas Agregadas Plataforma",
            tipo="metrica", clasificacion=ClasificacionMAC.PUBLICO,
            propietario_id="sistema"),
        "contrato_sofia": Recurso(
            id="r007", nombre="Contrato Distribucion - Sofia",
            tipo="contrato", clasificacion=ClasificacionMAC.SECRETO,
            propietario_id="u001"),
    }

    return usuarios, recursos, motor


def ejecutar_simulacion():
    """Ejecuta todos los casos de uso del enunciado."""

    def sep(titulo):
        print(f"\n{'=' * 70}\n  CASO: {titulo}\n{'=' * 70}")

    usuarios, recursos, motor = construir_escenario()

    print("""
+----------------------------------------------------------------------+
|       TUNEBOX - Simulacion de Control de Acceso RBAC + DAC + MAC     |
+----------------------------------------------------------------------+
""")

    motor.imprimir_matriz_rbac()

    # CASO 1: Artista accede a SUS propios datos
    sep("1. Artista accede a sus propios datos [esperado: PERMITIDO]")
    motor.solicitar_acceso(usuarios["sofia"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["sofia"], recursos["cancion_sofia"], Accion.ESCRIBIR)

    # CASO 2: Artista intenta ver datos de otro artista
    sep("2. Artista intenta ver datos de artista rival [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["carlos"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["sofia"], recursos["cancion_carlos"], Accion.LEER)

    # CASO 3: Manager accede a datos de su artista representado
    sep("3. Manager accede a datos de SU artista [esperado: PERMITIDO]")
    motor.solicitar_acceso(usuarios["manager_a"], recursos["ganancias_sofia"], Accion.LEER)

    # CASO 4: CONFLICTO - Manager intenta ver datos de artista rival
    sep("4. CONFLICTO: Manager accede a artista NO representado [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["manager_a"], recursos["ganancias_carlos"], Accion.LEER)

    # CASO 5: Marketing intenta filtrar lanzamiento bajo embargo
    sep("5. CONFLICTO EMBARGO: Marketing lee antes de fecha oficial [esperado: DENEGADO]")
    motor.solicitar_acceso(usuarios["marketing"], recursos["lanzamiento_futuro_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["marketing"], recursos["metricas_agregadas"], Accion.LEER)
    motor.solicitar_acceso(usuarios["marketing"], recursos["ganancias_sofia"], Accion.LEER)

    # CASO 6: Legal/Compliance - auditoria irrestricta
    sep("6. Legal audita datos SECRETOS [esperado: PERMITIDO + registrado]")
    motor.solicitar_acceso(usuarios["legal"], recursos["ganancias_sofia"], Accion.AUDITAR)
    motor.solicitar_acceso(usuarios["legal"], recursos["lanzamiento_futuro_sofia"], Accion.AUDITAR)
    motor.solicitar_acceso(usuarios["legal"], recursos["contrato_sofia"], Accion.AUDITAR)

    # CASO 7: Analitica - solo metricas agregadas
    sep("7. Analitica accede a metricas [esperado: PERMITIDO solo publicas]")
    motor.solicitar_acceso(usuarios["analitica"], recursos["metricas_agregadas"], Accion.LEER)
    motor.solicitar_acceso(usuarios["analitica"], recursos["ganancias_sofia"], Accion.LEER)

    # CASO 8: API externa - acceso solo a sus datos
    sep("8. Spotify API - acceso solo a sus artistas [esperado: mixto]")
    motor.solicitar_acceso(usuarios["spotify_api"], recursos["cancion_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["spotify_api"], recursos["cancion_carlos"], Accion.LEER)

    # CASO 9: DAC - Artista comparte dashboard con contador externo
    sep("9. DAC: Artista delega acceso temporal a contador externo")
    motor.delegar_permiso(
        propietario=usuarios["sofia"],
        recurso=recursos["ganancias_sofia"],
        beneficiario=usuarios["contador"],
        acciones=[Accion.LEER],
        dias=30
    )
    motor.solicitar_acceso(usuarios["contador"], recursos["ganancias_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["contador"], recursos["ganancias_carlos"], Accion.LEER)

    # CASO 10: Rol futuro - Productor Editorial
    sep("10. Nuevo Rol: Productor Editorial accede a canciones y ganancias")
    motor.solicitar_acceso(usuarios["prod_editorial"], recursos["cancion_sofia"], Accion.LEER)
    motor.solicitar_acceso(usuarios["prod_editorial"], recursos["ganancias_sofia"], Accion.LEER)

    # LOG COMPLETO
    motor.imprimir_log()

    # CLASIFICACION MAC
    print("=" * 70)
    print("  CLASIFICACION DE DATOS SEGUN MAC - TuneBox")
    print("=" * 70)
    clasificaciones = [
        ("PUBLICO (nivel 1)",
         "Metricas agregadas, nombres artistas, info publica de lanzamientos",
         "Todos los roles autenticados, APIs externas, Analitica"),
        ("CONFIDENCIAL (nivel 2)",
         "Datos de lanzamientos futuros (embargo), campanas de marketing",
         "Marketing (con restriccion embargo), Admin, Manager, Artista propietario"),
        ("SECRETO (nivel 3)",
         "Ganancias individuales, contratos de distribucion, datos fiscales",
         "Artista (propios), Manager (representados), Legal, Admin agregado, DAC"),
    ]
    for nivel, desc, acceso in clasificaciones:
        print(f"\n  [*] {nivel}")
        print(f"      Datos  : {desc}")
        print(f"      Acceso : {acceso}")
    print("\n" + "=" * 70)
    print("\n  Simulacion completada. Revise el log de auditoria para el informe.\n")


# ══════════════════════════════════════════════════════════════════════════════
# 6.  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    ejecutar_simulacion()