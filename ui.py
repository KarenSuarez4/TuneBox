from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Iterable

from access_control import RBAC_MATRIZ
from models import Accion, Recurso, Usuario
from scenario import construir_escenario


class TuneBoxGUI:
    """Interfaz gráfica educativa orientada a exploración guiada."""

    COLORS = {
        "bg": "#f4f7f5",
        "panel": "#ffffff",
        "panel_soft": "#e8efec",
        "panel_accent": "#eff6f3",
        "primary": "#1f6f5f",
        "primary_soft": "#dcefe8",
        "text": "#13302a",
        "muted": "#4f6b63",
        "ok_bg": "#ddf4e8",
        "ok_fg": "#146c43",
        "no_bg": "#fde4e4",
        "no_fg": "#9b1c1c",
    }

    def __init__(self, raiz: tk.Tk) -> None:
        """Inicializa la ventana principal, datos del escenario y widgets base."""
        self.raiz = raiz
        self.raiz.title("TuneBox Lab - RBAC + DAC + MAC")
        self.raiz.geometry("1240x780")
        self.raiz.minsize(1020, 680)
        self.raiz.configure(bg=self.COLORS["bg"])

        self.usuarios, self.recursos, self.motor = construir_escenario()
        self.usuarios_ordenados = list(self.usuarios.values())
        self.recursos_ordenados = list(self.recursos.values())
        self.acciones_ordenadas = list(Accion)

        self._construir_estilos()
        self._construir_layout()
        self._poblar_selectores()
        self._actualizar_contexto()
        self._actualizar_auditoria()
        self._actualizar_dac_vigente()

    def _construir_estilos(self) -> None:
        """Define estilos ttk compartidos para mantener consistencia visual en toda la GUI."""
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass

        estilo.configure("Root.TFrame", background=self.COLORS["bg"])
        estilo.configure("Card.TFrame", background=self.COLORS["panel"], relief="flat")
        estilo.configure(
            "Heading.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 20, "bold"),
        )
        estilo.configure(
            "Caption.TLabel",
            background=self.COLORS["bg"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 10),
        )
        estilo.configure(
            "Section.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 11, "bold"),
        )
        estilo.configure(
            "Body.TLabel",
            background=self.COLORS["panel"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10),
        )
        estilo.configure(
            "TNotebook",
            background=self.COLORS["bg"],
            borderwidth=0,
        )
        estilo.configure(
            "TNotebook.Tab",
            background=self.COLORS["panel_soft"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
        )
        estilo.map("TNotebook.Tab", background=[("selected", self.COLORS["primary_soft"])])

        estilo.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            background=self.COLORS["primary"],
            foreground="#ffffff",
            borderwidth=0,
            padding=(12, 8),
        )
        estilo.map(
            "Accent.TButton",
            background=[("active", "#185a4d"), ("pressed", "#154e43")],
            foreground=[("disabled", "#dbe6e3")],
        )

        estilo.configure("Soft.TButton", font=("Segoe UI", 10), padding=(10, 7), borderwidth=0)

        estilo.configure(
            "Matrix.Treeview",
            font=("Segoe UI", 10),
            rowheight=29,
            background="#ffffff",
            fieldbackground="#ffffff",
            bordercolor=self.COLORS["panel_soft"],
            borderwidth=0,
        )
        estilo.configure(
            "Matrix.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background=self.COLORS["primary_soft"],
            foreground=self.COLORS["text"],
            relief="flat",
            padding=(8, 6),
        )
        estilo.map(
            "Matrix.Treeview",
            background=[("selected", "#cde7de")],
            foreground=[("selected", self.COLORS["text"])],
        )

    def _construir_layout(self) -> None:
        """Construye la estructura general: encabezado y pestañas principales."""
        root = ttk.Frame(self.raiz, style="Root.TFrame", padding=14)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root, style="Root.TFrame")
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="TuneBox Learning Lab", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            top,
            text="Aprende control de acceso con simulaciones interactivas y retroalimentación inmediata.",
            style="Caption.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        self.badge_estado = tk.Label(
            top,
            text="Sin evaluaciones aun",
            bg=self.COLORS["panel_soft"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=5,
        )
        self.badge_estado.pack(anchor="e", pady=(6, 0))

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self.tab_lab = ttk.Frame(notebook, padding=10)
        self.tab_teoria = ttk.Frame(notebook, padding=10)
        self.tab_matriz = ttk.Frame(notebook, padding=10)
        self.tab_auditoria = ttk.Frame(notebook, padding=10)

        notebook.add(self.tab_lab, text="Laboratorio")
        notebook.add(self.tab_teoria, text="Guía")
        notebook.add(self.tab_matriz, text="Matriz RBAC")
        notebook.add(self.tab_auditoria, text="Auditoría")

        self._tab_laboratorio()
        self._tab_teoria()
        self._tab_matriz()
        self._tab_auditoria()

    def _card(self, parent: ttk.Frame) -> ttk.Frame:
        """Crea una tarjeta visual reutilizable para agrupar controles relacionados."""
        frame = ttk.Frame(parent, style="Card.TFrame", padding=12)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def _tab_laboratorio(self) -> None:
        """Renderiza la pestaña interactiva para evaluar solicitudes y delegar DAC."""
        card_selector = self._card(self.tab_lab)
        ttk.Label(card_selector, text="Simular solicitud", style="Section.TLabel").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )

        ttk.Label(card_selector, text="Usuario", style="Body.TLabel").grid(row=1, column=0, sticky="w")
        self.cmb_usuario = ttk.Combobox(card_selector, state="readonly", width=40)
        self.cmb_usuario.grid(row=2, column=0, sticky="we", padx=(0, 10))
        self.cmb_usuario.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_contexto())

        ttk.Label(card_selector, text="Recurso", style="Body.TLabel").grid(row=1, column=1, sticky="w")
        self.cmb_recurso = ttk.Combobox(card_selector, state="readonly", width=44)
        self.cmb_recurso.grid(row=2, column=1, sticky="we", padx=(0, 10))
        self.cmb_recurso.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_contexto())

        ttk.Label(card_selector, text="Accion", style="Body.TLabel").grid(row=1, column=2, sticky="w")
        self.cmb_accion = ttk.Combobox(card_selector, state="readonly", width=18)
        self.cmb_accion.grid(row=2, column=2, sticky="we")

        acciones = ttk.Frame(card_selector, style="Card.TFrame")
        acciones.grid(row=2, column=3, sticky="e", padx=(12, 0))
        ttk.Button(acciones, text="Evaluar", style="Accent.TButton", command=self._evaluar).pack(side="left")
        ttk.Button(acciones, text="Demo", style="Soft.TButton", command=self._demo).pack(side="left", padx=6)

        for i in range(3):
            card_selector.columnconfigure(i, weight=1)

        card_contexto = self._card(self.tab_lab)
        ttk.Label(card_contexto, text="Contexto didáctico", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.lbl_contexto_usuario = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_usuario.pack(anchor="w")
        self.lbl_contexto_recurso = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_recurso.pack(anchor="w", pady=(2, 0))
        self.lbl_contexto_regla = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_regla.pack(anchor="w", pady=(2, 0))

        card_dac = self._card(self.tab_lab)
        ttk.Label(card_dac, text="Delegación DAC (propietario -> beneficiario)", style="Section.TLabel").grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 8)
        )

        ttk.Label(card_dac, text="Propietario", style="Body.TLabel").grid(row=1, column=0, sticky="w")
        self.cmb_propietario = ttk.Combobox(card_dac, state="readonly", width=26)
        self.cmb_propietario.grid(row=2, column=0, sticky="we", padx=(0, 8))

        ttk.Label(card_dac, text="Beneficiario", style="Body.TLabel").grid(row=1, column=1, sticky="w")
        self.cmb_beneficiario = ttk.Combobox(card_dac, state="readonly", width=26)
        self.cmb_beneficiario.grid(row=2, column=1, sticky="we", padx=(0, 8))

        ttk.Label(card_dac, text="Recurso", style="Body.TLabel").grid(row=1, column=2, sticky="w")
        self.cmb_recurso_dac = ttk.Combobox(card_dac, state="readonly", width=34)
        self.cmb_recurso_dac.grid(row=2, column=2, sticky="we", padx=(0, 8))

        ttk.Label(card_dac, text="Acción", style="Body.TLabel").grid(row=1, column=3, sticky="w")
        self.cmb_accion_dac = ttk.Combobox(card_dac, state="readonly", width=16)
        self.cmb_accion_dac.grid(row=2, column=3, sticky="we", padx=(0, 8))

        ttk.Label(card_dac, text="Días", style="Body.TLabel").grid(row=1, column=4, sticky="w")
        self.spn_dias = tk.Spinbox(card_dac, from_=1, to=365, width=8)
        self.spn_dias.grid(row=2, column=4, sticky="w")

        ttk.Button(card_dac, text="Delegar permiso DAC", style="Accent.TButton", command=self._delegar).grid(
            row=2, column=5, sticky="e", padx=(10, 0)
        )

        for i in range(5):
            card_dac.columnconfigure(i, weight=1)

        card_resultado = ttk.Frame(self.tab_lab, style="Card.TFrame", padding=12)
        card_resultado.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Label(card_resultado, text="Explicación del resultado", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.txt_resultado = tk.Text(
            card_resultado,
            wrap="word",
            font=("Cascadia Code", 10),
            bg="#f7faf9",
            fg=self.COLORS["text"],
            relief="flat",
            padx=10,
            pady=8,
        )
        self.txt_resultado.pack(fill="both", expand=True)
        self._set_text(self.txt_resultado, "Selecciona datos y presiona Evaluar para iniciar.")

    def _tab_teoria(self) -> None:
        """Muestra una guia textual con conceptos clave y secuencia de aprendizaje."""
        card = ttk.Frame(self.tab_teoria, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Guía rápida", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        texto = tk.Text(
            card,
            wrap="word",
            font=("Segoe UI", 11),
            bg="#f7faf9",
            fg=self.COLORS["text"],
            relief="flat",
            padx=10,
            pady=8,
        )
        texto.pack(fill="both", expand=True)
        texto.insert(
            "end",
            """
RBAC
- Determina acciones permitidas por rol y tipo de recurso.

DAC
- Permite delegaciones temporales por parte del propietario.

MAC
- Obliga a cumplir niveles de clasificación y reglas de embargo.

Secuencia educativa recomendada
1. Ejecuta una solicitud permitida y una denegada.
2. Analiza el motivo exacto y el modelo que decidio.
3. Crea delegacion DAC y repite la solicitud.
4. Contrasta el cambio en la auditoría.
""".strip(),
        )
        texto.configure(state="disabled")

    def _tab_matriz(self) -> None:
        """Pinta la matriz RBAC con leyenda y nivel MAC sugerido por rol."""
        card = ttk.Frame(self.tab_matriz, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Matriz RBAC", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        meta = tk.Frame(card, bg=self.COLORS["panel_accent"], padx=10, pady=8)
        meta.pack(fill="x", pady=(0, 8))
        tk.Label(
            meta,
            text="Roles: 8",
            bg=self.COLORS["panel_accent"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")
        tk.Label(
            meta,
            text="Recursos: 5",
            bg=self.COLORS["panel_accent"],
            fg=self.COLORS["text"],
            font=("Segoe UI", 9, "bold"),
            padx=16,
        ).pack(side="left")
        tk.Label(
            meta,
            text="Tip: selecciona una fila para compararla con auditoría",
            bg=self.COLORS["panel_accent"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="right")

        leyenda = tk.Frame(card, bg=self.COLORS["panel"], pady=6)
        leyenda.pack(fill="x")
        tk.Label(
            leyenda,
            text="Leyenda: L=leer, E=escribir, C=compartir, A=auditar, --=sin acceso",
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 10),
        ).pack(anchor="w")
        tk.Label(
            leyenda,
            text="(*) Manager: solo artistas representados. (**) Marketing: solo después de levantarse el embargo.",
            bg=self.COLORS["panel"],
            fg=self.COLORS["muted"],
            font=("Segoe UI", 10, "italic"),
        ).pack(anchor="w")

        columnas = ("rol", "canciones", "ganancias", "metricas", "metadatos", "contratos", "nivel_mac")
        tabla_wrap = ttk.Frame(card, style="Card.TFrame")
        tabla_wrap.pack(fill="both", expand=True)

        scroll_y = ttk.Scrollbar(tabla_wrap, orient="vertical")
        scroll_x = ttk.Scrollbar(tabla_wrap, orient="horizontal")

        self.tbl_matriz = ttk.Treeview(
            tabla_wrap,
            columns=columnas,
            show="headings",
            height=16,
            style="Matrix.Treeview",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        scroll_y.configure(command=self.tbl_matriz.yview)
        scroll_x.configure(command=self.tbl_matriz.xview)

        headers = {
            "rol": "Rol",
            "canciones": "Canciones",
            "ganancias": "Ganancias",
            "metricas": "Métricas",
            "metadatos": "Metadatos",
            "contratos": "Contratos",
            "nivel_mac": "Nivel MAC",
        }
        widths = {
            "rol": 250,
            "canciones": 110,
            "ganancias": 110,
            "metricas": 110,
            "metadatos": 110,
            "contratos": 110,
            "nivel_mac": 130,
        }

        for col in columnas:
            self.tbl_matriz.heading(col, text=headers[col])
            self.tbl_matriz.column(col, width=widths[col], anchor="center")

        self.tbl_matriz.column("rol", anchor="w", width=260)

        self.tbl_matriz.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        nivel_por_rol = {
            "Artista/Productor": "SECRETO",
            "Manager": "SECRETO",
            "Equipo de Marketing": "CONFIDENCIAL",
            "Legal/Compliance": "SECRETO",
            "Equipo de Analitica": "PÚBLICO",
            "Administrativo": "CONFIDENCIAL",
            "Plataforma Externa (API)": "PÚBLICO",
            "Productor Editorial": "CONFIDENCIAL",
        }

        def formatear_acciones(acciones: Iterable[Accion]) -> str:
            """Convierte acciones permitidas en siglas legibles para la tabla."""
            orden = ["leer", "escribir", "compartir", "auditar", "eliminar"]
            letras = {
                "leer": "L",
                "escribir": "E",
                "compartir": "C",
                "auditar": "A",
                "eliminar": "D",
            }
            presentes = [letras[a] for a in orden if any(x.value == a for x in acciones)]
            return ", ".join(presentes) if presentes else "--"

        tipos = ["cancion", "ganancia", "metrica", "metadato", "contrato"]
        for idx, (rol, permisos) in enumerate(RBAC_MATRIZ.items()):
            fila = [rol.value]
            for tipo in tipos:
                texto = formatear_acciones(permisos.get(tipo, set()))
                if rol.value == "Manager" and tipo == "ganancia" and texto != "--":
                    texto = f"{texto}*"
                if rol.value == "Equipo de Marketing" and tipo == "metrica" and texto != "--":
                    texto = f"{texto}**"
                fila.append(texto)
            fila.append(nivel_por_rol.get(rol.value, "-"))
            tag = "even" if idx % 2 == 0 else "odd"
            self.tbl_matriz.insert("", "end", values=fila, tags=(tag,))

        self.tbl_matriz.tag_configure("even", background="#ffffff")
        self.tbl_matriz.tag_configure("odd", background="#f8fbfa")

    def _tab_auditoria(self) -> None:
        """Construye la vista de eventos de auditoria y permisos DAC vigentes."""
        top = ttk.Frame(self.tab_auditoria, style="Root.TFrame")
        top.pack(fill="x", pady=(0, 10))

        ttk.Button(top, text="Actualizar", style="Soft.TButton", command=self._actualizar_auditoria).pack(side="left")
        ttk.Button(top, text="Limpiar", style="Soft.TButton", command=self._limpiar_auditoria).pack(side="left", padx=6)

        self.lbl_resumen = ttk.Label(top, text="", style="Caption.TLabel")
        self.lbl_resumen.pack(side="right")

        card = ttk.Frame(self.tab_auditoria, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)

        columnas = ("hora", "usuario", "rol", "accion", "recurso", "resultado", "modelo")
        self.tbl_log = ttk.Treeview(card, columns=columnas, show="headings", height=15)

        conf = {
            "hora": 90,
            "usuario": 170,
            "rol": 170,
            "accion": 95,
            "recurso": 310,
            "resultado": 100,
            "modelo": 130,
        }
        for col in columnas:
            self.tbl_log.heading(col, text=col.upper())
            self.tbl_log.column(col, width=conf[col], anchor="center")

        self.tbl_log.tag_configure("ok", background=self.COLORS["ok_bg"], foreground=self.COLORS["ok_fg"])
        self.tbl_log.tag_configure("no", background=self.COLORS["no_bg"], foreground=self.COLORS["no_fg"])

        self.tbl_log.pack(fill="both", expand=True)

        ttk.Label(card, text="Permisos DAC vigentes", style="Section.TLabel").pack(anchor="w", pady=(10, 6))
        self.txt_dac = tk.Text(
            card,
            height=6,
            wrap="word",
            font=("Cascadia Code", 10),
            bg="#f7faf9",
            fg=self.COLORS["text"],
            relief="flat",
            padx=10,
            pady=8,
        )
        self.txt_dac.pack(fill="x")

    def _poblar_selectores(self) -> None:
        """Carga los combobox iniciales con usuarios, recursos y acciones disponibles."""
        usuarios_txt = [f"{u.nombre} [{u.rol.name}]" for u in self.usuarios_ordenados]
        recursos_txt = [f"{r.nombre} ({r.tipo}/{r.clasificacion.name})" for r in self.recursos_ordenados]
        acciones_txt = [a.value for a in self.acciones_ordenadas]

        self.cmb_usuario["values"] = usuarios_txt
        self.cmb_recurso["values"] = recursos_txt
        self.cmb_accion["values"] = acciones_txt

        self.cmb_propietario["values"] = usuarios_txt
        self.cmb_beneficiario["values"] = usuarios_txt
        self.cmb_recurso_dac["values"] = recursos_txt
        self.cmb_accion_dac["values"] = acciones_txt

        self.cmb_usuario.current(0)
        self.cmb_recurso.current(0)
        self.cmb_accion.current(0)

        self.cmb_propietario.current(0)
        self.cmb_beneficiario.current(1)
        self.cmb_recurso_dac.current(0)
        self.cmb_accion_dac.current(0)

    def _usuario_actual(self) -> Usuario:
        """Retorna el usuario actualmente seleccionado en el laboratorio."""
        return self.usuarios_ordenados[self.cmb_usuario.current()]

    def _recurso_actual(self) -> Recurso:
        """Retorna el recurso actualmente seleccionado en el laboratorio."""
        return self.recursos_ordenados[self.cmb_recurso.current()]

    def _accion_actual(self) -> Accion:
        """Retorna la accion seleccionada en el laboratorio."""
        return self.acciones_ordenadas[self.cmb_accion.current()]

    def _set_text(self, widget: tk.Text, text: str) -> None:
        """Actualiza un widget de texto en modo seguro (habilitar, escribir, deshabilitar)."""
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def _actualizar_contexto(self) -> None:
        """Refresca etiquetas de contexto con datos del usuario y recurso activo."""
        usuario = self._usuario_actual()
        recurso = self._recurso_actual()
        embargo = (
            f"Embargo hasta {recurso.fecha_embargo.strftime('%Y-%m-%d')}"
            if recurso.fecha_embargo
            else "Sin embargo"
        )

        self.lbl_contexto_usuario.configure(
            text=f"Usuario: {usuario.nombre} | Rol: {usuario.rol.value} | Nivel MAC: {usuario.nivel_autorizacion.name}"
        )
        self.lbl_contexto_recurso.configure(
            text=f"Recurso: {recurso.nombre} | Tipo: {recurso.tipo} | Clasificación: {recurso.clasificacion.name} | {embargo}"
        )
        self.lbl_contexto_regla.configure(
            text="Regla base: RBAC valida rol, MAC valida nivel y DAC permite excepciones temporales."
        )

    def _actualizar_badge(self, permitido: bool) -> None:
        """Actualiza el indicador visual segun el resultado de la ultima evaluacion."""
        if permitido:
            self.badge_estado.configure(text="Último resultado: PERMITIDO", bg=self.COLORS["ok_bg"], fg=self.COLORS["ok_fg"])
        else:
            self.badge_estado.configure(text="Último resultado: DENEGADO", bg=self.COLORS["no_bg"], fg=self.COLORS["no_fg"])

    def _evaluar(self) -> None:
        """Ejecuta la evaluacion de acceso y explica la decision para el estudiante."""
        usuario = self._usuario_actual()
        recurso = self._recurso_actual()
        accion = self._accion_actual()

        permitido, registro = self.motor.evaluar_acceso(usuario, recurso, accion)
        self._actualizar_badge(permitido)

        contenido = "\n".join(
            [
                "Resultado de evaluación",
                "=" * 58,
                f"Usuario   : {usuario.nombre} ({usuario.rol.value})",
                f"Recurso   : {recurso.nombre}",
                f"Acción    : {accion.value}",
                f"Decision  : {'PERMITIDO' if permitido else 'DENEGADO'}",
                f"Modelo    : {registro.modelo_aplicado}",
                "-" * 58,
                "Motivo detallado:",
                registro.motivo,
                "",
                "Interpretación:",
                "1) RBAC decide permisos por rol.",
                "2) Se evalua contexto de propietario/representacion.",
                "3) MAC verifica nivel y embargo.",
                "4) DAC puede habilitar excepciones temporales.",
            ]
        )

        self._set_text(self.txt_resultado, contenido)
        self._actualizar_auditoria()
        self._actualizar_dac_vigente()

    def _delegar(self) -> None:
        """Crea una delegacion DAC validando entradas y evitando duplicados vigentes."""
        propietario = self.usuarios_ordenados[self.cmb_propietario.current()]
        beneficiario = self.usuarios_ordenados[self.cmb_beneficiario.current()]
        recurso = self.recursos_ordenados[self.cmb_recurso_dac.current()]
        accion = self.acciones_ordenadas[self.cmb_accion_dac.current()]

        try:
            dias = int(self.spn_dias.get())
        except ValueError:
            messagebox.showerror("DAC", "El número de días no es válido.")
            return

        # Evita duplicados activos del mismo permiso para no confundir el laboratorio.
        for permiso in self.motor.permisos_dac:
            if (
                permiso.otorgado_por == propietario.id
                and permiso.otorgado_a == beneficiario.id
                and permiso.recurso_id == recurso.id
                and accion in permiso.acciones
                and permiso.esta_vigente()
            ):
                messagebox.showinfo(
                    "DAC",
                    (
                        "Ya existe un permiso DAC vigente con esos datos.\n"
                        f"ID: {permiso.id} | Expira: {permiso.expira.strftime('%Y-%m-%d')}"
                    ),
                )
                self._actualizar_dac_vigente()
                return

        try:
            permiso = self.motor.delegar_permiso_silencioso(
                propietario=propietario,
                recurso=recurso,
                beneficiario=beneficiario,
                acciones=[accion],
                dias=dias,
            )
        except PermissionError as exc:
            messagebox.showwarning("DAC", str(exc))
            return

        messagebox.showinfo(
            "DAC",
            (
                f"Permiso {permiso.id} creado:\n"
                f"{propietario.nombre} -> {beneficiario.nombre}\n"
                f"Recurso: {recurso.nombre}\n"
                f"Acción: {accion.value} | Días: {dias}"
            ),
        )
        self._actualizar_dac_vigente()

    def _actualizar_auditoria(self) -> None:
        """Sincroniza la tabla de auditoria con el log actual del motor."""
        for row in self.tbl_log.get_children():
            self.tbl_log.delete(row)

        for entrada in self.motor.log:
            tag = "ok" if entrada.resultado == "PERMITIDO" else "no"
            self.tbl_log.insert(
                "",
                "end",
                values=(
                    entrada.timestamp.strftime("%H:%M:%S"),
                    entrada.usuario_nombre,
                    entrada.usuario_rol,
                    entrada.accion.upper(),
                    entrada.recurso_nombre,
                    entrada.resultado,
                    entrada.modelo_aplicado,
                ),
                tags=(tag,),
            )

        permitidos = sum(1 for e in self.motor.log if e.resultado == "PERMITIDO")
        denegados = sum(1 for e in self.motor.log if e.resultado == "DENEGADO")
        self.lbl_resumen.configure(
            text=f"Intentos: {len(self.motor.log)} | Permitidos: {permitidos} | Denegados: {denegados}"
        )

    def _actualizar_dac_vigente(self) -> None:
        """Muestra en texto los permisos DAC activos y su fecha de expiracion."""
        lineas = ["Permisos vigentes:"]
        vigentes = [perm for perm in self.motor.permisos_dac if perm.esta_vigente()]

        if not vigentes:
            lineas.append("- No hay delegaciones DAC activas.")
        else:
            nombres_usuario = {u.id: u.nombre for u in self.usuarios_ordenados}
            nombres_recurso = {r.id: r.nombre for r in self.recursos_ordenados}
            for permiso in vigentes:
                acciones = ", ".join(a.value for a in permiso.acciones)
                lineas.append(
                    f"- {permiso.id}: {nombres_usuario.get(permiso.otorgado_por, permiso.otorgado_por)} -> "
                    f"{nombres_usuario.get(permiso.otorgado_a, permiso.otorgado_a)} | "
                    f"{nombres_recurso.get(permiso.recurso_id, permiso.recurso_id)} | "
                    f"{acciones} | expira {permiso.expira.strftime('%Y-%m-%d')}"
                )

        self._set_text(self.txt_dac, "\n".join(lineas))

    def _limpiar_auditoria(self) -> None:
        """Limpia el log de auditoria para iniciar nuevas pruebas comparativas."""
        self.motor.log.clear()
        self._actualizar_auditoria()
        self._set_text(self.txt_resultado, "Auditoría reiniciada. Ejecuta nuevas pruebas para comparar resultados.")
        self.badge_estado.configure(text="Sin evaluaciones aun", bg=self.COLORS["panel_soft"], fg=self.COLORS["text"])

    def _demo(self) -> None:
        """Ejecuta un conjunto corto de casos predefinidos para poblar la auditoria."""
        casos = [
            ("sofia", "ganancias_sofia", Accion.LEER),
            ("manager_a", "ganancias_carlos", Accion.LEER),
            ("marketing", "lanzamiento_futuro_sofia", Accion.LEER),
            ("legal", "contrato_sofia", Accion.AUDITAR),
            ("spotify_api", "cancion_carlos", Accion.LEER),
        ]

        for uid, rid, accion in casos:
            self.motor.evaluar_acceso(self.usuarios[uid], self.recursos[rid], accion)

        self._actualizar_auditoria()
        self._actualizar_dac_vigente()
        self._set_text(
            self.txt_resultado,
            "Demo ejecutada: revisa la pestaña de Auditoría para ver la mezcla de permitidos y denegados.",
        )


def lanzar_gui() -> None:
    """Inicia la aplicacion Tkinter de TuneBox."""
    raiz = tk.Tk()
    TuneBoxGUI(raiz)
    raiz.mainloop()
