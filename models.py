from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class ClasificacionMAC(Enum):
    """Niveles de sensibilidad de datos segun MAC."""

    PUBLICO = 1
    CONFIDENCIAL = 2
    SECRETO = 3


class Rol(Enum):
    """Roles de la plataforma TuneBox."""

    ARTISTA = "Artista/Productor"
    MANAGER = "Manager"
    MARKETING = "Equipo de Marketing"
    LEGAL_COMPLIANCE = "Legal/Compliance"
    ANALITICA = "Equipo de Analitica"
    ADMINISTRATIVO = "Administrativo"
    PLATAFORMA_EXTERNA = "Plataforma Externa (API)"
    PRODUCTOR_EDITORIAL = "Productor Editorial"


class Accion(Enum):
    """Acciones posibles sobre un recurso."""

    LEER = "leer"
    ESCRIBIR = "escribir"
    ELIMINAR = "eliminar"
    COMPARTIR = "compartir"
    AUDITAR = "auditar"


@dataclass
class Recurso:
    """Representa cualquier activo de informacion dentro de TuneBox."""

    id: str
    nombre: str
    tipo: str
    clasificacion: ClasificacionMAC
    propietario_id: str
    fecha_embargo: Optional[datetime] = None

    def __str__(self) -> str:
        embargo = (
            f", embargo hasta {self.fecha_embargo.strftime('%Y-%m-%d')}"
            if self.fecha_embargo
            else ""
        )
        return f"[{self.tipo.upper()}] '{self.nombre}' ({self.clasificacion.name}{embargo})"


@dataclass
class Usuario:
    """Representa a cualquier actor del sistema."""

    id: str
    nombre: str
    rol: Rol
    nivel_autorizacion: ClasificacionMAC
    artistas_representados: list = field(default_factory=list)
    plataforma_id: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.nombre} [{self.rol.value}]"


@dataclass
class PermisoDelegado:
    """DAC: permiso temporal que un propietario otorga a un tercero."""

    id: str
    recurso_id: str
    otorgado_por: str
    otorgado_a: str
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
    resultado: str
    motivo: str
    modelo_aplicado: str

    def __str__(self) -> str:
        icono = "OK " if self.resultado == "PERMITIDO" else "NO "
        return (
            f"{icono} [{self.timestamp.strftime('%H:%M:%S')}] "
            f"{self.usuario_nombre} ({self.usuario_rol}) -> "
            f"{self.accion.upper()} '{self.recurso_nombre}' | "
            f"{self.resultado} | {self.motivo} [{self.modelo_aplicado}]"
        )
