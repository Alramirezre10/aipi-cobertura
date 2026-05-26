# AIPI Cobertura - Automatización GitHub Actions

Este repositorio ejecuta diariamente el proceso de cobertura AIPI y genera:

- `output/AIPI_COBERTURA.parquet`
- `output/AIPI_COBERTURA.xlsx`

## Estructura esperada

```text
.
├── cobertura.py
├── requirements.txt
├── data/
│   ├── INSTITUCIONAL_8h/
│   │   └── 20260521_i8h.xlsx
│   └── JARDINES_INTEGRALES/
│       └── 20260521_ji.xlsx
├── output/
└── .github/
    └── workflows/
        └── aipi_cobertura.yml
```

## Regla de nombres de archivos

Los archivos de entrada deben iniciar con la fecha de corte en formato `AAAAMMDD_`, por ejemplo:

- `20260521_i8h.xlsx`
- `20260521_ji.xlsx`

## Ejecución local

```bash
pip install -r requirements.txt
python cobertura.py
```

## Ejecución automática

El workflow `.github/workflows/aipi_cobertura.yml` está configurado para ejecutarse todos los días a las 5:00 a. m. en zona horaria `America/Bogota`.

También se puede ejecutar manualmente desde GitHub Actions usando `workflow_dispatch`.

## Nota importante

GitHub Actions no puede leer rutas locales como:

```text
C:\Users\aleja\OneDrive - FUNDACION ATENCION A LA NIÑEZ\Data\AIPI
```

Por eso el script usa por defecto carpetas relativas dentro del repositorio:

```text
data/INSTITUCIONAL_8h
data/JARDINES_INTEGRALES
output
```

Si los archivos deben venir desde SharePoint/OneDrive, el siguiente paso recomendado es agregar una etapa previa que descargue los Excel usando Microsoft Graph antes de ejecutar `cobertura.py`.
