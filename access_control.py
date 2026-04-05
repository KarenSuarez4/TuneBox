from __future__ import annotations

from datetime import datetime, timedelta
import uuid

from models import Accion, PermisoDelegado, Recurso, RegistroAcceso, Rol, Usuario


RBAC_MATRIZ: dict[Rol, dict[str, set[Accion]]] = {
    Rol.ARTISTA: {
        "cancion": {Accion.LEER, Accion.ESCRIBIR, Accion.COMPARTIR},
        "ganancia": {Accion.LEER},
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER, Accion.ESCRIBIR},
        "contrato": {Accion.LEER},
    },
    Rol.MANAGER: {
        "cancion": {Accion.LEER},
        "ganancia": {Accion.LEER},
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER, Accion.ESCRIBIR},
        "contrato": {Accion.LEER},
    },
    Rol.MARKETING: {
        "cancion": {Accion.LEER},
        "ganancia": set(),
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER},
        "contrato": set(),
    },
    Rol.LEGAL_COMPLIANCE: {
        "cancion": {Accion.LEER, Accion.AUDITAR},
        "ganancia": {Accion.LEER, Accion.AUDITAR},
        "metrica": {Accion.LEER, Accion.AUDITAR},
        "metadato": {Accion.LEER, Accion.AUDITAR},
        "contrato": {Accion.LEER, Accion.AUDITAR},
    },
    Rol.ANALITICA: {
        "cancion": {Accion.LEER},
        "ganancia": set(),
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER},
        "contrato": set(),
    },
    Rol.ADMINISTRATIVO: {
        "cancion": set(),
        "ganancia": {Accion.LEER},
        "metrica": set(),
        "metadato": {Accion.LEER},
        "contrato": {Accion.LEER},
    },
    Rol.PLATAFORMA_EXTERNA: {
        "cancion": {Accion.LEER},
        "ganancia": set(),
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER},
        "contrato": set(),
    },
    Rol.PRODUCTOR_EDITORIAL: {
        "cancion": {Accion.LEER, Accion.ESCRIBIR},
        "ganancia": {Accion.LEER},
        "metrica": {Accion.LEER},
        "metadato": {Accion.LEER, Accion.ESCRIBIR},
        "contrato": {Accion.LEER},
    },
}


class MotorAcceso:
    """Evalua solicitudes de acceso aplicando RBAC, contexto, MAC y DAC."""

    def __init__(self) -> None:
        """Inicializa el estado de auditoria y delegaciones DAC activas."""
        self.log: list[RegistroAcceso] = []
        self.permisos_dac: list[PermisoDelegado] = []

    def _registrar(
        self,
        usuario: Usuario,
        recurso: Recurso,
        accion: Accion,
        resultado: str,
        motivo: str,
        modelo: str,
    ) -> RegistroAcceso:
        """Crea una entrada de auditoria y la agrega al log interno."""
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

    def _verificar_rbac(self, usuario: Usuario, recurso: Recurso, accion: Accion) -> tuple[bool, str]:
        """Valida si el rol tiene permiso para la accion y tipo de recurso."""
        permisos_rol = RBAC_MATRIZ.get(usuario.rol, {})
        acciones_permitidas = permisos_rol.get(recurso.tipo, set())
        if accion in acciones_permitidas:
            return True, "Rol autorizado por RBAC"
        return False, (
            f"Rol '{usuario.rol.value}' sin permiso "
            f"'{accion.value}' sobre '{recurso.tipo}'"
        )

    def _verificar_mac(self, usuario: Usuario, recurso: Recurso) -> tuple[bool, str]:
        """Aplica validaciones MAC por nivel de clasificacion y embargo temporal."""
        if usuario.nivel_autorizacion.value < recurso.clasificacion.value:
            return False, (
                "Nivel MAC insuficiente: usuario tiene "
                f"'{usuario.nivel_autorizacion.name}', recurso requiere "
                f"'{recurso.clasificacion.name}'"
            )

        if recurso.fecha_embargo and datetime.now() < recurso.fecha_embargo:
            if usuario.rol not in (Rol.LEGAL_COMPLIANCE,) and usuario.id != recurso.propietario_id:
                return False, (
                    "ALERTA EMBARGO: acceso restringido hasta "
                    f"{recurso.fecha_embargo.strftime('%Y-%m-%d')} "
                    "(fecha oficial de lanzamiento)"
                )

        return True, "Nivel MAC autorizado"

    def _verificar_dac(self, usuario: Usuario, recurso: Recurso, accion: Accion) -> tuple[bool, str]:
        """Verifica si existe una delegacion DAC vigente para este acceso."""
        for permiso in self.permisos_dac:
            if (
                permiso.recurso_id == recurso.id
                and permiso.otorgado_a == usuario.id
                and accion in permiso.acciones
                and permiso.esta_vigente()
            ):
                dias = (permiso.expira - datetime.now()).days
                return True, f"Permiso DAC vigente (expira en {dias} dia(s))"
        return False, "Sin permiso DAC para este recurso/accion"

    @staticmethod
    def _es_propietario(usuario: Usuario, recurso: Recurso) -> bool:
        """Indica si el usuario es el propietario directo del recurso."""
        return usuario.id == recurso.propietario_id

    @staticmethod
    def _manager_representa_artista(usuario: Usuario, recurso: Recurso) -> bool:
        """Determina si el manager representa al artista propietario del recurso."""
        return recurso.propietario_id in usuario.artistas_representados

    @staticmethod
    def _api_tiene_acceso(usuario: Usuario, recurso: Recurso) -> bool:
        """Restringe plataformas externas a sus recursos vinculados."""
        return usuario.plataforma_id == recurso.propietario_id

    def evaluar_acceso(self, usuario: Usuario, recurso: Recurso, accion: Accion) -> tuple[bool, RegistroAcceso]:
        """Versión silenciosa para GUI y CLI. Retorna (permitido, registro)."""
        rbac_ok, rbac_msg = self._verificar_rbac(usuario, recurso, accion)
        if not rbac_ok:
            dac_ok, dac_msg = self._verificar_dac(usuario, recurso, accion)
            if dac_ok:
                return True, self._registrar(usuario, recurso, accion, "PERMITIDO", dac_msg, "DAC")
            return False, self._registrar(usuario, recurso, accion, "DENEGADO", rbac_msg, "RBAC")

        es_propietario = self._es_propietario(usuario, recurso)

        if usuario.rol == Rol.ARTISTA and not es_propietario:
            dac_ok, dac_msg = self._verificar_dac(usuario, recurso, accion)
            if dac_ok:
                return True, self._registrar(usuario, recurso, accion, "PERMITIDO", dac_msg, "DAC")
            return False, self._registrar(
                usuario,
                recurso,
                accion,
                "DENEGADO",
                "Artista sin acceso a datos de otro artista (privacidad)",
                "RBAC+DAC",
            )

        if usuario.rol == Rol.MANAGER and not self._manager_representa_artista(usuario, recurso):
            dac_ok, dac_msg = self._verificar_dac(usuario, recurso, accion)
            if dac_ok:
                return True, self._registrar(usuario, recurso, accion, "PERMITIDO", dac_msg, "DAC")
            return False, self._registrar(
                usuario,
                recurso,
                accion,
                "DENEGADO",
                "Conflicto de interes: artista no representado por este manager",
                "RBAC+DAC",
            )

        if usuario.rol == Rol.ADMINISTRATIVO and not es_propietario:
            dac_ok, _ = self._verificar_dac(usuario, recurso, accion)
            if not dac_ok:
                return False, self._registrar(
                    usuario,
                    recurso,
                    accion,
                    "DENEGADO",
                    "Administrativo externo requiere delegacion DAC del propietario",
                    "DAC",
                )

        if usuario.rol == Rol.PLATAFORMA_EXTERNA and not self._api_tiene_acceso(usuario, recurso):
            return False, self._registrar(
                usuario,
                recurso,
                accion,
                "DENEGADO",
                "API externa sin acceso a datos de otra plataforma",
                "RBAC",
            )

        mac_ok, mac_msg = self._verificar_mac(usuario, recurso)
        if not mac_ok:
            return False, self._registrar(usuario, recurso, accion, "DENEGADO", mac_msg, "MAC")

        modelo = "RBAC+MAC(propietario)" if es_propietario else "RBAC+MAC"
        motivo = f"{rbac_msg} | {mac_msg}"
        return True, self._registrar(usuario, recurso, accion, "PERMITIDO", motivo, modelo)

    def solicitar_acceso(self, usuario: Usuario, recurso: Recurso, accion: Accion) -> bool:
        """Evalua acceso e imprime el registro para escenarios de consola."""
        permitido, entrada = self.evaluar_acceso(usuario, recurso, accion)
        print(entrada)
        return permitido

    def delegar_permiso(
        self,
        propietario: Usuario,
        recurso: Recurso,
        beneficiario: Usuario,
        acciones: list[Accion],
        dias: int = 30,
    ) -> PermisoDelegado:
        """Crea una delegacion DAC y muestra un mensaje explicativo en consola."""
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
        print(
            f"\n  [DAC] '{propietario.nombre}' delega acceso a "
            f"'{beneficiario.nombre}' sobre '{recurso.nombre}' "
            f"({', '.join(a.value for a in acciones)}) por {dias} dias.\n"
        )
        return permiso

    def delegar_permiso_silencioso(
        self,
        propietario: Usuario,
        recurso: Recurso,
        beneficiario: Usuario,
        acciones: list[Accion],
        dias: int = 30,
    ) -> PermisoDelegado:
        """Crea una delegacion DAC sin imprimir, para uso de la GUI."""
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
        return permiso

    def imprimir_log(self) -> None:
        """Imprime en consola el resumen y detalle del log de auditoria."""
        print("\n" + "=" * 80)
        print("  REGISTRO COMPLETO DE AUDITORÍA - TUNEBOX")
        print("=" * 80)
        permitidos = sum(1 for e in self.log if e.resultado == "PERMITIDO")
        denegados = sum(1 for e in self.log if e.resultado == "DENEGADO")
        print(
            f"  Total intentos: {len(self.log)}  |  "
            f"PERMITIDOS: {permitidos}  |  DENEGADOS: {denegados}\n"
        )
        for entrada in self.log:
            print(f"  {entrada}")
        print("=" * 80 + "\n")

    def imprimir_matriz_rbac(self) -> None:
        """Muestra en consola la matriz RBAC resumida por rol y tipo de recurso."""
        print("\n" + "=" * 80)
        print("  MATRIZ RBAC - TuneBox  (Rol x Recurso x Acciones)")
        print("=" * 80)
        tipos = ["cancion", "ganancia", "metrica", "metadato", "contrato"]
        header = f"  {'ROL':<28}" + "".join(f"{t:<14}" for t in tipos)
        print(header)
        print("  " + "-" * 76)
        for rol, permisos in RBAC_MATRIZ.items():
            fila = f"  {rol.value:<28}"
            for tipo in tipos:
                acciones = permisos.get(tipo, set())
                siglas = "".join(sorted(a.value[0].upper() for a in acciones))
                fila += f"{siglas or '--':<14}"
            print(fila)
        print("\n  Leyenda: L=leer, E=escribir, C=compartir, A=auditar, D=eliminar")
        print("=" * 80 + "\n")
