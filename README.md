# DataToSQL

Este proyecto contiene un servidor MCP denominado **bbva-catalogo** construido con [FastMCP](https://gofastmcp.com/) que expone un catálogo sintético de productos tecnológicos. El servidor se ejecuta en modo STDIO mediante `fastmcp run fastmcp.json`.

## Herramientas disponibles

- `schema()`: devuelve la estructura del dataset, con tipos de campos y ejemplos de valores.
- `sample(n=5)`: proporciona una muestra de *n* registros del catálogo.
- `fields()`: lista los nombres de campos aceptados y sus alias reconocidos (por ejemplo, "cantidad en stock" → `cantidad_en_stock`, "benificio" → `beneficio`).
- `query_nl(pregunta)`: interpreta consultas en lenguaje natural en español para filtrar, ordenar y agregar datos.

## Tipos de consultas admitidas por `query_nl`

La herramienta de consultas naturales admite combinaciones de filtros, agregaciones y ordenaciones sobre los campos:

- **Filtros por texto**: producto, marca, tipo y modelo se pueden filtrar por coincidencias parciales o exactas, por ejemplo: "tablets de la marca Lumina", "portátiles modelo Pro".
- **Fechas**: `fechacompra` acepta rangos como "desde 2024-01-01", "hasta 2024-12-31", "entre 2024-03-01 y 2024-06-30", así como expresiones relativas "últimos 6 meses" o "este año".
- **Campos numéricos**: `pvp`, `compra`, `beneficio` (alias "benificio") y `cantidad_en_stock` (alias "cantidad en stock") admiten comparadores como "mayor que", "menor que", "al menos", "como máximo".
- **Agregaciones**:
  - Suma de beneficio ante frases como "beneficio total", "ventas totales", "margen total".
  - Media de PVP para expresiones como "pvp medio", "precio promedio".
  - Suma de stock con peticiones tipo "stock total" o "existencias".
  - Conteos agrupados por campos como marca, tipo o producto cuando se usa "por marca", "por tipo", etc.
- **Orden y límite**: reconoce peticiones de ordenamiento, por ejemplo "ordenado desc por beneficio", y extracciones de top N como "top 5 por beneficio" o "los 3 más caros". Los resultados se limitan a 50 filas.

### Ejemplos

- `beneficio total por marca en los últimos 6 meses (top 5)`
- `pvp medio de los portátiles de marca Acme desde 2025-01-01`
- `productos con cantidad en stock menor que 10`
- `tablets de la marca Lumina con modelo que contenga "Pro", ordenado desc por beneficio`
- `ventas totales por tipo este año`

Cada respuesta incluye un resumen de la interpretación, las filas resultantes (hasta 50), métricas agregadas cuando corresponda y el detalle de filtros aplicados.
