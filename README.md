# AIPI Cobertura

Pipeline automatizado para consolidar información de cobertura AIPI desde archivos Excel almacenados en OneDrive, transformarla a formato analítico y publicar salidas en formato Parquet y Excel para Power BI.

---

# Arquitectura General

El proyecto utiliza:

- GitHub Actions para automatización
- Microsoft Graph API para integración con OneDrive
- Python + pandas para procesamiento y transformación
- Parquet como formato principal de consumo analítico
- Power BI como herramienta de visualización

---

# Estructura del Repositorio

```txt
aipi-cobertura/
├── app/
│   ├── cobertura.py
│   ├── graph_client.py
│   ├── report_runner.py
│   └── requirements.txt
│
└── .github/
    └── workflows/
        └── workflow.yml
```

---

# Flujo General del Pipeline

1. GitHub Actions ejecuta el workflow automáticamente todos los días.
2. `report_runner.py` descarga desde OneDrive:
   - archivos de `INSTITUCIONAL_8H`
   - archivos de `JARDINES_INTEGRALES`
   - archivo `DICCIONARIO.xlsx`
3. `cobertura.py` consolida, valida y transforma la información.
4. Se generan outputs analíticos:
   - `AIPI_COBERTURA.parquet`
   - `AIPI_COBERTURA.xlsx`
5. Los outputs se cargan nuevamente a OneDrive.

---

# GitHub Actions

## Trigger Manual

```yaml
workflow_dispatch:
```

## Trigger Automático

```yaml
schedule:
  - cron: '0 5 * * *'
```

> El cron `0 5 * * *` corresponde aproximadamente a las 12:00 a. m. hora Colombia (UTC-5).

---

# Workflow Actual

```yaml
name: AIPI Cobertura

on:
  workflow_dispatch:
  schedule:
    - cron: '0 5 * * *'

jobs:
  run:
    runs-on: ubuntu-latest

    env:
      TENANT_ID: ${{ secrets.TENANT_ID }}
      CLIENT_ID: ${{ secrets.CLIENT_ID }}
      CLIENT_SECRET: ${{ secrets.CLIENT_SECRET }}
      ONEDRIVE_USER_ID: ${{ secrets.ONEDRIVE_USER_ID }}
      ONEDRIVE_INPUT_INSTITUCIONAL_8H: ${{ secrets.INPUT_FOLDER_INSTITUCIONAL_8H }}
      ONEDRIVE_INPUT_JARDINES_INTEGRALES: ${{ secrets.INPUT_FOLDER_JARDINES_INTEGRALES }}
      ONEDRIVE_OUTPUT_FOLDER: ${{ secrets.OUTPUT_FOLDER }}
      INPUT_FILE_DICCIONARIO: ${{ secrets.INPUT_FILE_DICCIONARIO }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r app/requirements.txt

      - name: Run process
        run: python app/report_runner.py
```

---

# Secrets Requeridos

| Secret | Descripción |
|---|---|
| `TENANT_ID` | Tenant ID de Microsoft Entra ID |
| `CLIENT_ID` | Application ID del App Registration |
| `CLIENT_SECRET` | Client Secret del App Registration |
| `ONEDRIVE_USER_ID` | Usuario propietario del OneDrive |
| `INPUT_FOLDER_INSTITUCIONAL_8H` | Ruta OneDrive carpeta Institucional 8H |
| `INPUT_FOLDER_JARDINES_INTEGRALES` | Ruta OneDrive carpeta Jardines Integrales |
| `INPUT_FILE_DICCIONARIO` | Ruta OneDrive archivo DICCIONARIO.xlsx |
| `OUTPUT_FOLDER` | Ruta OneDrive donde se cargan outputs |

---

# Rutas OneDrive

## Ruta Correcta del Diccionario

```txt
Data/AIPI/DICCIONARIO.xlsx
```

---

# Estructura Esperada en OneDrive

```txt
Data/
└── AIPI/
    ├── INSTITUCIONAL_8H/
    ├── JARDINES_INTEGRALES/
    ├── DICCIONARIO.xlsx
    └── OUTPUT/
```

---

# Diferencia entre Rutas OneDrive y Rutas Locales

## Correcto

```txt
Data/AIPI/DICCIONARIO.xlsx
```

## Incorrecto

```txt
C:\Users\aleja\OneDrive - FUNDACION ATENCION A LA NIÑEZ\Data\AIPI\DICCIONARIO.xlsx
```

## Incorrecto

```txt
data/AIPI/DICCIONARIO.xlsx
```

> `data/...` es únicamente una carpeta temporal local dentro del runner de GitHub Actions.

---

# Dependencias

Archivo `requirements.txt`:

```txt
pandas
openpyxl
pyarrow
msal
requests
```

---

# Componentes Principales

## graph_client.py

Responsable de:

- autenticación Microsoft Graph
- descarga de archivos
- descarga de carpetas
- carga de outputs
- integración OneDrive

Funciones principales:

- `get_access_token()`
- `download_file()`
- `download_folder_xlsx()`
- `upload_folder()`

---

## report_runner.py

Orquestador principal del pipeline.

Responsable de:

1. descargar inputs
2. descargar diccionario
3. ejecutar transformación
4. cargar outputs

---

## cobertura.py

Motor principal de transformación analítica.

Responsable de:

- validaciones
- consolidación
- transformación formato largo
- enriquecimiento con diccionario
- generación parquet
- generación excel auditoría

---

# Diccionario Centralizado de Sedes

El pipeline utiliza un diccionario centralizado para controlar:

- modalidad
- nombre_sede
- comuna_sede

La llave utilizada es:

```txt
id_sede
```

---

# Estructura Esperada del DICCIONARIO.xlsx

## Hoja requerida

```txt
DICCIONARIO
```

## Columnas obligatorias

```txt
id_sede
nombre_sede
modalidad
comuna_sede
```

---

# Validaciones Implementadas

El pipeline valida:

- existencia de archivos Excel
- formato correcto de nombres de archivo
- columnas requeridas
- existencia de sedes en diccionario
- estructura del diccionario

Las columnas adicionales en archivos fuente son ignoradas.

---

# Convención de Nombres de Archivo

## Institucional 8H

```txt
YYYYMMDD_i8h.xlsx
```

Ejemplo:

```txt
20260526_i8h.xlsx
```

---

## Jardines Integrales

```txt
YYYYMMDD_ji.xlsx
```

Ejemplo:

```txt
20260526_ji.xlsx
```

---

# Outputs Generados

## Parquet

```txt
AIPI_COBERTURA.parquet
```

Output principal para Power BI.

---

## Excel

```txt
AIPI_COBERTURA.xlsx
```

Incluye:

| Hoja | Descripción |
|---|---|
| `AIPI_COBERTURA` | Base analítica larga |
| `AUD_ARCHIVOS` | Auditoría de archivos procesados |

---

# Modelo Analítico

El pipeline transforma la información a formato largo para facilitar:

- análisis temporal
- métricas dinámicas
- visualizaciones Power BI
- medidas DAX
- segmentación por tipo de sala

Métricas generadas:

- cupos
- matriculados
- disponibles

Tipos de sala:

- salas_generales
- salas_cunas

---

# Troubleshooting

## Error: KeyError INPUT_FILE_DICCIONARIO

```txt
KeyError: 'INPUT_FILE_DICCIONARIO'
```

Causa:
El secret existe en GitHub pero no fue agregado al bloque `env` del workflow.

Solución:

```yaml
INPUT_FILE_DICCIONARIO: ${{ secrets.INPUT_FILE_DICCIONARIO }}
```

---

## Error: FileNotFoundError DICCIONARIO.xlsx

```txt
FileNotFoundError: No se encontró el diccionario
```

Causa:
El archivo no fue descargado antes de ejecutar `cobertura.py`.

Verificar:

```python
download_file(
    os.environ["INPUT_FILE_DICCIONARIO"],
    Path("data/AIPI/DICCIONARIO.xlsx"),
)
```

---

## Error: 404 Client Error Not Found

```txt
404 Client Error: Not Found
```

Causa:
La ruta almacenada en el secret no existe para Microsoft Graph.

Verificar que el secret use ruta OneDrive y no ruta local Windows.

Correcto:

```txt
Data/AIPI/DICCIONARIO.xlsx
```

Incorrecto:

```txt
C:\Users\...
```

---

## Error: sedes no encontradas

```txt
Hay id_sede que no existen en el DICCIONARIO.xlsx
```

Causa:
Existen sedes en archivos fuente no registradas en el diccionario.

Solución:
Actualizar `DICCIONARIO.xlsx`.

---

# Decisiones Arquitectónicas

## ¿Por qué GitHub Actions?

- automatización serverless
- ejecución programada
- bajo mantenimiento
- trazabilidad de ejecuciones

---

## ¿Por qué Microsoft Graph?

- integración oficial Microsoft 365
- acceso seguro OneDrive
- automatización institucional

---

## ¿Por qué Parquet?

- mejor rendimiento Power BI
- menor tamaño
- mayor velocidad de lectura
- formato analítico estándar

---

## ¿Por qué diccionario centralizado?

Permite:

- gobernanza de sedes
- estandarización
- evitar inconsistencias
- controlar modalidad y ubicación desde una única fuente

---

# Deuda Técnica / Mejoras Futuras

## Posibles mejoras futuras

- logs estructurados
- alertas automáticas
- retries automáticos Graph API
- control incremental
- validaciones de duplicados
- control de cambios del diccionario
- monitoreo de calidad de datos
- versionamiento outputs
- tests automáticos

---

# Notas Operativas

- No mover carpetas OneDrive sin actualizar secrets.
- No mover `DICCIONARIO.xlsx` sin actualizar `INPUT_FILE_DICCIONARIO`.
- Mantener `id_sede` como llave única.
- El output Parquet es el insumo principal para Power BI.
- Los archivos Excel funcionan como auditoría y validación manual.

---

# Estado Actual del Proyecto

Estado:

```txt
Operativo
```

Características implementadas:

- automatización diaria
- descarga automática OneDrive
- consolidación multi-fuente
- transformación analítica
- integración diccionario sedes
- exportación parquet
- exportación excel auditoría
- carga automática outputs OneDrive
