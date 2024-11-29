import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

# Configuración de la base de datos
DB_NAME = "tpv_peluqueria.db"

# Inicialización de Tkinter
root = tk.Tk()
root.title("TPV - Salón de Peluquería")
root.geometry("1200x700")
root.configure(bg="white")

# Variables de Tkinter
ticket = []
total = tk.DoubleVar(value=0.0)
empleado_actual = tk.StringVar(value="No seleccionado")
productos_servicios = {}
empleados = {}

# Función para inicializar la base de datos
def inicializar_base_datos():
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        if not cursor.fetchall():
            messagebox.showerror("Error", "La base de datos no está configurada.")
        conexion.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo conectar a la base de datos: {e}")

# Función para cargar datos de la base de datos
def cargar_datos():
    global productos_servicios, empleados
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()

        # Cargar productos/servicios
        cursor.execute("SELECT id, nombre, precio FROM productos_servicios")
        productos_servicios = {row[1]: {"id": row[0], "precio": row[2]} for row in cursor.fetchall()}

        # Cargar empleados
        cursor.execute("SELECT id, nombre FROM empleados")
        empleados = {row[1]: row[0] for row in cursor.fetchall()}
        conexion.close()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron cargar los datos: {e}")

# Función para actualizar el ticket
def actualizar_ticket():
    global ticket
    try:
        area_ticket.delete(1.0, tk.END)
        # Ajustamos los márgenes de cada columna para evitar superposición
        area_ticket.insert(tk.END, f"{'Producto':<25}{'Cant.':<8}{'Total':<10}\n")
        area_ticket.insert(tk.END, f"{'-'*45}\n")
        for item in ticket:
            area_ticket.insert(tk.END, f"{item[0]:<25}{item[1]:<8}{item[2]:.2f} €\n")
        total.set(sum(item[2] for item in ticket))  # Recalculamos el total correctamente
    except Exception as e:
        messagebox.showerror("Error", f"Error al actualizar el ticket: {e}")

# Función para agregar productos al ticket
def agregar_producto(nombre, precio):
    global ticket
    try:
        for item in ticket:
            if item[0] == nombre:
                item[1] += 1
                item[2] += precio
                actualizar_ticket()
                return
        ticket.append([nombre, 1, precio])
        actualizar_ticket()
    except Exception as e:
        messagebox.showerror("Error", f"Error al agregar el producto: {e}")

# Función para limpiar el ticket
def limpiar_ticket():
    global ticket
    ticket.clear()
    actualizar_ticket()

# Función para eliminar una línea del ticket
def eliminar_linea():
    try:
        seleccion = area_ticket.index(tk.SEL_FIRST)
        indice = int(seleccion.split(".")[0]) - 3
        if 0 <= indice < len(ticket):
            ticket.pop(indice)
            actualizar_ticket()
    except tk.TclError:
        messagebox.showerror("Error", "Selecciona una línea del ticket para eliminar.")

# Función para registrar una venta
def registrar_venta(metodo_pago):
    if not ticket:
        messagebox.showerror("Error", "El ticket está vacío.")
        return
    empleado_nombre = empleado_actual.get()
    if empleado_nombre == "No seleccionado" or empleado_nombre not in empleados:
        messagebox.showerror("Error", "Selecciona un empleado válido.")
        return
    cliente = entry_cliente.get().strip()
    if not cliente:
        messagebox.showerror("Error", "El campo de cliente es obligatorio.")
        return

    try:
        # Conectar a la base de datos
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()

        # Registrar cliente si no existe
        cursor.execute("SELECT id FROM clientes WHERE nombre = ?", (cliente,))
        cliente_data = cursor.fetchone()
        if cliente_data:
            cliente_id = cliente_data[0]
        else:
            cursor.execute("INSERT INTO clientes (nombre) VALUES (?)", (cliente,))
            cliente_id = cursor.lastrowid

        # Registrar venta
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO ventas (fecha, id_empleado, id_cliente, total, forma_pago)
            VALUES (?, ?, ?, ?, ?)
        """, (fecha, empleados[empleado_nombre], cliente_id, total.get(), metodo_pago))
        id_venta = cursor.lastrowid

        # Registrar detalles de la venta
        for item in ticket:
            cursor.execute("""
                INSERT INTO detalle_ventas (id_venta, id_producto_servicio, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (id_venta, productos_servicios[item[0]]["id"], item[1], productos_servicios[item[0]]["precio"], item[2]))

        conexion.commit()
        conexion.close()
        messagebox.showinfo("Éxito", "Venta registrada correctamente.")
        limpiar_ticket()
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo registrar la venta: {e}")

# Función para cobrar el ticket
def cobrar_ticket():
    if not ticket:
        messagebox.showerror("Error", "El ticket está vacío.")
        return

    def procesar_pago(metodo):
        registrar_venta(metodo)
        ventana_pago.destroy()

    ventana_pago = tk.Toplevel(root)
    ventana_pago.title("Cobrar Ticket")
    ventana_pago.geometry("300x200")

    tk.Label(ventana_pago, text="Selecciona método de pago:", font=("Helvetica", 14)).pack(pady=20)
    tk.Button(ventana_pago, text="Efectivo", font=("Helvetica", 12), bg="lightgreen", command=lambda: procesar_pago("efectivo")).pack(fill=tk.X, padx=20, pady=10)
    tk.Button(ventana_pago, text="Tarjeta", font=("Helvetica", 12), bg="lightblue", command=lambda: procesar_pago("tarjeta")).pack(fill=tk.X, padx=20, pady=10)

# Configuración de la interfaz gráfica
frame_izquierdo = tk.Frame(root, bg="lightgray", padx=10, pady=10)
frame_izquierdo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk.Label(frame_izquierdo, text="Productos y Servicios", font=("Helvetica", 16), bg="lightgray").pack(anchor="w", pady=10)

# Scroll para productos
scrollbar = tk.Scrollbar(frame_izquierdo)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

productos_canvas = tk.Canvas(frame_izquierdo, yscrollcommand=scrollbar.set, bg="white")
productos_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

productos_frame = tk.Frame(productos_canvas, bg="white")
productos_canvas.create_window((0, 0), window=productos_frame, anchor="nw")

scrollbar.config(command=productos_canvas.yview)

# Productos/Servicios
def cargar_botones_productos():
    for widget in productos_frame.winfo_children():
        widget.destroy()
    for nombre, datos in productos_servicios.items():
        tk.Button(productos_frame, text=f"{nombre} - {datos['precio']} €", font=("Helvetica", 12), bg="white", command=lambda n=nombre, p=datos["precio"]: agregar_producto(n, p)).pack(fill=tk.X, pady=5)

frame_derecho = tk.Frame(root, bg="white", padx=10, pady=10)
frame_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

tk.Label(frame_derecho, text="Ticket", font=("Helvetica", 16), bg="white").pack(anchor="w", pady=10)
area_ticket = tk.Text(frame_derecho, height=20, font=("Courier", 12), relief=tk.SUNKEN, bd=1)
area_ticket.pack(fill=tk.BOTH, expand=True)

tk.Label(frame_derecho, text="Total:", font=("Helvetica", 14), bg="white").pack(anchor="w", pady=5)
tk.Label(frame_derecho, textvariable=total, font=("Helvetica", 16, "bold"), bg="white").pack(anchor="w", pady=5)

tk.Label(frame_derecho, text="Empleado:", font=("Helvetica", 12), bg="white").pack(anchor="w", pady=5)
combo_empleados = ttk.Combobox(frame_derecho, values=[], textvariable=empleado_actual)
combo_empleados.pack(anchor="w", pady=5)

tk.Label(frame_derecho, text="Cliente:", font=("Helvetica", 12), bg="white").pack(anchor="w", pady=5)
entry_cliente = tk.Entry(frame_derecho, font=("Helvetica", 12))
entry_cliente.pack(anchor="w", pady=5)

frame_botones = tk.Frame(frame_derecho, bg="white", pady=10)
frame_botones.pack(fill=tk.X)

tk.Button(frame_botones, text="Nuevo Ticket", font=("Helvetica", 12), bg="lightgray", command=limpiar_ticket).pack(side=tk.LEFT, padx=5)
tk.Button(frame_botones, text="Eliminar Línea", font=("Helvetica", 12), bg="lightgray", command=eliminar_linea).pack(side=tk.LEFT, padx=5)
tk.Button(frame_botones, text="Cobrar Ticket", font=("Helvetica", 12), bg="orange", command=cobrar_ticket).pack(side=tk.RIGHT, padx=5)

# Inicializar base de datos y cargar datos
inicializar_base_datos()
cargar_datos()
cargar_botones_productos()
combo_empleados["values"] = list(empleados.keys())

root.mainloop()
