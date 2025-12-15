"""Analizador estático simple de código Python.

Este script busca patrones comunes de código redundante o que pueden mejorarse,
como asignaciones redundantes, operaciones con 0 o 1, comparaciones booleanas
innecesarias, y detección de variables/funciones/clases/importaciones no utilizadas.

El programa lee un archivo llamado `codigo.txt` en el mismo directorio y
emite sugerencias que indican la línea y la mejora recomendada.
"""

import re
"""Patrones por línea.

`patrones_linea` es un diccionario cuyas claves son etiquetas que describen
el caso detectado (p. ej. "incremento", "suma0") y cuyos valores son
expresiones regulares que coinciden con una sola línea de código. Estas
expresiones capturan identificadores y literales necesarios para generar
sugerencias precisas.
"""
patrones_linea = {}
"""Patrones que se aplican al texto completo del archivo.

`patrones_completo` contiene expresiones regulares que se ejecutan sobre
el contenido completo del archivo para detectar elementos que no se usan
en todo el código (variables, listas, diccionarios, funciones o clases).
Las regex usan el modificador (?s) cuando es necesario para manejar
coincidencias multilínea.
"""
patrones_completo = {}
end_comment = r'(?:\s*(?:#.*)?)$'
patrones_linea["incremento"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\+\s*(-?\d+)\s*' + end_comment
patrones_linea["decremento"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*-\s*(-?\d+)\s*' + end_comment
patrones_linea["multiplicacion"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\*\s*(-?\d+)\s*' + end_comment
patrones_linea["division"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*/\s*(-?\d+)\s*' + end_comment
patrones_linea["modulo"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*%\s*(-?\d+)\s*' + end_comment
patrones_linea["exponente"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\*\*\s*(-?\d+)\s*' + end_comment
patrones_linea["asignacion"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["suma0"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\+\s*0\s*' + end_comment
patrones_linea["resta0"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*-\s*0\s*' + end_comment
patrones_linea["multiplicacion1"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\*\s*1\s*' + end_comment
patrones_linea["division1"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*/\s*1\s*' + end_comment
patrones_linea["modulo1"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*%\s*1\s*' + end_comment
patrones_linea["exponente1"] = r'^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\*\*\s*1\s*' + end_comment
patrones_linea["0suma"] = r'^\s*([A-Za-z_]\w*)\s*=\s*0\s*\+\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["0resta"] = r'^\s*([A-Za-z_]\w*)\s*=\s*0\s*-\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["1multiplicacion"] = r'^\s*([A-Za-z_]\w*)\s*=\s*1\s*\*\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["1division"] = r'^\s*([A-Za-z_]\w*)\s*=\s*1\s*/\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["1modulo"] = r'^\s*([A-Za-z_]\w*)\s*=\s*1\s*%\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["1exponente"] = r'^\s*([A-Za-z_]\w*)\s*=\s*1\s*\*\*\s*([A-Za-z_]\w*)\s*' + end_comment
patrones_linea["if_true"] = r'^\s*if\s*(\(([A-Za-z_]\w*)\s*==\s*True\))\s*:?\s*' + end_comment
patrones_linea["if_false"] = r'^\s*if\s*(\(([A-Za-z_]\w*)\s*==\s*False\))\s*:?\s*' + end_comment
patrones_linea["while_true"] = r'^\s*while\s*(\(([A-Za-z_]\w*)\s*==\s*True\))\s*:?\s*' + end_comment
patrones_linea["while_false"] = r'^\s*while\s*(\(([A-Za-z_]\w*)\s*==\s*False\))\s*:?\s*' + end_comment

patrones_completo["funcion_inutil"] = r'(?s)^(?!.*(def)\s*([A-Za-z_]\w*)(\(.*\)).*(def)\s*([A-Za-z_]\w*)(\(.*\))).*(def)\s*([A-Za-z_]\w*)(\(.*\)).*$'
patrones_completo["variable_inutil"] = r'(?s)^(?=.*\b([A-Za-z_]\w*)\s*=)(?!.*\b\1\b.*\b\1\b).*$'
patrones_completo["lista_inutil"] = r'(?s)^(?=.*\b([A-Za-z_]\w*)\s*=\s*\[.*\])(?!.*\b\1\b.*\b\1\b).*$'
patrones_completo["diccionario_inutil"] = r'(?s)^(?=.*\b([A-Za-z_]\w*)\s*=\s*\{.*\})(?!.*\b\1\b.*\b\1\b).*$'
patrones_completo["clase_inutil"] = r'(?s)^(?=.*\bclass\s+([A-Za-z_]\w*))(?!.*\b\1\b.*\b\1\b).*$'
patrones_completo["if_inutil"] = r'(?s)^(?=.*\bif\s*\(.*\):)(?!.*\bif\s*\(.*\):.*\b.*\b).*$'
patrones_completo["while_inutil"] = r'(?s)^(?=.*\bwhile\s*\(.*\):)(?!.*\bwhile\s*\(.*\):.*\b.*\b).*$'
patrones_completo["for_inutil"] = r'(?s)^(?=.*\bfor\s+([A-Za-z_]\w*)\s+in\s+.*:)(?!.*\b\1\b.*\b\1\b).*$'

"""Proceso principal.

Pasos:
1. Lee `codigo.txt`.
2. Recorre cada línea y aplica `patrones_linea` para detectar mejoras locales.
3. Aplica `patrones_completo` al contenido completo para detectar elementos no usados.
4. Detecta importaciones no utilizadas y añade sugerencias a la lista `respuesta`.
5. Imprime las sugerencias encontradas o un mensaje de felicitación si no hay.
"""
with open("codigo.txt", "r") as archivo:
    completo = archivo.read()
    linea = 0
    respuesta = []
    lineas = completo.splitlines()
    for codigo in lineas:
        linea += 1
        for caso, regex in patrones_linea.items():
            for flag in re.finditer(regex, codigo.strip()):
                match caso:
                    case "incremento":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} += {var3} en lugar de {var1} = {var2} + {var3}")
                    case "decremento":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} -= {var3} en lugar de {var1} = {var2} - {var3}")
                    case "multiplicacion":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} *= {var3} en lugar de {var1} = {var2} * {var3}")
                    case "division":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} /= {var3} en lugar de {var1} = {var2} / {var3}")
                    case "modulo":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} %= {var3} en lugar de {var1} = {var2} % {var3}")
                    case "exponente":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        var3 = flag.group(3)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera utilizar {var1} **= {var3} en lugar de {var1} = {var2} ** {var3}")
                    case "asignacion":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} la asignación {var1} = {var2} es redundante")
                    case "suma0":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la suma con 0 en {var1} = {var2} + 0")
                    case "resta0":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la resta con 0 en {var1} = {var2} - 0")
                    case "multiplicacion1":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la multiplicación por 1 en {var1} = {var2} * 1")
                    case "division1":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la división por 1 en {var1} = {var2} / 1")
                    case "modulo1":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar el módulo por 1 en {var1} = {var2} % 1")
                    case "exponente1":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la potenciación por 1 en {var1} = {var2} ** 1")
                    case "0suma":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la suma con 0 en {var1} = 0 + {var2}")
                    case "0resta":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la resta con 0 en {var1} = 0 - {var2}")
                    case "1multiplicacion":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la multiplicación por 1 en {var1} = 1 * {var2}")
                    case "1division":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la división por 1 en {var1} = 1 / {var2}")
                    case "1modulo":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar el módulo por 1 en {var1} = 1 % {var2}")
                    case "1exponente":
                        var1 = flag.group(1)
                        var2 = flag.group(2)
                        if var1 == var2:
                            respuesta.append(f"En la linea {linea} considera eliminar la potenciación por 1 en {var1} = 1 ** {var2}")
                    case "if_true":
                        var1 = flag.group(2)
                        respuesta.append(f"En la linea {linea} la condición if ({var1} == True) se puede simplificarla a if {var1}")
                    case "if_false":
                        var1 = flag.group(2)
                        respuesta.append(f"En la linea {linea} la condición if ({var1} == False) se puede simplificarla a if not {var1}")
                    case "while_true":
                        var1 = flag.group(2)
                        respuesta.append(f"En la linea {linea} la condición while ({var1} == True) se puede simplificarla a while {var1}")
                    case "while_false":
                        var1 = flag.group(2)
                        respuesta.append(f"En la linea {linea} la condición while ({var1} == False) se puede simplificarla a while not {var1}")
                                               
    for caso, regex in patrones_completo.items():
        for flag in re.finditer(regex, completo, re.S):
            if caso == "variable_inutil":
                inicio = flag.start(1)
            elif caso == "funcion_inutil":
                inicio = flag.start(8)
            elif caso in ("lista_inutil", "diccionario_inutil", "clase_inutil", "import_inutil"):
                inicio = flag.start(1)
            elif caso == "from_import_inutil":
                inicio = flag.start(2)
            elif caso == "for_inutil":
                inicio = flag.start(1)
            linea = completo[:inicio].count('\n') + 1
            match caso:
                case "variable_inutil":
                    var = flag.group(1)
                    respuesta.append(f"La variable {var} en la linea {linea} se asigna pero nunca se utiliza en el código")
                case "funcion_inutil":
                    func = flag.group(8)
                    respuesta.append(f"La función {func} en la linea {linea} no se utiliza en el código")
                case "lista_inutil":
                    lista = flag.group(1)
                    respuesta.append(f"La lista {lista} en la linea {linea} no se utiliza en el código")
                case "diccionario_inutil":
                    dict = flag.group(1)
                    respuesta.append(f"El diccionario {dict} en la linea {linea} no se utiliza en el código")
                case "if_inutil":
                    respuesta.append(f"El bloque if en la linea {linea} nunca se ejecuta o su contenido nunca se utiliza")
                case "while_inutil":
                    respuesta.append(f"El bloque while en la linea {linea} nunca se ejecuta o su contenido nunca se utiliza")
                case "for_inutil":
                    respuesta.append(f"El bloque for en la linea {linea} nunca se ejecuta o su contenido nunca se utiliza")
                case "clase_inutil":
                    clase = flag.group(1)
                    respuesta.append(f"La clase {clase} en la linea {linea} no se utiliza en el código")
                
    # Detección de imports y verificación de si se usan
    imports = []
    for m in re.finditer(r'^\s*import\s+([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?', completo, re.M):
        module = m.group(1)
        alias = m.group(2) or None
        identifier = alias if alias else module
        start_pos = m.start()
        line_no = completo[:start_pos].count('\n') + 1
        imports.append({'identifier': identifier, 'line': line_no})
    for m in re.finditer(r'^\s*from\s+([A-Za-z_]\w*)\s+import\s+([A-Za-z_]\w*)(?:\s+as\s+([A-Za-z_]\w*))?', completo, re.M):
        name = m.group(2)
        alias = m.group(3) or None
        identifier = alias if alias else name
        start_pos = m.start()
        line_no = completo[:start_pos].count('\n') + 1
        imports.append({'identifier': identifier, 'line': line_no})

    declaraciones = {}
    for declaracion in imports:
        declaraciones.setdefault(declaracion['identifier'], []).append(declaracion)

    for ident, decls in declaraciones.items():
        total_occ = len(re.findall(r'\b' + re.escape(ident) + r'\b', completo))
        num_decls = len(decls)
        if total_occ - num_decls <= 0:
            for d in decls:
                respuesta.append(f"La importación {ident} en la linea {d['line']} no se utiliza en el código")

# Salida: imprimir sugerencias si las hay, o un mensaje de éxito
if respuesta:
    with open("salida.txt", "w", encoding="utf-8") as archivo_salida:
        for sugerencia in respuesta:
            print(sugerencia)
            archivo_salida.write(sugerencia + "\n")
else:
    print("Felicitaciones! No se encontraron mejoras.")