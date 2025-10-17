import datetime
import random
import statistics
import unicodedata
import re
from typing import Dict, List, Optional, Tuple, Any

from fastmcp import FastMCP

BRANDS = [
    "Acme",
    "NovaTech",
    "Orbit",
    "Zenit",
    "Lumina",
    "Kairo",
    "Vertex",
]

PRODUCT_TEMPLATES = [
    {
        "producto": "Portátil",
        "tipos": ["Ultrabook", "Gaming", "Empresarial", "Convertible"],
        "modelos": ["Atlas", "Vector", "Pulse", "Quantum"],
        "base_precio": 1250,
    },
    {
        "producto": "Smartphone",
        "tipos": ["Premium", "Gama media", "Compacto", "Profesional"],
        "modelos": ["Nova", "Sfera", "Aero", "Helix"],
        "base_precio": 780,
    },
    {
        "producto": "Tablet",
        "tipos": ["Profesional", "Educativa", "Creativa", "Compacta"],
        "modelos": ["Canvas", "Studio", "Prime", "Flow"],
        "base_precio": 620,
    },
    {
        "producto": "Monitor",
        "tipos": ["OLED", "Curvo", "IPS", "UltraWide"],
        "modelos": ["Vision", "Spectra", "Orbit", "Crest"],
        "base_precio": 540,
    },
    {
        "producto": "Auriculares",
        "tipos": ["Inalámbrico", "Cancelación activa", "Deportivo", "Studio"],
        "modelos": ["Echo", "Wave", "Pulse", "Sync"],
        "base_precio": 210,
    },
]

FIELD_ALIASES = {
    "cantidad en stock": "cantidad_en_stock",
    "cantidad stock": "cantidad_en_stock",
    "existencias": "cantidad_en_stock",
    "stock": "cantidad_en_stock",
    "inventario": "cantidad_en_stock",
    "benificio": "beneficio",
    "margen": "beneficio",
    "ganancia": "beneficio",
    "ganancias": "beneficio",
    "precio de venta": "pvp",
    "precio venta": "pvp",
    "precio": "pvp",
    "costo": "compra",
    "coste": "compra",
}

NUMERIC_FIELD_SYNONYMS = {
    "pvp": ["pvp", "precio", "precio de venta", "precio final"],
    "compra": ["compra", "costo", "coste"],
    "beneficio": ["beneficio", "benificio", "margen", "ganancia", "ganancias", "ventas"],
    "cantidad_en_stock": ["cantidad_en_stock", "cantidad en stock", "stock", "existencias", "inventario"],
}

GROUPABLE_FIELDS = {
    "marca": "por marca",
    "tipo": "por tipo",
    "producto": "por producto",
    "modelo": "por modelo",
}

TIPO_SYNONYMS = {
    "portatil": ["portatil", "portatiles", "laptop", "notebook"],
    "smartphone": ["smartphone", "movil", "moviles", "celular", "celulares"],
    "tablet": ["tablet", "tablets"],
    "monitor": ["monitor", "monitores"],
    "auriculares": ["auricular", "auriculares", "headset"],
}

AGGREGATION_SYNONYMS = {
    "beneficio": {
        "keywords": ["beneficio total", "margen total", "ventas totales", "beneficio global"],
        "alias": "total_beneficio",
        "type": "sum",
    },
    "pvp": {
        "keywords": ["pvp medio", "pvp promedio", "precio promedio", "precio medio"],
        "alias": "pvp_medio",
        "type": "mean",
    },
    "cantidad_en_stock": {
        "keywords": ["stock total", "existencias totales", "inventario total"],
        "alias": "stock_total",
        "type": "sum",
    },
}

COMPARISON_KEYWORDS = {
    ">=": ["mayor o igual que", "al menos", "como minimo", "minimo", "mayor o igual a"],
    ">": ["mayor que", "mayor a", "mas de", "mas que", "superior a"],
    "<=": ["menor o igual que", "como maximo", "no mas de", "no mas que", "hasta", "a lo sumo", "menor o igual a"],
    "<": ["menor que", "menor a", "menos de", "por debajo de", "inferior a"],
    "=": ["igual a", "exactamente"]
}

STOP_WORDS_FOR_VALUES = [
    " con ",
    " que ",
    " y ",
    " donde ",
    " desde ",
    " hasta ",
    " entre ",
    " top ",
    " orden",
    " mayor",
    " menor",
    " sum",
    " promedi",
    " media",
    " ultimos",
    " ultimo",
]


def generar_datos() -> List[Dict[str, Any]]:
    rng = random.Random(2025)
    today = datetime.date.today()
    registros: List[Dict[str, Any]] = []
    for i in range(50):
        template = rng.choice(PRODUCT_TEMPLATES)
        producto = template["producto"]
        tipo = rng.choice(template["tipos"])
        modelo_base = rng.choice(template["modelos"])
        modelo = f"{modelo_base} {rng.choice(['A', 'B', 'C', 'D', 'E'])}{rng.randint(1, 9)}{rng.choice(['', ' Pro', ' Plus', ' Max'])}".strip()
        marca = rng.choice(BRANDS)
        base_precio = template["base_precio"]
        compra = round(rng.uniform(base_precio * 0.55, base_precio * 0.85), 2)
        pvp = round(rng.uniform(base_precio * 0.9, base_precio * 1.2), 2)
        if pvp < compra:
            pvp = round(compra + rng.uniform(10, 120), 2)
        beneficio = round(pvp - compra, 2)
        fecha_compra = today - datetime.timedelta(days=rng.randint(0, 540))
        cantidad_en_stock = rng.randint(0, 200)
        registros.append(
            {
                "producto": producto,
                "marca": marca,
                "tipo": tipo,
                "modelo": modelo,
                "pvp": float(f"{pvp:.2f}"),
                "compra": float(f"{compra:.2f}"),
                "beneficio": float(f"{beneficio:.2f}"),
                "fechacompra": fecha_compra.isoformat(),
                "cantidad_en_stock": cantidad_en_stock,
            }
        )
    return registros


def normalizar_texto(valor: str) -> str:
    nfkd = unicodedata.normalize("NFKD", valor)
    sin_acentos = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sin_acentos.lower()


def resolver_alias(nombre: str) -> Optional[str]:
    normalizado = normalizar_texto(nombre)
    if normalizado in FIELD_ALIASES:
        return FIELD_ALIASES[normalizado]
    if normalizado in {"producto", "marca", "tipo", "modelo", "pvp", "compra", "beneficio", "fechacompra", "cantidad_en_stock"}:
        return normalizado
    return None


def reemplazar_aliases(texto: str) -> str:
    reemplazos = sorted(FIELD_ALIASES.items(), key=lambda x: len(x[0]), reverse=True)
    resultado = texto
    for alias, real in reemplazos:
        resultado = resultado.replace(alias, real)
    return resultado


def truncar_valor(valor: str) -> str:
    texto = valor.strip(" \t\n\r'\"")
    for stop in STOP_WORDS_FOR_VALUES:
        indice = texto.find(stop)
        if indice != -1:
            texto = texto[:indice]
    return texto.strip(" ,.;:\t\n\r'\"")


def detectar_comparador(fragmento: str) -> Optional[str]:
    for operador, keywords in COMPARISON_KEYWORDS.items():
        for keyword in keywords:
            if keyword in fragmento:
                return operador
    return None


def extraer_valor_numerico(cadena: str) -> Optional[float]:
    numeros = re.findall(r"\d+(?:[\.,]\d+)?", cadena)
    if not numeros:
        return None
    valor = numeros[0].replace(",", ".")
    try:
        return float(valor)
    except ValueError:
        return None


def parsear_filtros_y_agregaciones(pregunta: str) -> Dict[str, Any]:
    texto = normalizar_texto(pregunta)
    texto = reemplazar_aliases(texto)
    resultado = {
        "filters": [],
        "date_range": [None, None],
        "aggregations": {},
        "group_by": [],
        "order_by": None,
        "limit": None,
        "assumed_default": False,
    }

    # Grupo solicitado
    for campo, frase in GROUPABLE_FIELDS.items():
        if frase in texto:
            resultado["group_by"].append(campo)

    # Rango de fechas
    entre = re.search(r"entre\s+(\d{4}-\d{2}-\d{2})\s+y\s+(\d{4}-\d{2}-\d{2})", texto)
    if entre:
        inicio, fin = entre.groups()
        resultado["date_range"] = [inicio, fin]
    else:
        desde = re.search(r"desde\s+(\d{4}-\d{2}-\d{2})", texto)
        hasta = re.search(r"hasta\s+(\d{4}-\d{2}-\d{2})", texto)
        if desde:
            resultado["date_range"][0] = desde.group(1)
        if hasta:
            resultado["date_range"][1] = hasta.group(1)
    ultimos = re.search(r"ultimos?\s+(\d+)\s+meses", texto)
    if ultimos:
        meses = int(ultimos.group(1))
        fecha_fin = datetime.date.today()
        fecha_inicio = fecha_fin - datetime.timedelta(days=meses * 30)
        resultado["date_range"] = [fecha_inicio.isoformat(), fecha_fin.isoformat()]
    if "este ano" in texto:
        hoy = datetime.date.today()
        inicio_ano = datetime.date(hoy.year, 1, 1)
        resultado["date_range"] = [inicio_ano.isoformat(), hoy.isoformat()]

    # Filtros de cadenas explícitos
    patrones_cadena = {
        "marca": [r"marca\s+(?:es\s+|=|igual\s+a\s+|llamada\s+|llamado\s+)?['\"]?([a-z0-9\s\-]+)", r"de\s+marca\s+['\"]?([a-z0-9\s\-]+)"],
        "producto": [r"producto\s+(?:es\s+|=|igual\s+a\s+)?['\"]?([a-z0-9\s\-]+)", r"de\s+producto\s+['\"]?([a-z0-9\s\-]+)"],
        "tipo": [r"tipo\s+(?:es\s+|=|igual\s+a\s+)?['\"]?([a-z0-9\s\-]+)", r"de\s+tipo\s+['\"]?([a-z0-9\s\-]+)"],
        "modelo": [r"modelo\s+(?:es\s+|=|igual\s+a\s+|llamado\s+)?['\"]?([a-z0-9\s\-]+)", r"modelo\s+que\s+contenga\s+['\"]?([a-z0-9\s\-]+)"]
    }
    for campo, patrones in patrones_cadena.items():
        for patron in patrones:
            for coincidencia in re.finditer(patron, texto):
                valor = truncar_valor(coincidencia.group(1))
                if valor:
                    resultado["filters"].append({"field": campo, "type": "contains", "value": valor})

    # Reconocer palabras clave de tipos
    for tipo_base, sinonimos in TIPO_SYNONYMS.items():
        for sinonimo in sinonimos:
            if re.search(rf"\b{re.escape(sinonimo)}\b", texto):
                resultado["filters"].append({"field": "producto", "type": "contains", "value": tipo_base})
                break

    # Filtros numéricos
    for campo, sinonimos in NUMERIC_FIELD_SYNONYMS.items():
        for sinonimo in sinonimos:
            for coincidencia in re.finditer(rf"{re.escape(sinonimo)}\s+([a-z\s]+)?(\d+(?:[\.,]\d+)?)", texto):
                fragmento = coincidencia.group(0)
                comparador = detectar_comparador(fragmento)
                if not comparador:
                    continue
                valor = extraer_valor_numerico(fragmento)
                if valor is None:
                    continue
                resultado["filters"].append({"field": resolver_alias(campo) or campo, "type": comparador, "value": valor})
    # Filtros numéricos con expresiones "al menos X" sin repetir campo
    for campo, sinonimos in NUMERIC_FIELD_SYNONYMS.items():
        for sinonimo in sinonimos:
            for coincidencia in re.finditer(rf"{re.escape(sinonimo)}\s+(al menos|como minimo|minimo)\s+(\d+(?:[\.,]\d+)?)", texto):
                valor = float(coincidencia.group(2).replace(",", "."))
                resultado["filters"].append({"field": resolver_alias(campo) or campo, "type": ">=", "value": valor})

    # Agregaciones
    for campo, datos in AGGREGATION_SYNONYMS.items():
        for keyword in datos["keywords"]:
            if keyword in texto:
                resultado["aggregations"][campo] = {"type": datos["type"], "alias": datos["alias"]}
                break

    if resultado["group_by"] and "count" not in resultado["aggregations"]:
        resultado["aggregations"]["count"] = {"type": "count", "alias": "conteo"}

    # Orden y limite
    limite = re.search(r"top\s+(\d+)", texto)
    if limite:
        resultado["limit"] = int(limite.group(1))
    else:
        primeros = re.search(r"primeros?\s+(\d+)", texto)
        if primeros:
            resultado["limit"] = int(primeros.group(1))
    orden = re.search(r"ordenad[oa]s?\s+(ascendente|descendente|asc|desc)?\s*por\s+([a-z_\s]+)", texto)
    if orden:
        direccion_texto = orden.group(1) or "asc"
        direccion = "desc" if direccion_texto.startswith("desc") else "asc"
        campo_orden = truncar_valor(orden.group(2)).replace(" ", "_")
        canonico = resolver_alias(campo_orden) or campo_orden
        resultado["order_by"] = {"field": canonico, "direction": direccion}
    elif resultado["limit"] and "por" in texto:
        match = re.search(r"por\s+([a-z_\s]+)$", texto)
        if match:
            campo_orden = truncar_valor(match.group(1)).replace(" ", "_")
            canonico = resolver_alias(campo_orden) or campo_orden
            resultado["order_by"] = {"field": canonico, "direction": "desc"}

    if resultado["order_by"] and resultado["aggregations"]:
        campo = resultado["order_by"]["field"]
        if campo in resultado["aggregations"]:
            resultado["order_by"]["field"] = resultado["aggregations"][campo]["alias"]

    if resultado["group_by"] and resultado["limit"] and not resultado["order_by"]:
        for prioridad in ["beneficio", "pvp", "cantidad_en_stock", "count"]:
            if prioridad in resultado["aggregations"]:
                alias = resultado["aggregations"][prioridad]["alias"] if prioridad != "count" else resultado["aggregations"]["count"]["alias"]
                resultado["order_by"] = {"field": alias, "direction": "desc"}
                break

    if not resultado["filters"] and not resultado["aggregations"] and not resultado["group_by"]:
        resultado["order_by"] = {"field": "beneficio", "direction": "desc"}
        resultado["limit"] = 10
        resultado["assumed_default"] = True

    return resultado


def aplicar_filtros(filas: List[Dict[str, Any]], filtros: List[Dict[str, Any]], rango_fechas: List[Optional[str]]) -> List[Dict[str, Any]]:
    resultado = []
    inicio = datetime.date.fromisoformat(rango_fechas[0]) if rango_fechas[0] else None
    fin = datetime.date.fromisoformat(rango_fechas[1]) if rango_fechas[1] else None

    for fila in filas:
        coincide = True
        for filtro in filtros:
            campo = filtro["field"]
            if campo not in fila:
                continue
            valor_fila = fila[campo]
            tipo_filtro = filtro["type"]
            valor = filtro["value"]
            if tipo_filtro == "contains":
                valor_norm = normalizar_texto(str(valor))
                fila_norm = normalizar_texto(str(valor_fila))
                if valor_norm not in fila_norm:
                    coincide = False
                    break
            elif tipo_filtro in {">", ">=", "<", "<=", "="}:
                try:
                    valor_num = float(valor_fila)
                except (TypeError, ValueError):
                    coincide = False
                    break
                if tipo_filtro == ">" and not (valor_num > valor):
                    coincide = False
                    break
                if tipo_filtro == ">=" and not (valor_num >= valor):
                    coincide = False
                    break
                if tipo_filtro == "<" and not (valor_num < valor):
                    coincide = False
                    break
                if tipo_filtro == "<=" and not (valor_num <= valor):
                    coincide = False
                    break
                if tipo_filtro == "=" and not (valor_num == valor):
                    coincide = False
                    break
        if not coincide:
            continue
        fecha_compra = datetime.date.fromisoformat(fila["fechacompra"])
        if inicio and fecha_compra < inicio:
            continue
        if fin and fecha_compra > fin:
            continue
        resultado.append(fila)
    return resultado


def agrupar_y_agregar(filas: List[Dict[str, Any]], group_by: List[str], agregaciones: Dict[str, Dict[str, str]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    agrupados: Dict[Tuple[Any, ...], Dict[str, Any]] = {}
    for fila in filas:
        clave = tuple(fila[campo] for campo in group_by)
        if clave not in agrupados:
            agrupados[clave] = {
                "conteo": 0,
                "sumas": {},
            }
        agrupados[clave]["conteo"] += 1
        for campo, info in agregaciones.items():
            if campo == "count":
                continue
            if info["type"] == "sum" or info["type"] == "mean":
                agrupados[clave]["sumas"].setdefault(campo, 0.0)
                agrupados[clave]["sumas"][campo] += float(fila[campo])
    resultados: List[Dict[str, Any]] = []
    for clave, datos in agrupados.items():
        registro = {campo: valor for campo, valor in zip(group_by, clave)}
        if "count" in agregaciones:
            registro[agregaciones["count"]["alias"]] = datos["conteo"]
        for campo, info in agregaciones.items():
            if campo == "count":
                continue
            alias = info["alias"]
            if info["type"] == "sum":
                valor = round(datos["sumas"].get(campo, 0.0), 2)
                registro[alias] = float(f"{valor:.2f}")
            elif info["type"] == "mean":
                count = datos["conteo"]
                valor = round(datos["sumas"].get(campo, 0.0) / count, 2) if count else 0.0
                registro[alias] = float(f"{valor:.2f}")
        resultados.append(registro)

    metrics: Dict[str, Any] = {}
    if "count" in agregaciones:
        metrics[agregaciones["count"]["alias"]] = sum(datos["conteo"] for datos in agrupados.values())
    for campo, info in agregaciones.items():
        if campo == "count":
            continue
        alias = info["alias"]
        if info["type"] == "sum":
            total = sum(datos["sumas"].get(campo, 0.0) for datos in agrupados.values())
            metrics[alias] = float(f"{round(total, 2):.2f}")
        elif info["type"] == "mean":
            valores = []
            for datos in agrupados.values():
                count = datos["conteo"]
                if count:
                    valores.append(datos["sumas"].get(campo, 0.0) / count)
            if valores:
                metrics[alias] = float(f"{round(statistics.mean(valores), 2):.2f}")
    return resultados, metrics


def aplicar_orden_y_limite(rows: List[Dict[str, Any]], orden: Optional[Dict[str, str]], limite: Optional[int]) -> List[Dict[str, Any]]:
    resultado = rows
    if orden and rows:
        campo = orden["field"]
        direccion = orden["direction"]
        if campo not in rows[0]:
            campo_alias = None
            for value in rows[0].keys():
                if normalizar_texto(value) == campo:
                    campo_alias = value
                    break
            if campo_alias:
                campo = campo_alias
        resultado = sorted(
            resultado,
            key=lambda r: r.get(campo, 0),
            reverse=direccion == "desc",
        )
    if limite is not None:
        resultado = resultado[:limite]
    return resultado[:50]


def construir_summary(contexto: Dict[str, Any], filtros: List[Dict[str, Any]], total_filas: int) -> str:
    partes = []
    if contexto["aggregations"]:
        descripciones = []
        for campo, info in contexto["aggregations"].items():
            if campo == "count":
                descripciones.append("conteo de registros")
            elif info["type"] == "sum":
                descripciones.append(f"suma de {campo}")
            elif info["type"] == "mean":
                descripciones.append(f"promedio de {campo}")
        if descripciones:
            partes.append("Se calcularon " + ", ".join(descripciones))
    if contexto["group_by"]:
        partes.append("agrupado por " + ", ".join(contexto["group_by"]))
    if filtros:
        descripcion_filtros = []
        for filtro in filtros:
            campo = filtro["field"]
            if filtro["type"] == "contains":
                descripcion_filtros.append(f"{campo} contiene '{filtro['value']}'")
            elif filtro["type"] in {">", ">=", "<", "<=", "="}:
                descripcion_filtros.append(f"{campo} {filtro['type']} {filtro['value']}")
        if descripcion_filtros:
            partes.append("con filtros: " + ", ".join(descripcion_filtros))
    if contexto["assumed_default"]:
        partes.append("Interpretación por defecto: top 10 por beneficio")
    if not partes:
        partes.append(f"Se muestran {total_filas} registros filtrados del catálogo")
    return ". ".join(partes)


DATASET = generar_datos()

mcp = FastMCP("catalogo")


@mcp.tool()
def schema() -> Dict[str, Any]:
    """Devuelve el esquema del dataset con ejemplos."""
    ejemplo = DATASET[0]
    campos = {}
    for campo, valor in ejemplo.items():
        campos[campo] = {
            "type": type(valor).__name__,
            "example": valor,
        }
    return {"schema": campos}


@mcp.tool()
def sample(n: int = 5) -> List[Dict[str, Any]]:
    """Devuelve una muestra de n filas del dataset."""
    n = max(1, min(int(n), len(DATASET)))
    return DATASET[:n]


@mcp.tool()
def fields() -> Dict[str, Any]:
    """Lista los campos y alias aceptados."""
    return {
        "fields": [
            "producto",
            "marca",
            "tipo",
            "modelo",
            "pvp",
            "compra",
            "beneficio",
            "fechacompra",
            "cantidad_en_stock",
        ],
        "aliases": FIELD_ALIASES,
    }


@mcp.tool()
def query_nl(pregunta: str) -> Dict[str, Any]:
    """Interpreta una consulta en lenguaje natural y devuelve resultados."""
    contexto = parsear_filtros_y_agregaciones(pregunta)
    filas_filtradas = aplicar_filtros(DATASET, contexto["filters"], contexto["date_range"])

    metrics: Dict[str, Any] = {}
    rows: List[Dict[str, Any]]

    if contexto["group_by"]:
        filas_agrupadas, metrics = agrupar_y_agregar(filas_filtradas, contexto["group_by"], contexto["aggregations"])
        filas_agrupadas = aplicar_orden_y_limite(filas_agrupadas, contexto["order_by"], contexto["limit"])
        rows = filas_agrupadas
    else:
        if contexto["aggregations"]:
            for campo, info in contexto["aggregations"].items():
                if campo == "count":
                    metrics[info["alias"]] = len(filas_filtradas)
                elif info["type"] == "sum":
                    total = round(sum(float(fila[campo]) for fila in filas_filtradas), 2)
                    metrics[info["alias"]] = float(f"{total:.2f}")
                elif info["type"] == "mean":
                    valores = [float(fila[campo]) for fila in filas_filtradas]
                    if valores:
                        promedio = round(statistics.mean(valores), 2)
                        metrics[info["alias"]] = float(f"{promedio:.2f}")
                    else:
                        metrics[info["alias"]] = 0.0
        filas_ordenadas = aplicar_orden_y_limite(filas_filtradas, contexto["order_by"], contexto["limit"])
        rows = filas_ordenadas

    applied_filters = {}
    for filtro in contexto["filters"]:
        campo = filtro["field"]
        descripcion = filtro["value"] if filtro["type"] == "contains" else f"{filtro['type']} {filtro['value']}"
        applied_filters.setdefault(campo, []).append(descripcion)

    summary = construir_summary(contexto, contexto["filters"], len(rows))

    return {
        "summary": summary,
        "rows": rows[:50],
        "metrics": metrics,
        "applied_filters": applied_filters,
    }


if __name__ == "__main__":
    mcp.run()
