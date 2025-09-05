import tkinter as tk
from tkinter import messagebox, ttk
import db
from recibo import generar_recibo
from datetime import datetime
from tkinter import simpledialog
import sqlite3

def bootstrap_admin_si_falta():
#Si no hay un administrador creado, pide crear uno al iniciar el programa
    try:
        db.crear_tabla_credenciales()
        if db.contar_usuarios_login() == 0:
            messagebox.showinfo("Configuración inicial", "No hay usuarios. Crea el usuario administrador.")
            while True:
                user = simpledialog.askstring("Nuevo admin", "Usuario:")
                if user is None or user.strip() == "":
                    messagebox.showwarning("Requerido", "Debes ingresar un usuario.")
                    continue
                pwd = simpledialog.askstring("Nuevo admin", "Contraseña:", show="*")
                if pwd is None or pwd == "":
                    messagebox.showwarning("Requerido", "Debes ingresar una contraseña.")
                    continue
                try:
                    db.crear_usuario(user.strip(), pwd)
                    messagebox.showinfo("Listo", f"Usuario administrador '{user.strip()}' creado.")
                    break
                except sqlite3.IntegrityError:
                    messagebox.showerror("Error", "Ese usuario ya existe. Intenta con otro.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo preparar el sistema de credenciales:\n{e}")


def parse_fecha(fecha_str: str):
   
    if not fecha_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d-%m-%y"):
        try:
            return datetime.strptime(fecha_str, fmt).date()
        except Exception:
            continue
    return None  

def formato_ddmmyyyy(fecha_str: str | None) -> str:
    
    d = parse_fecha(fecha_str)
    return d.strftime("%d/%m/%Y") if d else (fecha_str or "")



# Conectar base de datos
db.conectar()
bootstrap_admin_si_falta()

usuario_editando = None

def registrar_usuario():
    global usuario_editando
    nombre = entry_nombre.get()
    apellido = entry_apellido.get()
    telefono = entry_telefono.get()
    membresia = combo_membresia.get()

    if not (nombre and apellido and telefono and membresia):
        messagebox.showwarning("Campos incompletos", "Por favor completa todos los campos.")
        return

    if usuario_editando is None:
        # Registrar nuevo usuario
        id_usuario = db.agregar_usuario(nombre, apellido, telefono, membresia)
        usuario = db.obtener_usuario(id_usuario)
        if usuario:
            generar_recibo(usuario)
            messagebox.showinfo("Registro exitoso", f"Se agregó el usuario: {nombre}. Recibo generado.")
    else:
        # Actualizar usuario existente
        id_usuario = usuario_editando["id"]
        db.actualizar_usuario(id_usuario, nombre, apellido, telefono, membresia)
        usuario_actualizado = db.obtener_usuario(id_usuario)
        if usuario_actualizado:
            generar_recibo(usuario_actualizado)
        messagebox.showinfo("Actualización", f"Usuario {nombre} {apellido} actualizado. Recibo generado.")
        usuario_editando = None
        btn_registrar.config(text="Registrar")

    limpiar_campos()
    cargar_usuarios_en_lista()

def limpiar_campos():
    global usuario_editando
    entry_nombre.delete(0, tk.END)
    entry_apellido.delete(0, tk.END)
    entry_telefono.delete(0, tk.END)
    combo_membresia.set("")
    usuario_editando = None
    btn_registrar.config(text="Registrar")

    
    try:
        lista_usuarios.selection_remove(lista_usuarios.selection())
    except Exception:
        pass

def cargar_usuarios_en_lista():
    usuarios = db.obtener_usuarios()
    lista_usuarios.delete(*lista_usuarios.get_children())
    hoy = datetime.today().date()

    for u in usuarios:
        id_usuario = u["id"]
        nombre = u["nombre"]
        apellido = u["apellido"]
        telefono = u["telefono"]
        membresia = u["membresia"]
        fecha_registro = u["fecha_registro"]
        fecha_vencimiento = u["fecha_vencimiento"]

        vence_mostrar = formato_ddmmyyyy(fecha_vencimiento)

        tag_color = 'normal'
        fecha_ven = parse_fecha(fecha_vencimiento)
        if fecha_ven:
            dias_restantes = (fecha_ven - hoy).days
            if dias_restantes < 0:
                tag_color = 'vencido'
            elif dias_restantes <= 7:
                tag_color = 'por_vencer'

        lista_usuarios.insert(
            "", tk.END,
            values=(id_usuario, nombre, apellido, telefono, membresia, vence_mostrar),
            tags=(tag_color,)
        )

    lista_usuarios.tag_configure('vencido', foreground='red')
    lista_usuarios.tag_configure('normal', foreground='black')
    lista_usuarios.tag_configure('por_vencer', foreground='orange')


def on_usuario_doble_click(event):
    global usuario_editando
    sel = lista_usuarios.selection()
    if sel:
        valores = lista_usuarios.item(sel[0], "values")  # <- usa sel[0]
        id_usuario = valores[0]
        usuario_editando = db.obtener_usuario(id_usuario)
        if usuario_editando:
            _, nombre, apellido, telefono, membresia, _, _ = usuario_editando
            entry_nombre.delete(0, tk.END)
            entry_nombre.insert(0, nombre)
            entry_apellido.delete(0, tk.END)
            entry_apellido.insert(0, apellido)
            entry_telefono.delete(0, tk.END)
            entry_telefono.insert(0, telefono)
            combo_membresia.set(membresia)
            btn_registrar.config(text="Actualizar")
            
def eliminar_usuario_gui():
    sel = lista_usuarios.selection()
    if not sel:
        messagebox.showwarning("Selecciona un usuario", "Primero selecciona un usuario para eliminar.")
        return

    valores = lista_usuarios.item(sel[0], "values")  
    
    try:
        id_usuario = int(valores[0]) 
        nombre = valores[1]
        apellido = valores[2]
    except (IndexError, ValueError):
        messagebox.showerror("Error", "No se pudo obtener la información del usuario.")
        return

    confirmacion = messagebox.askyesno(
        "Confirmar eliminación",
        f"¿Estás seguro de eliminar al usuario '{nombre} {apellido}'?"
    )
    if confirmacion:
        db.eliminar_usuario(id_usuario)
        messagebox.showinfo("Usuario eliminado", f"El usuario '{nombre} {apellido}' fue eliminado correctamente.")
        cargar_usuarios_en_lista()
        limpiar_campos()

def abrir_ventana_registro():
    global entry_nombre, entry_apellido, entry_telefono, combo_membresia, lista_usuarios, btn_registrar

    root = tk.Tk()
    root.title("Registro de Usuarios - Gimnasio")

  
    ancho_ventana = 800
    alto_ventana = 500

    ancho_pantalla = root.winfo_screenwidth()
    alto_pantalla = root.winfo_screenheight()

    x = (ancho_pantalla // 2) - (ancho_ventana // 2)
    y = (alto_pantalla // 2) - (alto_ventana // 2)

    root.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

    frm_form = tk.Frame(root)
    frm_form.pack(pady=10, padx=10, fill=tk.X)

    tk.Label(frm_form, text="Nombre:").grid(row=0, column=0, sticky="w")
    entry_nombre = tk.Entry(frm_form)
    entry_nombre.grid(row=0, column=1, sticky="ew")

    tk.Label(frm_form, text="Apellido:").grid(row=1, column=0, sticky="w")
    entry_apellido = tk.Entry(frm_form)
    entry_apellido.grid(row=1, column=1, sticky="ew")

    tk.Label(frm_form, text="Teléfono:").grid(row=2, column=0, sticky="w")
    entry_telefono = tk.Entry(frm_form)
    entry_telefono.grid(row=2, column=1, sticky="ew")

    tk.Label(frm_form, text="Tipo membresía:").grid(row=3, column=0, sticky="w")
    combo_membresia = ttk.Combobox(frm_form, values=["Mensual", "Trimestral", "Anual"], state="readonly")
    combo_membresia.grid(row=3, column=1, sticky="ew")

    frm_form.columnconfigure(1, weight=1)

    # Botones: Registrar, Nuevo, Eliminar
    frm_botones = tk.Frame(root)
    frm_botones.pack(pady=10)

    btn_registrar = tk.Button(frm_botones, text="Registrar", command=registrar_usuario)
    btn_registrar.pack(side="left", padx=5)

    btn_nuevo = tk.Button(frm_botones, text="Nuevo", command=limpiar_campos)
    btn_nuevo.pack(side="left", padx=5)
    
    btn_eliminar = tk.Button(frm_botones, text="Eliminar", command=eliminar_usuario_gui)
    btn_eliminar.pack(side="left", padx=5)

    columnas = ("ID", "Nombre", "Apellido", "Teléfono", "Membresía", "Vence")
    lista_usuarios = ttk.Treeview(root, columns=columnas, show="headings", height=10)
    for col in columnas:
        lista_usuarios.heading(col, text=col)
        lista_usuarios.column(col, anchor="center")

    lista_usuarios.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    lista_usuarios.bind("<Double-1>", on_usuario_doble_click)

    cargar_usuarios_en_lista()
    root.mainloop()

def verificar_login():
    usuario = entry_usuario.get().strip()
    contrasena = entry_contrasena.get()
    if db.verificar_credenciales(usuario, contrasena):
        login.destroy()
        abrir_ventana_registro()
    else:
        messagebox.showerror("Error de login", "Usuario o contraseña incorrectos.")

# Función para mostrar/ocultar contraseña 
def toggle_password(entry_widget, button_widget):
    if entry_widget.cget("show") == "":
        entry_widget.config(show="*")
        button_widget.config(text="Mostrar contraseña")
    else:
        entry_widget.config(show="")
        button_widget.config(text="Ocultar contraseña")

login = tk.Tk()
login.title("Login - Gimnasio")
ancho_ventana = 300
alto_ventana = 180

ancho_pantalla = login.winfo_screenwidth()
alto_pantalla = login.winfo_screenheight()

x = (ancho_pantalla // 2) - (ancho_ventana // 2)
y = (alto_pantalla // 2) - (alto_ventana // 2)

login.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")

# Usuario
tk.Label(login, text="Usuario:").pack(pady=5)
entry_usuario = tk.Entry(login)
entry_usuario.pack()

# Contraseña
tk.Label(login, text="Contraseña:").pack(pady=5)
entry_contrasena = tk.Entry(login, show="*")
entry_contrasena.pack()

# Botón Mostrar/Ocultar
btn_toggle = tk.Button(login, text="Mostrar contraseña") 
btn_toggle.config(command=lambda e=entry_contrasena, b=btn_toggle: toggle_password(e, b))
btn_toggle.pack(pady=2)

# Botón Ingresar
tk.Button(login, text="Ingresar", command=verificar_login).pack(pady=10)

login.mainloop()