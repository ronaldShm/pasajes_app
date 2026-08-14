# Gestor de Pasajes Aereos

Aplicacion de escritorio para **extraer, registrar y exportar informacion de pasajes aereos** desde archivos PDF, EML y MSG. Detecta automaticamente la aerolinea y extrae los datos clave del pasaje.

## Funcionalidades

- **Extraccion automatica** de datos desde PDFs y correos electronicos (.msg, .eml)
- **Deteccion automatica** de aerolinea (LATAM, SKY, JetSMART)
- **Validacion de duplicados** por ticket, reserva o similitud de campos
- **Base de datos SQLite** para almacenamiento persistente
- **Exportacion a Excel** con formato profesional
- **Interfaz grafica** moderna con CustomTkinter
- **Log de actividad** con registro de procesados, duplicados y errores

## Aerolineas Soportadas

| Aerolinea | Fuente | Indicador de deteccion |
|-----------|--------|------------------------|
| LATAM | PDF | `LATAM AIRLINES GROUP`, `AEROLINEA EMISORA LATAM` |
| SKY | PDF | `SKY AIRLINE`, `AEROLINEA EMISORA SKY` |
| JetSMART | MSG | `JetSMART`, emails de `jetsmart.com` |

## Datos Extraidos

Cada registro contiene:

| Campo | Descripcion |
|-------|-------------|
| Fecha Registro | Fecha y hora del procesamiento |
| Aerolinea | LATAM, SKY o JetSMART |
| Pasajeros | Nombres de los pasajeros |
| Cantidad Pasajeros | Numero de pasajeros |
| Ticket | Numero de ticket aereo |
| Reserva | Codigo de reserva (6 caracteres) |
| Fecha Emision | Fecha de emision del pasaje |
| Vuelo | Codigo de vuelo (ej: LA 123) |
| Origen | Codigo IATA de origen |
| Destino | Codigo IATA de destino |
| Fecha Vuelo | Fecha del vuelo |
| Total Pagado | Monto total en CLP |
| Forma Pago | Metodo de pago |
| Archivo Origen | Nombre del archivo procesado |

## Arquitectura

```
pasajes_app/
├── main.py                 # Punto de entrada
├── config.py               # Configuracion central
├── gui/
│   ├── app.py              # Ventana principal
│   ├── home_frame.py       # Panel de procesamiento
│   └── records_frame.py    # Panel de registros
├── core/
│   ├── processor.py        # Procesador principal
│   ├── detector.py         # Detector de aerolinea
│   └── validator.py        # Validador de duplicados
├── extractors/
│   ├── base.py             # Clase base + TicketData
│   ├── latam.py            # Extractor LATAM
│   ├── sky.py              # Extractor SKY
│   └── jetsmart.py         # Extractor JetSMART
├── parsers/
│   ├── pdf_parser.py       # Parser de PDFs
│   └── msg_parser.py       # Parser de correos MSG
├── database/
│   ├── connection.py       # Conexion SQLite (singleton)
│   └── repository.py       # Repositorio CRUD
├── excel/
│   └── exporter.py         # Exportador a Excel
└── utils/
    ├── file_manager.py     # Gestion de archivos
    └── logger.py           # Sistema de logging
```

## Requisitos

- Python 3.10+
- Windows (por las rutas de OneDrive/Documentos)

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/TU_USUARIO/pasajes_app.git
cd pasajes_app

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

```bash
python main.py
```

1. Haz clic en **Seleccionar** para elegir la carpeta con los pasajes
2. Haz clic en **PROCESAR PASAJES** para iniciar la extraccion
3. Los registros se guardan automaticamente en la base de datos
4. El archivo `Pasajes.xlsx` se actualiza con todos los registros
5. Los archivos procesados se mueven a la subcarpeta `Procesados/`

## Dependencias

| Paquete | Version | Uso |
|---------|---------|-----|
| pdfplumber | >=0.10.0 | Extraccion de texto de PDFs |
| openpyxl | >=3.1.0 | Generacion de archivos Excel |
| customtkinter | >=5.2.0 | Interfaz grafica moderna |
| extract-msg | >=0.45.0 | Lectura de correos Outlook (.msg) |
| pillow | >=10.0.0 | Manejo de imagenes |
| pyinstaller | >=6.0.0 | Empaquetado como .exe |

## Estructura de la Base de Datos

```sql
CREATE TABLE pasajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_registro TEXT NOT NULL,
    aerolinea TEXT NOT NULL,
    pasajeros TEXT NOT NULL,
    cantidad_pasajeros INTEGER DEFAULT 1,
    ticket TEXT,
    reserva TEXT,
    fecha_emision TEXT,
    vuelo TEXT,
    origen TEXT,
    destino TEXT,
    fecha_vuelo TEXT,
    total_pagado REAL,
    forma_pago TEXT,
    archivo_origen TEXT NOT NULL,
    estado TEXT DEFAULT 'procesado',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## Licencia

Proyecto privado - Uso interno de ProDrilling.
