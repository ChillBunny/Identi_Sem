# Analizador semántico

Analizador semántico para una calculadora con variables de tipo `entero` y `decimal`, hecho
en Python con una ventana en Tkinter. Trabaja encima de los dos analizadores anteriores:

1. El analizador léxico, hecho con FLEX (`analizador.l`), convierte el texto en tokens.
2. El analizador sintáctico, descendente recursivo (`sintactico.py`), revisa el orden de los
   tokens y arma el árbol de cada instrucción.
3. El analizador semántico (`semantico.py`) recorre cada árbol, le calcula a cada nodo su
   tipo y su valor, lleva la tabla de símbolos y reporta los errores de significado.

Para usarlo basta con abrir `AnalizadorSemantico.exe`, escribir el código y presionar
**Analizar** (o F5). La ventana muestra el resultado de cada instrucción, el árbol anotado,
la tabla de símbolos, los tokens, y la gramática con sus reglas semánticas.

Después de cambiar `analizador.l`, `sintactico.py`, `semantico.py` o `app.py`,
`compilar.bat` vuelve a generar todo: el analizador léxico con flex y gcc, y el ejecutable
con PyInstaller. Necesita flex y gcc en `%USERPROFILE%\herramientas-compiladores` y Python
con PyInstaller.

## El lenguaje

Cada instrucción ocupa una línea. Una variable se declara con su tipo y después se le puede
asignar otro valor sin repetir el tipo.

```
# precio con descuento
decimal precio = 150.50
decimal descuento = 0.15
decimal total = precio - (precio * descuento)
entero cantidad = 7
entero mitad = cantidad / 2
total = total + mitad
```

Los tokens son NUMERO, IDENTIFICADOR, TIPO (`entero` o `decimal`), ASIGNACION (`=`), SUMA,
RESTA, MULT, DIV, PAR_IZQ, PAR_DER y COMENTARIO (`#` hasta el final de la línea).

## La gramática

```
programa     →  instruccion*
instruccion  →  TIPO  IDENTIFICADOR  =  expresion      (declaración)
             |  IDENTIFICADOR  =  expresion            (asignación)
expresion    →  termino  ( ( + | - )  termino )*
termino      →  factor  ( ( * | / )  factor )*
factor       →  NUMERO
             |  IDENTIFICADOR
             |  ( expresion )
             |  -  factor
```

## Las reglas semánticas

Cada nodo del árbol tiene dos atributos, `tipo` y `valor`, que se calculan a partir de los de
sus hijos, de las hojas hacia la raíz.

| Producción | Regla semántica |
|---|---|
| factor → NUMERO | tipo = `entero` si no tiene punto, `decimal` si lo tiene; valor = el número |
| factor → IDENTIFICADOR | la variable tiene que estar declarada; tipo y valor salen de la tabla de símbolos |
| factor → - factor1 | tipo = factor1.tipo; valor = - factor1.valor |
| a + b, a - b, a * b | tipo = `entero` si los dos son `entero`; si no, `decimal` |
| a / b | b no puede valer 0; entre dos enteros la división es entera (7 / 2 = 3) |
| declaración | la variable no puede estar declarada antes; un decimal no se guarda en una variable `entero`; la variable se agrega a la tabla de símbolos |
| asignación | la variable tiene que estar declarada; un decimal no se guarda en una variable `entero` |

Un entero sí se puede guardar en una variable `decimal`: `decimal e = 5` guarda 5.0.

## Errores

Los errores léxicos detienen el análisis. Los sintácticos y los semánticos se reportan por
línea, y el análisis sigue con la línea siguiente.

| Instrucción | Error |
|---|---|
| `entero x = 2.5` | Semántico: no se puede guardar un decimal en 'x', que es entero |
| `y = 4` | Semántico: la variable 'y' no fue declarada |
| `entero a = 9` (con `a` ya declarada) | Semántico: la variable 'a' ya fue declarada en la línea 3 |
| `decimal z = w + 1` | Semántico: la variable 'w' no fue declarada |
| `entero d = 10 / (5 - 5)` | Semántico: división entre cero |
| `entero k = 3 +` | Sintáctico: falta un número, una variable o '(' después de '+' |
