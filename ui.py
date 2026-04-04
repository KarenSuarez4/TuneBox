from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from access_control import RBAC_MATRIZ
from models import Accion
from scenario import construir_escenario


class TuneBoxGUI:
    """Interfaz grafica educativa orientada a exploracion guiada."""

    COLORS = {
        "bg": "#f4f7f5",
        "panel": "#ffffff",
        "panel_soft": "#e8efec",
        "primary": "#1f6f5f",
        "primary_soft": "#dcefe8",
        "text": "#13302a",
        "muted": "#4f6b63",
        "ok_bg": "#ddf4e8",
        "ok_fg": "#146c43",
        "no_bg": "#fde4e4",
        "no_fg": "#9b1c1c",
    }

    def __init__(self, raiz: tk.Tk):
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

    def _construir_estilos(self):
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

    def _construir_layout(self):
        root = ttk.Frame(self.raiz, style="Root.TFrame", padding=14)
        root.pack(fill="both", expand=True)

        top = ttk.Frame(root, style="Root.TFrame")
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="TuneBox Learning Lab", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            top,
            text="Aprende control de acceso con simulaciones interactivas y retroalimentacion inmediata.",
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
        notebook.add(self.tab_teoria, text="Guia")
        notebook.add(self.tab_matriz, text="Matriz RBAC")
        notebook.add(self.tab_auditoria, text="Auditoria")

        self._tab_laboratorio()
        self._tab_teoria()
        self._tab_matriz()
        self._tab_auditoria()

    def _card(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame", padding=12)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    def _tab_laboratorio(self):
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
        ttk.Label(card_contexto, text="Contexto didactico", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
        self.lbl_contexto_usuario = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_usuario.pack(anchor="w")
        self.lbl_contexto_recurso = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_recurso.pack(anchor="w", pady=(2, 0))
        self.lbl_contexto_regla = ttk.Label(card_contexto, text="", style="Body.TLabel")
        self.lbl_contexto_regla.pack(anchor="w", pady=(2, 0))

        card_resultado = ttk.Frame(self.tab_lab, style="Card.TFrame", padding=12)
        card_resultado.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Label(card_resultado, text="Explicacion del resultado", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
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

        card_dac = self._card(self.tab_lab)
        ttk.Label(card_dac, text="Delegacion DAC", style="Section.TLabel").grid(
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

        ttk.Label(card_dac, text="Accion", style="Body.TLabel").grid(row=1, column=3, sticky="w")
        self.cmb_accion_dac = ttk.Combobox(card_dac, state="readonly", width=16)
        self.cmb_accion_dac.grid(row=2, column=3, sticky="we", padx=(0, 8))

        ttk.Label(card_dac, text="Dias", style="Body.TLabel").grid(row=1, column=4, sticky="w")
        self.spn_dias = tk.Spinbox(card_dac, from_=1, to=365, width=8)
        self.spn_dias.grid(row=2, column=4, sticky="w")

        ttk.Button(card_dac, text="Delegar", style="Accent.TButton", command=self._delegar).grid(
            row=2, column=5, sticky="e", padx=(10, 0)
        )

        for i in range(5):
            card_dac.columnconfigure(i, weight=1)

    def _tab_teoria(self):
        card = ttk.Frame(self.tab_teoria, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Guia rapida", style="Section.TLabel").pack(anchor="w", pady=(0, 6))
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
- Obliga a cumplir niveles de clasificacion y reglas de embargo.

Secuencia educativa recomendada
1. Ejecuta una solicitud permitida y una denegada.
2. Analiza el motivo exacto y el modelo que decidio.
3. Crea delegacion DAC y repite la solicitud.
4. Contrasta el cambio en la auditoria.
""".strip(),
        )
        texto.configure(state="disabled")

    def _tab_matriz(self):
        card = ttk.Frame(self.tab_matriz, style="Card.TFrame", padding=12)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Matriz RBAC", style="Section.TLabel").pack(anchor="w", pady=(0, 6))

        columnas = ("rol", "cancion", "ganancia", "metrica", "metadato", "contrato")
        self.tbl_matriz = ttk.Treeview(card, columns=columnas, show="headings", height=16)

        headers = {
            "rol": "Rol",
            "cancion": "Cancion",
            "ganancia": "Ganancia",
            "metrica": "Metrica",
            "metadato": "Metadato",
            "contrato": "Contrato",
        }
        widths = {"rol": 260, "cancion": 100, "ganancia": 100, "metrica": 100, "metadato": 100, "contrato": 100}

        for col in columnas:
            self.tbl_matriz.heading(col, text=headers[col])
            self.tbl_matriz.column(col, width=widths[col], anchor="center")

        self.tbl_matriz.pack(fill="both", expand=True)

        tipos = ["cancion", "ganancia", "metrica", "metadato", "contrato"]
        for rol, permisos in RBAC_MATRIZ.items():
            fila = [rol.value]
            for tipo in tipos:
                acciones = permisos.get(tipo, set())
                siglas = "".join(sorted(a.value[0].upper() for a in acciones)) or "--"
                fila.append(siglas)
            self.tbl_matriz.insert("", "end", values=fila)

        ttk.Label(card, text="Leyenda: L=leer, E=escribir, C=compartir, A=auditar, D=eliminar", style="Body.TLabel").pack(
            anchor="w", pady=(8, 0)
        )

    def _tab_auditoria(self):
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

    def _poblar_selectores(self):
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

    def _usuario_actual(self):
        return self.usuarios_ordenados[self.cmb_usuario.current()]

    def _recurso_actual(self):
        return self.recursos_ordenados[self.cmb_recurso.current()]

    def _accion_actual(self):
        return self.acciones_ordenadas[self.cmb_accion.current()]

    def _set_text(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", text)
        widget.configure(state="disabled")

    def _actualizar_contexto(self):
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
            text=f"Recurso: {recurso.nombre} | Tipo: {recurso.tipo} | Clasificacion: {recurso.clasificacion.name} | {embargo}"
        )
        self.lbl_contexto_regla.configure(
            text="Regla base: RBAC valida rol, MAC valida nivel y DAC permite excepciones temporales."
        )

    def _actualizar_badge(self, permitido):
        if permitido:
            self.badge_estado.configure(text="Ultimo resultado: PERMITIDO", bg=self.COLORS["ok_bg"], fg=self.COLORS["ok_fg"])
        else:
            self.badge_estado.configure(text="Ultimo resultado: DENEGADO", bg=self.COLORS["no_bg"], fg=self.COLORS["no_fg"])

    def _evaluar(self):
        usuario = self._usuario_actual()
        recurso = self._recurso_actual()
        accion = self._accion_actual()

        permitido, registro = self.motor.evaluar_acceso(usuario, recurso, accion)
        self._actualizar_badge(permitido)

        contenido = "\n".join(
            [
                "Resultado de evaluacion",
                "=" * 58,
                f"Usuario   : {usuario.nombre} ({usuario.rol.value})",
                f"Recurso   : {recurso.nombre}",
                f"Accion    : {accion.value}",
                f"Decision  : {'PERMITIDO' if permitido else 'DENEGADO'}",
                f"Modelo    : {registro.modelo_aplicado}",
                "-" * 58,
                "Motivo detallado:",
                registro.motivo,
                "",
                "Interpretacion:",
                "1) RBAC decide permisos por rol.",
                "2) Se evalua contexto de propietario/representacion.",
                "3) MAC verifica nivel y embargo.",
                "4) DAC puede habilitar excepciones temporales.",
            ]
        )

        self._set_text(self.txt_resultado, contenido)
        self._actualizar_auditoria()
        self._actualizar_dac_vigente()

    def _delegar(self):
        propietario = self.usuarios_ordenados[self.cmb_propietario.current()]
        beneficiario = self.usuarios_ordenados[self.cmb_beneficiario.current()]
        recurso = self.recursos_ordenados[self.cmb_recurso_dac.current()]
        accion = self.acciones_ordenadas[self.cmb_accion_dac.current()]

        try:
            dias = int(self.spn_dias.get())
        except ValueError:
            messagebox.showerror("DAC", "El numero de dias no es valido.")
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
                f"Accion: {accion.value} | Dias: {dias}"
            ),
        )
        self._actualizar_dac_vigente()

    def _actualizar_auditoria(self):
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

    def _actualizar_dac_vigente(self):
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

    def _limpiar_auditoria(self):
        self.motor.log.clear()
        self._actualizar_auditoria()
        self._set_text(self.txt_resultado, "Auditoria reiniciada. Ejecuta nuevas pruebas para comparar resultados.")
        self.badge_estado.configure(text="Sin evaluaciones aun", bg=self.COLORS["panel_soft"], fg=self.COLORS["text"])

    def _demo(self):
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
            "Demo ejecutada: revisa la pestana de Auditoria para ver la mezcla de permitidos y denegados.",
        )


def lanzar_gui():
    raiz = tk.Tk()
    TuneBoxGUI(raiz)
    raiz.mainloop()
