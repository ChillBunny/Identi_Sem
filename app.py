import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from sintactico import AnalizadorSintactico, obtener_tokens
from semantico import AnalizadorSemantico, formatear


GRAMATICA = """GRAMÁTICA

programa     →  instruccion*

instruccion  →  TIPO  IDENTIFICADOR  =  expresion      (declaración)
             |  IDENTIFICADOR  =  expresion            (asignación)

expresion    →  termino  ( ( + | - )  termino )*

termino      →  factor  ( ( * | / )  factor )*

factor       →  NUMERO
             |  IDENTIFICADOR
             |  ( expresion )
             |  -  factor

TIPO es la palabra entero o decimal. Cada instrucción ocupa una línea.


REGLAS SEMÁNTICAS

Cada nodo del árbol tiene dos atributos, tipo y valor, que se calculan
a partir de los de sus hijos.

factor → NUMERO          tipo = entero si no tiene punto, decimal si lo tiene
                         valor = el número

factor → IDENTIFICADOR   la variable tiene que estar declarada
                         tipo y valor = los de la tabla de símbolos

factor → - factor1       tipo = factor1.tipo      valor = - factor1.valor

a + b,  a - b,  a * b    tipo = entero si a y b son entero; si no, decimal

a / b                    b no puede valer 0
                         entre dos enteros la división es entera (7 / 2 = 3)

declaración              la variable no puede estar declarada antes
                         un decimal no se guarda en una variable entero
                         la variable se agrega a la tabla de símbolos

asignación               la variable tiene que estar declarada
                         un decimal no se guarda en una variable entero
"""

# lo que se muestra en la pestaña del arbol: (linea, texto de la instruccion, arbol)
arboles = []


# boton Analizar
def analizar():
    global arboles
    texto = editor.get("1.0", "end-1c")
    lineas = texto.split("\n")

    try:
        tokens = obtener_tokens(texto)
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró analizador.exe.\nPrimero hay que correr compilar.bat")
        return

    limpiar_resultados()
    llenar_tabla_tokens(tokens)

    # el analisis sintactico trabaja sobre los tokens del lexico,
    # asi que si hay errores lexicos no se puede seguir
    errores_lexicos = [t for t in tokens if t[0] == "ERROR"]
    if errores_lexicos:
        for tipo, lexema, linea, columna in errores_lexicos:
            mensaje = f"Error léxico: '{lexema}' no pertenece al lenguaje"
            tabla_analisis.insert("", "end", values=(linea, lineas[linea - 1].strip(), mensaje), tags=("error",))
            marcar(linea, columna, lexema)
        etiqueta_resumen.config(text=f"{len(errores_lexicos)} errores léxicos. Hay que corregirlos antes del análisis sintáctico.", foreground="red")
        return

    # los comentarios no forman parte de la gramatica
    tokens = [t for t in tokens if t[0] != "COMENTARIO"]
    analizador = AnalizadorSintactico(tokens)
    instrucciones, errores = analizador.programa()

    # el analisis semantico solo revisa las instrucciones que pasaron el sintactico
    semantico = AnalizadorSemantico()
    errores_semanticos = semantico.analizar(instrucciones)
    lineas_con_error = {}
    for error in errores_semanticos:
        lineas_con_error[error.linea] = error.mensaje
        marcar_linea(error.linea)

    # una fila por instruccion, en el orden en que aparecen
    filas = []
    for linea, arbol in instrucciones:
        if linea in lineas_con_error:
            filas.append((linea, lineas[linea - 1].strip(), "Error semántico: " + lineas_con_error[linea], "error"))
        else:
            filas.append((linea, lineas[linea - 1].strip(), "Correcta", ""))
    for error in errores:
        filas.append((error.linea, lineas[error.linea - 1].strip(), "Error sintáctico: " + error.mensaje, "error"))
        marcar(error.linea, error.columna, error.lexema)
    filas.sort()
    for linea, instruccion, estado, etiqueta in filas:
        tabla_analisis.insert("", "end", values=(linea, instruccion, estado), tags=(etiqueta,))

    arboles = []
    for linea, arbol in instrucciones:
        arboles.append((linea, lineas[linea - 1].strip(), arbol))
    selector_arbol["values"] = [f"Línea {linea}:  {texto_linea}" for linea, texto_linea, arbol in arboles]
    if arboles:
        selector_arbol.current(0)
        mostrar_arbol()

    llenar_tabla_simbolos(semantico.tabla)

    total = len(instrucciones) + len(errores)
    if errores or errores_semanticos:
        etiqueta_resumen.config(text=f"{len(errores)} errores sintácticos y {len(errores_semanticos)} errores semánticos en {total} instrucciones", foreground="red")
    else:
        etiqueta_resumen.config(text=f"Sin errores: {total} instrucciones", foreground="dark green")


def limpiar_resultados():
    editor.tag_remove("error", "1.0", "end")
    tabla_analisis.delete(*tabla_analisis.get_children())
    tabla_simbolos.delete(*tabla_simbolos.get_children())
    tabla_tokens.delete(*tabla_tokens.get_children())
    selector_arbol.set("")
    selector_arbol["values"] = []
    lienzo.delete("all")
    etiqueta_resumen.config(text="")


# pinta de rojo en el editor el lugar del error
def marcar(linea, columna, lexema):
    # en tkinter las columnas empiezan en 0 y en el analizador en 1
    inicio = f"{linea}.{columna - 1}"
    fin = f"{linea}.{columna - 1 + max(len(lexema), 1)}"
    editor.tag_add("error", inicio, fin)


# el error semantico es de toda la instruccion, asi que se pinta la linea completa
def marcar_linea(linea):
    editor.tag_add("error", f"{linea}.0", f"{linea}.end")


def llenar_tabla_tokens(tokens):
    for tipo, lexema, linea, columna in tokens:
        if tipo == "ERROR":
            tabla_tokens.insert("", "end", values=(tipo, lexema, linea, columna), tags=("error",))
        else:
            tabla_tokens.insert("", "end", values=(tipo, lexema, linea, columna))


def llenar_tabla_simbolos(tabla):
    for nombre, simbolo in tabla.items():
        tabla_simbolos.insert("", "end", values=(nombre, simbolo["tipo"], formatear(simbolo["valor"]), simbolo["linea"]))


# ---------------------------------------------------------------------------------------------
# dibujo del arbol

ALTO_NIVEL = 90
MARGEN = 50


def mostrar_arbol(evento=None):
    indice = selector_arbol.current()
    if indice < 0:
        return
    lienzo.delete("all")
    dibujar_arbol(arboles[indice][2])


# a cada nodo le toca una posicion: las hojas van una por columna, de izquierda
# a derecha, y cada nodo de adentro queda centrado arriba de sus hijos
def ubicar(nodo, nivel, posiciones, columnas_usadas, ancho_columna):
    if not nodo.hijos:
        x = columnas_usadas[0]
        columnas_usadas[0] = columnas_usadas[0] + 1
    else:
        suma = 0
        for hijo in nodo.hijos:
            suma = suma + ubicar(hijo, nivel + 1, posiciones, columnas_usadas, ancho_columna)
        x = suma / len(nodo.hijos)
    posiciones[id(nodo)] = (MARGEN + x * ancho_columna, MARGEN + nivel * ALTO_NIVEL)
    return x


# lo que va debajo de cada nodo: su tipo y su valor. si el semantico no llego a
# calcularlos (por un error) queda vacio
def anotacion(nodo):
    if nodo.tipo_dato is None:
        return ""
    return f"{nodo.tipo_dato}: {formatear(nodo.valor)}"


# lo que ocupa a lo ancho el nodo mas ancho del arbol (el ovalo o la anotacion,
# el que sea mas largo), para que las hojas no se encimen
def ancho_mas_grande(nodo):
    ancho = max(len(nodo.nombre) * 10 + 20, len(anotacion(nodo)) * 7)
    for hijo in nodo.hijos:
        ancho = max(ancho, ancho_mas_grande(hijo))
    return ancho


def dibujar_arbol(arbol):
    ancho_columna = max(80, ancho_mas_grande(arbol) + 20)
    posiciones = {}
    ubicar(arbol, 0, posiciones, [0], ancho_columna)
    dibujar_lineas(arbol, posiciones)
    dibujar_nodos(arbol, posiciones)
    caja = lienzo.bbox("all")
    lienzo.config(scrollregion=(0, 0, caja[2] + MARGEN, caja[3] + MARGEN))


# primero las lineas, para que los nodos queden encima
def dibujar_lineas(nodo, posiciones):
    x, y = posiciones[id(nodo)]
    for hijo in nodo.hijos:
        hijo_x, hijo_y = posiciones[id(hijo)]
        lienzo.create_line(x, y, hijo_x, hijo_y, width=1.5)
        dibujar_lineas(hijo, posiciones)


def dibujar_nodos(nodo, posiciones):
    x, y = posiciones[id(nodo)]
    # los nodos con hijos en azul, el tipo en amarillo y las hojas en verde
    if nodo.hijos:
        color = "#d6e4ff"
    elif nodo.tipo == "TIPO":
        color = "#fff2cc"
    else:
        color = "#d9f2d9"
    ancho = max(18, len(nodo.nombre) * 5 + 10)
    lienzo.create_oval(x - ancho, y - 18, x + ancho, y + 18, fill=color, width=1.5)
    lienzo.create_text(x, y, text=nodo.nombre, font=("Consolas", 11, "bold"))

    # la anotacion lleva un fondo blanco para que no la tape la linea hacia los hijos
    if anotacion(nodo) != "":
        texto = lienzo.create_text(x, y + 30, text=anotacion(nodo), font=("Consolas", 9), fill="#1f4e9e")
        fondo = lienzo.create_rectangle(lienzo.bbox(texto), fill="white", outline="")
        lienzo.tag_lower(fondo, texto)
    for hijo in nodo.hijos:
        dibujar_nodos(hijo, posiciones)


# ---------------------------------------------------------------------------------------------
# botones

def abrir_archivo():
    ruta = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    if ruta == "":
        return
    with open(ruta, encoding="utf-8", errors="replace") as archivo:
        contenido = archivo.read()
    editor.delete("1.0", "end")
    editor.insert("1.0", contenido)
    analizar()


def limpiar():
    editor.delete("1.0", "end")
    limpiar_resultados()


# ---------------------------------------------------------------------------------------------
# ventana principal

def crear_tabla(marco, columnas, anchos):
    tabla = ttk.Treeview(marco, columns=columnas, show="headings")
    for columna, ancho in zip(columnas, anchos):
        tabla.heading(columna, text=columna)
        tabla.column(columna, width=ancho, stretch=(ancho > 100))
    tabla.tag_configure("error", background="#ffb3b3")
    barra = ttk.Scrollbar(marco, command=tabla.yview)
    tabla.config(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    tabla.pack(fill="both", expand=True)
    return tabla


def crear_ventana():
    global editor, tabla_analisis, tabla_simbolos, tabla_tokens, selector_arbol, lienzo, etiqueta_resumen

    ventana = tk.Tk()
    ventana.title("Analizador semántico - Calculadora con variables")
    ventana.geometry("1200x700")

    # barra de arriba con los botones
    barra = ttk.Frame(ventana, padding=8)
    barra.pack(fill="x")
    ttk.Label(barra, text="Analizador semántico", font=("Segoe UI", 14, "bold")).pack(side="left")
    ttk.Label(barra, text="   F5 = analizar", foreground="gray").pack(side="left")
    ttk.Button(barra, text="Limpiar", command=limpiar).pack(side="right", padx=4)
    ttk.Button(barra, text="Analizar", command=analizar).pack(side="right", padx=4)
    ttk.Button(barra, text="Abrir archivo", command=abrir_archivo).pack(side="right", padx=4)

    # abajo, el resumen
    etiqueta_resumen = ttk.Label(ventana, text="", padding=8, font=("Segoe UI", 10, "bold"))
    etiqueta_resumen.pack(side="bottom", fill="x")

    panel = ttk.PanedWindow(ventana, orient="horizontal")
    panel.pack(fill="both", expand=True, padx=8)

    # a la izquierda el editor
    marco_editor = ttk.LabelFrame(panel, text="Código fuente", padding=4)
    editor = tk.Text(marco_editor, font=("Consolas", 12), undo=True, wrap="none", width=45)
    barra_editor = ttk.Scrollbar(marco_editor, command=editor.yview)
    editor.config(yscrollcommand=barra_editor.set)
    barra_editor.pack(side="right", fill="y")
    editor.pack(fill="both", expand=True)
    editor.tag_config("error", background="#ffb3b3")
    panel.add(marco_editor, weight=2)

    # a la derecha, una pestaña por cada cosa para no amontonar
    pestanas = ttk.Notebook(panel)
    panel.add(pestanas, weight=3)

    marco_analisis = ttk.Frame(pestanas)
    tabla_analisis = crear_tabla(marco_analisis, ("Línea", "Instrucción", "Resultado"), (60, 260, 400))
    pestanas.add(marco_analisis, text="Análisis")

    marco_arbol = ttk.Frame(pestanas, padding=6)
    fila = ttk.Frame(marco_arbol)
    fila.pack(fill="x")
    ttk.Label(fila, text="Instrucción:").pack(side="left")
    selector_arbol = ttk.Combobox(fila, state="readonly", width=55)
    selector_arbol.pack(side="left", padx=6)
    selector_arbol.bind("<<ComboboxSelected>>", mostrar_arbol)
    lienzo = tk.Canvas(marco_arbol, background="white")
    barra_x = ttk.Scrollbar(marco_arbol, orient="horizontal", command=lienzo.xview)
    barra_y = ttk.Scrollbar(marco_arbol, command=lienzo.yview)
    lienzo.config(xscrollcommand=barra_x.set, yscrollcommand=barra_y.set)
    barra_x.pack(side="bottom", fill="x")
    barra_y.pack(side="right", fill="y")
    lienzo.pack(fill="both", expand=True, pady=(6, 0))
    pestanas.add(marco_arbol, text="Árbol anotado")

    marco_simbolos = ttk.Frame(pestanas)
    tabla_simbolos = crear_tabla(marco_simbolos, ("Variable", "Tipo", "Valor", "Declarada en la línea"), (160, 100, 200, 150))
    pestanas.add(marco_simbolos, text="Tabla de símbolos")

    marco_tokens = ttk.Frame(pestanas)
    tabla_tokens = crear_tabla(marco_tokens, ("Token", "Lexema", "Línea", "Columna"), (150, 260, 60, 70))
    pestanas.add(marco_tokens, text="Tokens")

    marco_gramatica = ttk.Frame(pestanas, padding=10)
    texto_gramatica = tk.Text(marco_gramatica, font=("Consolas", 12), relief="flat", background="white")
    texto_gramatica.insert("1.0", GRAMATICA)
    texto_gramatica.config(state="disabled")
    texto_gramatica.pack(fill="both", expand=True)
    pestanas.add(marco_gramatica, text="Gramática y reglas")

    ventana.bind("<F5>", lambda evento: analizar())

    # un ejemplo para que no arranque vacio
    editor.insert("1.0", "# precio con descuento\n"
                         "decimal precio = 150.50\n"
                         "decimal descuento = 0.15\n"
                         "decimal total = precio - (precio * descuento)\n"
                         "entero cantidad = 7\n"
                         "entero mitad = cantidad / 2\n"
                         "total = total + mitad\n")
    return ventana


if __name__ == "__main__":
    ventana = crear_ventana()
    ventana.state("zoomed")
    ventana.after(100, analizar)
    ventana.mainloop()
