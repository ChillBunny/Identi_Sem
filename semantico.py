# analizador semantico: recorre el arbol de cada instruccion y le calcula a cada nodo
# dos atributos, su tipo (entero o decimal) y su valor. los atributos de un nodo salen
# de los de sus hijos, asi que se calculan de las hojas hacia la raiz


class ErrorSemantico(Exception):
    def __init__(self, mensaje, linea):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.linea = linea


class AnalizadorSemantico:
    def __init__(self):
        # tabla de simbolos: nombre de la variable -> {"tipo", "valor", "linea"}
        self.tabla = {}
        self.errores = []
        self.linea = 0

    # revisa las instrucciones en orden. si una tiene error se reporta y se sigue
    # con la siguiente
    def analizar(self, instrucciones):
        for linea, arbol in instrucciones:
            self.linea = linea
            try:
                if arbol.tipo == "DECLARACION":
                    self.declaracion(arbol)
                else:
                    self.asignacion(arbol)
            except ErrorSemantico as error:
                self.errores.append(error)
        return self.errores

    def error(self, mensaje):
        raise ErrorSemantico(mensaje, self.linea)

    # TIPO IDENTIFICADOR = expresion
    def declaracion(self, arbol):
        tipo, variable, expresion = arbol.hijos
        nombre = variable.nombre
        if nombre in self.tabla:
            linea_anterior = self.tabla[nombre]["linea"]
            self.error(f"La variable '{nombre}' ya fue declarada en la línea {linea_anterior}")

        self.expresion(expresion)
        valor = self.revisar_tipos(tipo.nombre, expresion, nombre)
        self.tabla[nombre] = {"tipo": tipo.nombre, "valor": valor, "linea": self.linea}
        anotar(variable, tipo.nombre, valor)
        anotar(arbol, tipo.nombre, valor)

    # IDENTIFICADOR = expresion
    def asignacion(self, arbol):
        variable, expresion = arbol.hijos
        nombre = variable.nombre
        if nombre not in self.tabla:
            self.error(f"La variable '{nombre}' no fue declarada")

        self.expresion(expresion)
        tipo = self.tabla[nombre]["tipo"]
        valor = self.revisar_tipos(tipo, expresion, nombre)
        self.tabla[nombre]["valor"] = valor
        anotar(variable, tipo, valor)
        anotar(arbol, tipo, valor)

    # un decimal no se puede guardar en una variable entero, porque se perderian
    # los decimales. al reves si se puede: el 5 se guarda como 5.0
    def revisar_tipos(self, tipo_variable, expresion, nombre):
        if tipo_variable == "entero" and expresion.tipo_dato == "decimal":
            self.error(f"No se puede guardar un decimal en '{nombre}', que es entero")
        if tipo_variable == "decimal":
            return float(expresion.valor)
        return expresion.valor

    # calcula el tipo y el valor de cada nodo de una expresion
    def expresion(self, nodo):
        if nodo.tipo == "NUMERO":
            if "." in nodo.nombre:
                anotar(nodo, "decimal", float(nodo.nombre))
            else:
                anotar(nodo, "entero", int(nodo.nombre))
            return

        if nodo.tipo == "IDENTIFICADOR":
            if nodo.nombre not in self.tabla:
                self.error(f"La variable '{nodo.nombre}' no fue declarada")
            simbolo = self.tabla[nodo.nombre]
            anotar(nodo, simbolo["tipo"], simbolo["valor"])
            return

        # es un operador: primero se calculan los hijos
        for hijo in nodo.hijos:
            self.expresion(hijo)

        # el menos de un numero negativo tiene un solo hijo
        if len(nodo.hijos) == 1:
            hijo = nodo.hijos[0]
            anotar(nodo, hijo.tipo_dato, -hijo.valor)
            return

        izquierdo = nodo.hijos[0]
        derecho = nodo.hijos[1]

        # si los dos son entero el resultado es entero; si alguno es decimal, es decimal
        if izquierdo.tipo_dato == "entero" and derecho.tipo_dato == "entero":
            tipo = "entero"
        else:
            tipo = "decimal"

        if nodo.nombre == "+":
            valor = izquierdo.valor + derecho.valor
        elif nodo.nombre == "-":
            valor = izquierdo.valor - derecho.valor
        elif nodo.nombre == "*":
            valor = izquierdo.valor * derecho.valor
        else:
            if derecho.valor == 0:
                self.error("División entre cero")
            if tipo == "entero":
                # entre dos enteros la division es entera, como en C: 7 / 2 = 3
                valor = int(izquierdo.valor / derecho.valor)
            else:
                valor = izquierdo.valor / derecho.valor

        anotar(nodo, tipo, valor)


def anotar(nodo, tipo, valor):
    nodo.tipo_dato = tipo
    nodo.valor = valor


# el entero se muestra tal cual y el decimal con su punto (5.0), cortando los
# decimales largos
def formatear(valor):
    if isinstance(valor, int):
        return str(valor)
    return str(round(valor, 4))
