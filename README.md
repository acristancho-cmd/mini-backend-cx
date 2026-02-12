# CX-service

Mini backend FastAPI para obtener ratings y comentarios de App Store y Play Store. Todo hardcodeado: Trii + competidores.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

O bien:

```bash
python main.py
```

## Endpoints (todos GET)

### 1. `GET /trii`

Retorna datos completos de la app **Trii**:
- `rating_global`, `total_votos`, `comentarios_ultimo_mes`
- Play Store + App Store
- Sin parámetros

---

### 2. `GET /ratings/playstore`

Retorna solo ratings de competidores en Play Store (Colombia). Lista hardcodeada: Flink, Hapi, tyba, Fintual, Zesty, Racional.

**Respuesta:**
```json
[
  {"app_name": "Flink", "app_id": "com.miflink.android_app", "rating_global": 3.9, "total_votos": 21600, "store": "playstore"},
  {"app_name": "Hapi", "app_id": "com.hapicorp.imhapi", "rating_global": 4.6, "total_votos": 15500, "store": "playstore"}
]
```

---

### 3. `GET /ratings/appstore`

Retorna solo ratings de competidores en App Store (México). Lista hardcodeada: Flink, Hapi, tyba, Fintual.

**Respuesta:**
```json
[
  {"app_name": "Flink", "app_id": "1303438003", "rating_global": 3.8, "total_votos": 1900, "store": "appstore"},
  {"app_name": "Hapi", "app_id": "1532828502", "rating_global": 4.4, "total_votos": 645, "store": "appstore"}
]
```

## Configuración (config.py)

- **Trii:** Play Store `com.triico.app`, App Store ID `1513826307` país `co`
- **Competidores:** listas hardcodeadas en `PLAYSTORE_COMPETITORS` y `APPSTORE_COMPETITORS`
