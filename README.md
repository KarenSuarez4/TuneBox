# TuneBox 

Sistema de Control de Acceso Integrado para una plataforma de distribución musical, que simula políticas de seguridad **RBAC + DAC + MAC** sobre activos de información de artistas.

---

## Tabla de Contenidos

1. [Descripción general](#descripción-general)
2. [Modelos de control de acceso](#modelos-de-control-de-acceso)
   - [RBAC – Role-Based Access Control](#rbac--role-based-access-control)
   - [DAC – Discretionary Access Control](#dac--discretionary-access-control)
   - [MAC – Mandatory Access Control](#mac--mandatory-access-control)
3. [Arquitectura del proyecto](#arquitectura-del-proyecto)
4. [Entidades principales](#entidades-principales)
   - [Roles](#roles)
   - [Tipos de recursos](#tipos-de-recursos)
   - [Acciones](#acciones)
   - [Clasificaciones MAC](#clasificaciones-mac)
5. [Flujo de evaluación de acceso](#flujo-de-evaluación-de-acceso)
6. [Matriz RBAC](#matriz-rbac)
7. [Escenario de simulación](#escenario-de-simulación)
8. [Casos de uso simulados](#casos-de-uso-simulados)
9. [Registro de auditoría](#registro-de-auditoría)
10. [Requisitos](#requisitos)
11. [Instalación y ejecución](#instalación-y-ejecución)
12. [Estructura del código](#estructura-del-código)

---

## Descripción general

**TuneBox** es un sistema académico/demostrativo que modela el control de acceso a información sensible dentro de una plataforma de distribución musical. El sistema protege activos como canciones, ganancias, métricas, metadatos y contratos aplicando simultáneamente tres modelos de seguridad clásicos:

| Modelo | Descripción breve |
|--------|-------------------|
| RBAC   | Los permisos se asignan por rol, no por usuario individual. |
| DAC    | El propietario de un recurso puede delegar acceso temporal a terceros. |
| MAC    | El acceso se rige por niveles de clasificación jerárquicos y reglas de embargo. |

Todos los intentos de acceso —permitidos y denegados— quedan registrados en un log de auditoría inmutable para trazabilidad completa.

---

## Modelos de control de acceso

### RBAC – Role-Based Access Control

Los permisos están definidos en una **matriz Rol × Tipo de recurso × Acciones**. Ningún usuario accede directamente a un recurso sin que su rol lo autorice primero.

Cada rol tiene un conjunto de acciones permitidas (leer, escribir, eliminar, compartir, auditar) diferenciado por tipo de recurso. Por ejemplo, el equipo de Marketing puede leer métricas públicas pero no tiene acceso a datos financieros.

### DAC – Discretionary Access Control

El **propietario** de un recurso puede delegar acceso temporal a otro usuario mediante `delegar_permiso()`. Este permiso incluye:

- Recurso específico
- Usuario beneficiario
- Conjunto de acciones autorizadas
- Fecha de expiración (configurable, por defecto 30 días)

El DAC actúa como **mecanismo de excepción**: puede conceder acceso incluso cuando RBAC lo denegaría.

### MAC – Mandatory Access Control

Cada recurso tiene un nivel de clasificación y cada usuario tiene un nivel de autorización máximo. La regla es:

> **nivel_autorización(usuario) ≥ clasificación(recurso)**

Además, existe una **regla de embargo**: recursos `CONFIDENCIAL` o `SECRETO` con una fecha de lanzamiento futura solo son accesibles por el propietario o por `Legal/Compliance`, independientemente del nivel MAC.

---

## Arquitectura del proyecto

```
TuneBox/
├── main.py        # Código fuente completo del sistema
└── README.md      # Documentación del proyecto
```

Todo el sistema está implementado en un único archivo Python (`main.py`) organizado en seis secciones:

| Sección | Contenido |
|---------|-----------|
| 1 | Enumeraciones: `ClasificacionMAC`, `Rol`, `Accion` |
| 2 | Estructuras de datos: `Recurso`, `Usuario`, `PermisoDelegado`, `RegistroAcceso` |
| 3 | Matriz RBAC |
| 4 | Motor de control de acceso (`MotorAcceso`) |
| 5 | Escenario de simulación con 10 casos de uso |
| 6 | Punto de entrada (`__main__`) |

---

## Entidades principales

### Roles

| Rol | Descripción |
|-----|-------------|
| `ARTISTA` | Artista/Productor — accede a sus propios datos |
| `MANAGER` | Manager — accede a datos de los artistas que representa |
| `MARKETING` | Equipo de Marketing — accede a métricas públicas, sin datos financieros |
| `LEGAL_COMPLIANCE` | Legal/Compliance — auditoría irrestricta sobre todos los recursos |
| `ANALITICA` | Equipo de Analítica — solo métricas agregadas |
| `ADMINISTRATIVO` | Administrativo — ganancias/contratos agregados; acceso individual vía DAC |
| `PLATAFORMA_EXTERNA` | Plataforma externa (API) — accede solo a los artistas de su plataforma |
| `PRODUCTOR_EDITORIAL` | Productor Editorial — rol futuro con permisos básicos |

### Tipos de recursos

| Tipo | Ejemplos |
|------|---------|
| `cancion` | Tracks de audio de un artista |
| `ganancia` | Reportes de ingresos por período |
| `metrica` | Estadísticas de reproducciones, alcance |
| `metadato` | Información descriptiva de lanzamientos |
| `contrato` | Contratos de distribución |

### Acciones

| Acción | Descripción |
|--------|-------------|
| `LEER` | Consultar el contenido de un recurso |
| `ESCRIBIR` | Crear o modificar un recurso |
| `ELIMINAR` | Borrar un recurso |
| `COMPARTIR` | Distribuir o publicar un recurso |
| `AUDITAR` | Revisar con fines de cumplimiento normativo |

### Clasificaciones MAC

| Nivel | Valor | Datos representativos | Quién puede acceder |
|-------|-------|-----------------------|---------------------|
| `PUBLICO` | 1 | Métricas agregadas, info pública de artistas | Todos los roles autenticados, APIs externas, Analítica |
| `CONFIDENCIAL` | 2 | Lanzamientos futuros (embargo), campañas de marketing | Marketing (con restricción embargo), Admin, Manager, Artista propietario |
| `SECRETO` | 3 | Ganancias individuales, contratos, datos fiscales | Artista (propios), Manager (representados), Legal, Admin agregado, DAC |

---

## Flujo de evaluación de acceso

Cuando se invoca `motor.solicitar_acceso(usuario, recurso, accion)`, el motor evalúa en este orden:

```
solicitud
   │
   ▼
[1] RBAC ──── NO ──▶ [DAC fallback] ──── SÍ ──▶ PERMITIDO (DAC)
   │                                     NO ──▶ DENEGADO
   │ SÍ
   ▼
[2] Contexto / Propietario
   ├─ Artista sin ser propietario       ──▶ DENEGADO
   ├─ Manager sin representar artista   ──▶ DENEGADO
   ├─ Admin externo sin delegación DAC  ──▶ DENEGADO
   └─ API externa sin acceso a plataforma ─▶ DENEGADO
   │ OK
   ▼
[3] MAC (nivel autorización + embargo)
   │ NO ──▶ DENEGADO
   │ SÍ
   ▼
PERMITIDO (RBAC + MAC)
```

Cada paso genera un `RegistroAcceso` con timestamp, resultado, motivo y modelo aplicado.

---

## Matriz RBAC

Leyenda de siglas: **L**=leer, **E**=escribir, **C**=compartir, **A**=auditar, **D**=eliminar, **--**=sin acceso.

| Rol | cancion | ganancia | metrica | metadato | contrato |
|-----|---------|----------|---------|----------|----------|
| Artista/Productor | L E C | L | L | L E | L |
| Manager | L | L | L | L E | L |
| Equipo de Marketing | L | -- | L | L | -- |
| Legal/Compliance | L A | L A | L A | L A | L A |
| Equipo de Analítica | L | -- | L | L | -- |
| Administrativo | -- | L | -- | L | L |
| Plataforma Externa (API) | L | -- | L | L | -- |
| Productor Editorial | L E | L | L | L E | L |

> **Nota:** Las restricciones de propietario (DAC) y nivel (MAC) se aplican adicionalmente sobre esta matriz.

---

## Escenario de simulación

El escenario incluye los siguientes usuarios y recursos preconstruidos:

### Usuarios

| ID | Nombre | Rol | Nivel MAC |
|----|--------|-----|-----------|
| u001 | Sofia Ramos | Artista | SECRETO |
| u002 | Carlos Vega | Artista | SECRETO |
| u003 | Laura Méndez | Manager (representa a Sofía) | SECRETO |
| u004 | Pedro Torres | Marketing | CONFIDENCIAL |
| u005 | Ana Ríos | Legal/Compliance | SECRETO |
| u006 | Luis Parra | Analítica | PÚBLICO |
| u007 | María Gil | Administrativo | CONFIDENCIAL |
| u008 | Spotify API | Plataforma Externa (de Sofía) | PÚBLICO |
| u009 | Rodrigo Salas | Administrativo (contador externo) | SECRETO |
| u010 | Diana Cruz | Productor Editorial | CONFIDENCIAL |

### Recursos

| ID | Nombre | Tipo | Clasificación | Propietario |
|----|--------|------|---------------|-------------|
| r001 | Track 'Noche Eterna' – Sofía | cancion | PÚBLICO | u001 |
| r002 | Ganancias Q1-2026 – Sofía | ganancia | SECRETO | u001 |
| r003 | Album 'Eclipse' (PRELANZAMIENTO) – Sofía | metrica | CONFIDENCIAL | u001 (con embargo) |
| r004 | Ganancias Q1-2026 – Carlos | ganancia | SECRETO | u002 |
| r005 | Track 'Solar' – Carlos | cancion | PÚBLICO | u002 |
| r006 | Métricas Agregadas Plataforma | metrica | PÚBLICO | sistema |
| r007 | Contrato Distribución – Sofía | contrato | SECRETO | u001 |

---

## Casos de uso simulados

| # | Caso | Resultado esperado |
|---|------|--------------------|
| 1 | Artista accede a sus propios datos (ganancias y canción) | ✅ PERMITIDO |
| 2 | Artista intenta ver datos de otro artista (privacidad) | ❌ DENEGADO |
| 3 | Manager accede a datos de su artista representado | ✅ PERMITIDO |
| 4 | Manager intenta acceder a artista NO representado (conflicto de interés) | ❌ DENEGADO |
| 5 | Marketing lee métricas bajo embargo / métricas públicas / ganancias | ❌/✅/❌ |
| 6 | Legal/Compliance audita datos SECRETOS con y sin embargo | ✅ PERMITIDO |
| 7 | Analítica accede a métricas públicas y ganancias individuales | ✅/❌ |
| 8 | Spotify API accede a datos de Sofía y de Carlos | ✅/❌ |
| 9 | DAC: Sofía delega acceso al contador externo (30 días) | ✅ PERMITIDO (DAC) / ❌ sin DAC |
| 10 | Productor Editorial accede a canciones y ganancias (rol futuro) | ✅/❌ |

---

## Registro de auditoría

Cada intento de acceso genera un `RegistroAcceso` con los siguientes campos:

| Campo | Descripción |
|-------|-------------|
| `timestamp` | Fecha y hora exacta del intento |
| `usuario_id` / `usuario_nombre` | Identidad del solicitante |
| `usuario_rol` | Rol en el momento del acceso |
| `recurso_id` / `recurso_nombre` | Recurso solicitado |
| `accion` | Acción solicitada |
| `resultado` | `PERMITIDO` o `DENEGADO` |
| `motivo` | Razón detallada de la decisión |
| `modelo_aplicado` | Modelo que tomó la decisión (`RBAC`, `MAC`, `DAC`, `RBAC+MAC`, etc.) |

Al finalizar la simulación se imprime el log completo con totales de intentos permitidos y denegados.

---

## Requisitos

- Python **3.8** o superior
- Sin dependencias externas (solo módulos de la biblioteca estándar: `dataclasses`, `datetime`, `enum`, `uuid`, `typing`)

---

## Instalación y ejecución

```bash
# Clonar el repositorio
git clone https://github.com/KarenSuarez4/TuneBox.git
cd TuneBox

# Ejecutar la simulación
python main.py
```

La salida en consola mostrará:

1. La **Matriz RBAC** completa
2. El resultado de cada uno de los **10 casos de uso**
3. El **registro completo de auditoría** con totales
4. La **tabla de clasificación MAC** de datos

---

## Estructura del código

```
main.py
│
├── ClasificacionMAC (Enum)      – Niveles PUBLICO / CONFIDENCIAL / SECRETO
├── Rol (Enum)                   – Roles de la plataforma
├── Accion (Enum)                – Acciones posibles sobre recursos
│
├── Recurso (dataclass)          – Activo de información
├── Usuario (dataclass)          – Actor del sistema
├── PermisoDelegado (dataclass)  – Delegación DAC temporal
├── RegistroAcceso (dataclass)   – Entrada del log de auditoría
│
├── RBAC_MATRIZ (dict)           – Matriz de permisos Rol × Recurso × Acciones
│
├── MotorAcceso (class)
│   ├── solicitar_acceso()       – Punto de entrada: evalúa RBAC → contexto → MAC → DAC
│   ├── delegar_permiso()        – Crea un permiso DAC temporal
│   ├── imprimir_log()           – Muestra el registro de auditoría
│   └── imprimir_matriz_rbac()   – Muestra la matriz de permisos
│
├── construir_escenario()        – Instancia usuarios, recursos y motor
└── ejecutar_simulacion()        – Ejecuta los 10 casos de uso
```

---

> **Versión:** 1.0 · **Año:** 2026 · **Equipo:** Seguridad TuneBox
