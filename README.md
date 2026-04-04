# TuneBox

Sistema de control de acceso integrado para una plataforma de distribución musical, con simulación de políticas de seguridad RBAC + DAC + MAC sobre activos de información de artistas.

---

## Tabla de contenidos

1. [Descripción general](#descripción-general)
2. [Modelos de control de acceso](#modelos-de-control-de-acceso)
3. [Arquitectura actual del proyecto](#arquitectura-actual-del-proyecto)
4. [Entidades y reglas principales](#entidades-y-reglas-principales)
5. [Flujo de evaluación de acceso](#flujo-de-evaluación-de-acceso)
6. [Matriz RBAC](#matriz-rbac)
7. [Escenario de simulación](#escenario-de-simulación)
8. [Interfaz gráfica educativa (GUI)](#interfaz-gráfica-educativa-gui)
9. [Modo consola (CLI)](#modo-consola-cli)
10. [Registro de auditoría](#registro-de-auditoría)
11. [Requisitos](#requisitos)
12. [Instalación y ejecución](#instalación-y-ejecución)
13. [Estructura del código](#estructura-del-código)

---

## Descripción general

TuneBox es un sistema académico/demostrativo orientado al estudio del control de acceso sobre recursos sensibles de una plataforma musical (canciones, ganancias, métricas, metadatos y contratos).

El motor combina tres modelos clásicos:

- RBAC (Role-Based Access Control): permisos por rol.
- DAC (Discretionary Access Control): delegaciones temporales por propietario.
- MAC (Mandatory Access Control): clasificaciones jerárquicas y embargo de lanzamientos.

Cada intento de acceso (permitido o denegado) queda trazado en un log de auditoría con su motivo y el modelo aplicado.

---

## Modelos de control de acceso

### RBAC - Role-Based Access Control

Define permisos por Rol x Tipo de recurso x Acción. Si una acción no está en la matriz del rol, el acceso se deniega (o puede habilitarse por DAC como excepción).

### DAC - Discretionary Access Control

El propietario de un recurso puede delegar acceso temporal a otro usuario con:

- recurso específico
- usuario beneficiario
- acciones autorizadas
- fecha de expiración (por defecto 30 días)

En código existen dos caminos:

- `delegar_permiso()`: delega e imprime mensaje (uso CLI).
- `delegar_permiso_silencioso()`: delega sin imprimir (uso GUI).

### MAC - Mandatory Access Control

Aplica la regla:

`nivel_autorizacion(usuario) >= clasificacion(recurso)`

Además, si un recurso tiene embargo activo (`fecha_embargo` en el futuro), solo puede acceder:

- el propietario del recurso
- `Legal/Compliance`

---

## Arquitectura actual del proyecto

La versión actual está modularizada en varios archivos (ya no monolítica):

```text
TuneBox/
├── main.py            # Punto de entrada y selector de modo (gui/cli)
├── models.py          # Enums y dataclasses del dominio
├── access_control.py  # Matriz RBAC y MotorAcceso
├── scenario.py        # Construcción de datos y simulación CLI
├── ui.py              # Interfaz gráfica educativa con Tkinter
├── mainoriginal.py    # Versión legacy previa (referencia histórica)
└── README.md          # Documentación
```

---

## Entidades y reglas principales

### Enumeraciones

- `ClasificacionMAC`: `PUBLICO`, `CONFIDENCIAL`, `SECRETO`
- `Rol`: `ARTISTA`, `MANAGER`, `MARKETING`, `LEGAL_COMPLIANCE`, `ANALITICA`, `ADMINISTRATIVO`, `PLATAFORMA_EXTERNA`, `PRODUCTOR_EDITORIAL`
- `Accion`: `LEER`, `ESCRIBIR`, `ELIMINAR`, `COMPARTIR`, `AUDITAR`

### Estructuras de datos

- `Recurso`: activo protegido, con tipo, clasificación, propietario y embargo opcional.
- `Usuario`: actor con rol, nivel MAC y atributos de contexto (representación y plataforma).
- `PermisoDelegado`: delegación temporal DAC.
- `RegistroAcceso`: evento auditable de cada evaluación.

### Reglas de contexto adicionales

Sobre RBAC y MAC se aplican restricciones adicionales en el motor:

- Artista: solo sus propios recursos (excepto si hay DAC vigente).
- Manager: solo artistas representados (excepto DAC).
- Administrativo: para datos no propios requiere DAC del propietario.
- Plataforma externa: solo recursos vinculados a su `plataforma_id`.

---

## Flujo de evaluación de acceso

Cuando se evalúa una solicitud (`evaluar_acceso` o `solicitar_acceso`), el motor aplica:

```text
[1] RBAC
    ├─ si falla -> intenta DAC
    │   ├─ DAC ok -> PERMITIDO (DAC)
    │   └─ DAC no -> DENEGADO (RBAC)
    └─ si pasa -> continúa

[2] Reglas de contexto (propietario/representacion/plataforma/admin)
    ├─ si falla -> puede intentar DAC según el caso
    └─ si pasa -> continúa

[3] MAC (nivel + embargo)
    ├─ si falla -> DENEGADO (MAC)
    └─ si pasa -> PERMITIDO (RBAC+MAC)
```

---

## Matriz RBAC

Leyenda: `L`=leer, `E`=escribir, `C`=compartir, `A`=auditar, `D`=eliminar, `--`=sin acceso.

| Rol | cancion | ganancia | metrica | metadato | contrato |
|-----|---------|----------|---------|----------|----------|
| Artista/Productor | L E C | L | L | L E | L |
| Manager | L | L | L | L E | L |
| Equipo de Marketing | L | -- | L | L | -- |
| Legal/Compliance | L A | L A | L A | L A | L A |
| Equipo de Analitica | L | -- | L | L | -- |
| Administrativo | -- | L | -- | L | L |
| Plataforma Externa (API) | L | -- | L | L | -- |
| Productor Editorial | L E | L | L | L E | L |

Notas operativas:

- Manager: acceso condicionado a artistas representados.
- Marketing: métricas sujetas a embargo.
- Administrativo externo: acceso individual mediante DAC.

---

## Escenario de simulación

`scenario.py` construye un entorno base con:

- 10 usuarios (artistas, manager, marketing, legal, analítica, administrativos, API externa y productor editorial)
- 7 recursos (canciones, ganancias, métricas agregadas, contrato y un recurso con embargo)
- 1 motor de acceso (`MotorAcceso`)

Los casos incluyen:

1. acceso propio de artista
2. intento de acceso cruzado entre artistas
3. manager sobre artista representado
4. manager sobre no representado
5. marketing con y sin embargo
6. auditoría legal en datos secretos
7. analítica sobre público vs secreto
8. API externa sobre artista propio vs ajeno
9. delegación DAC a contador externo
10. validación del rol Productor Editorial

---

## Interfaz gráfica educativa (GUI)

La GUI está implementada en `ui.py` con Tkinter y se lanza con `lanzar_gui()`.

Incluye 4 pestañas:

1. `Laboratorio`: simulación de solicitudes y explicación del resultado.
2. `Guia`: resumen didáctico de RBAC, DAC y MAC.
3. `Matriz RBAC`: tabla visual con leyendas y notas de contexto.
4. `Auditoria`: historial de eventos y permisos DAC vigentes.

Funciones destacadas de la GUI:

- evaluación interactiva usando `motor.evaluar_acceso()`
- badge del último resultado (permitido/denegado)
- creación de permisos DAC desde formulario
- prevención de delegaciones DAC duplicadas vigentes
- ejecución rápida de demo de casos predefinidos
- limpieza de auditoría en caliente

---

## Modo consola (CLI)

`ejecutar_simulacion()` imprime:

1. matriz RBAC
2. 10 casos de uso con resultado en tiempo real
3. log completo de auditoría con totales
4. tabla resumen de clasificación MAC

---

## Registro de auditoría

Cada evaluación genera un `RegistroAcceso` con:

- `timestamp`
- `usuario_id`, `usuario_nombre`, `usuario_rol`
- `recurso_id`, `recurso_nombre`
- `accion`
- `resultado`
- `motivo`
- `modelo_aplicado`

La trazabilidad permite explicar por qué una solicitud se permitió o se denegó.

---

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas (solo biblioteca estándar)

Módulos usados en el proyecto:

- `argparse`, `uuid`, `datetime`
- `dataclasses`, `enum`, `typing`
- `tkinter` (`ttk`, `messagebox`) para GUI

---

## Instalación y ejecución

```bash
# Clonar repositorio
git clone https://github.com/KarenSuarez4/TuneBox.git
cd TuneBox

# Modo GUI (por defecto)
python main.py
# o
python main.py --modo gui

# Modo CLI
python main.py --modo cli
```

---

## Estructura del código

### `main.py`

- configura argumentos de ejecución (`--modo gui|cli`)
- enruta a `lanzar_gui()` o `ejecutar_simulacion()`

### `models.py`

- define enums de negocio (`ClasificacionMAC`, `Rol`, `Accion`)
- define dataclasses (`Recurso`, `Usuario`, `PermisoDelegado`, `RegistroAcceso`)

### `access_control.py`

- declara `RBAC_MATRIZ`
- implementa `MotorAcceso`:
  - validaciones RBAC/MAC/DAC
  - validaciones de contexto (propietario, representación, API externa)
  - auditoría y utilidades de impresión

### `scenario.py`

- `construir_escenario()`: crea usuarios, recursos y motor
- `ejecutar_simulacion()`: reproduce los casos de uso en consola

### `ui.py`

- `TuneBoxGUI`: laboratorio educativo interactivo
- `lanzar_gui()`: inicia la aplicación Tkinter



Versión: 2.0  
Año: 2026  
Equipo: Seguridad TuneBox
