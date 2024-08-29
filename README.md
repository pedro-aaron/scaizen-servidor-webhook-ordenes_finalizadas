<!-- seccion -->

# Ejemplo de Servidor Webhook para recibir notificaciones de ordenes finalizadas de SCAIZEN

Se comparte un ejemplo simple de un servidor webhookque es capaz de recibir notificaciones de ordenes finalizadas de SCAIZEN.

El servidor webhook está desarrollado en Python y usa el framework FastAPI.

## instalar dependencias

```bash
pip3 install -r requirements.txt
```

## correr el server

```bash
python3 server_webhook.py
```

## Documentación server

-   http://localhost:8787/docs

## Credenciales de acceso

-   Username: johndoe
-   Password: secret

# Requerimientos para el diseño del servidor webhook

El servidor webhook debe ser diseñado siguiendo los siguientes requerimientos para ser capaz de recibir notificaciones de ordenes finalizadas de SCAIZEN.

## 1. Autenticación

El endpoint para obtener el token de acceso tiene el formato siguiente:

```http
<HOST_SERVIDOR>/token
```

### 1.1 Endpoint para obtener el token de acceso

Suponiendo que el HOST_SERVIDOR es `http://localhost:8787`, el endpoint sería `http://localhost:8787/token`.

### 1.2 Petición para obtener el token de acceso

La petición para obtener el token de acceso debe ser de tipo `POST`. A continuación se muestra un ejemplo de la petición usando CURL:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8787/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=johndoe&password=secret'
```

SCAIZEN enviará en la petición los siguientes headers (como se aprecia en el ejemplo de CURL):

-   Header `Content-Type` con el valor `application/x-www-form-urlencoded`.
-   Header `accept` con el valor `application/json`.

### 1.3 Respuesta de la petición

La respuesta de la petición será un objeto JSON con el token de acceso. Las llaves del objeto son `access_token` y `token_type`. El valor de `access_token` es el token de acceso que se debe enviar en el header `Authorization` de las peticiones al servidor webhook. El valor de `token_type` es el tipo de token, en este caso se espera `bearer`.

A continuación se muestra un ejemplo de la respuesta:

```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzI0OTYzNDI4fQ.cy_G-uOQHMgAUK_yW8vqXSnlRu4Fo7R4NPjzwIT3shU",
    "token_type": "bearer"
}
```

## 2. Webhook de orden finalizada

La URL para recibir la notificación de orden finalizada tiene un formato similar al siguiente:

```http
<HOST_SERVIDOR>/<ENDPOINT>
```

### 2.1 Endpoint para recibir la notificación de orden finalizada

Suponiendo que el HOST_SERVIDOR es `http://localhost:8787` y ENDPOINT es `webhook_scaizen_finalizacion_orden`, la URL sería `http://localhost:8787/webhook_scaizen_finalizacion_orden`.

### 2.2 Recepción del evento de orden finalizada

Una vez que SCAIZEN envíe la notificación de orden finalizada, el servidor webhook debe responder con un código HTTP `200` si la notificación fue recibida exitosamente, de lo contrario, debe responder con un código HTTP `400` u otro correspondiente al error.

SCAIZEN enviará al webhook (mediante POST) la siguiente información de la orden finalizada:

```json
{
    "timestamp": "2024-08-29 20:34:57",
    "id_orden": 124,
    "tipo": "carga",
    "producto": "diesel",
    "volumen_natural": 123.45,
    "volumen_neto": 123.456,
    "densidad": 1.254,
    "temperatura": 28.125,
    "fecha_inicio": "2024-08-29 20:34:57",
    "fecha_fin": "2024-08-29 20:34:57"
}
```

donde:

-   `timestamp` es la fecha y hora en la que se envió la notificación. Formato: YYYY-MM-DD HH:MM:SS
-   `id_orden` es el identificador único de la orden.
-   `tipo` es el tipo de orden. Posibles valores: carga, descarga, reingreso.
-   producto es el producto involucrado en la orden. Posibles valores: diesel, magna, premium.
-   `volumen_natural` es el volumen natural de la operación.
-   `volumen_neto` es el volumen neto de la operación.
-   `densidad` es la densidad del producto.
-   `temperatura` es la temperatura del producto.
-   `fecha_inicio` es la fecha y hora de inicio de la operación. Formato: YYYY-MM-DD HH:MM:SS
-   `fecha_fin` es la fecha y hora de fin de la operación. Formato: YYYY-MM-DD HH:MM:SS

A continuación se muestra un ejemplo de la petición que ejecutará SCAIZEN al servidor webhook usando CURL:

```bash
curl -X 'POST' \
  'http://127.0.0.1:8787/webhook_scaizen_finalizacion_orden' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzI0OTY2NTE3fQ.pH8ExYMUijmiXxVhOIxgbRpAipk7xqJHP1gQP2FwWS0' \
  -H 'Content-Type: application/json' \
  -d '{
  "timestamp": "2024-08-29 20:34:57",
  "id_orden": 124,
  "tipo": "carga",
  "producto": "diesel",
  "volumen_natural": 123.45,
  "volumen_neto": 123.456,
  "densidad": 1.254,
  "temperatura": 28.125,
  "fecha_inicio": "2024-08-29 20:34:57",
  "fecha_fin": "2024-08-29 20:34:57"
}'

```

Es importante que se desarrolle en webhook siguiendo la estructura mostrada en el ejemplo de CURL, de lo contrario no se podrá recibir la notificación de orden finalizada.

SCAIZEN enviará en la petición los siguientes headers (como se aprecia en el ejemplo de CURL):

-   Header `Authorization` con el token de acceso obtenido en el paso anterior.
-   Header `Content-Type` con el valor `application/json`.
-   Header `accept` con el valor `application/json`.

### 2.3 Respuesta de la petición

La respuesta de la petición puede ser un objeto JSON con un mensaje de confirmación. A continuación se muestra un ejemplo de la respuesta:

```json
{
    "status": "success",
    "message": "Orden procesada con éxito."
}
```

No obstante, la respuesta puede variar dependiendo de la implementación del servidor webhook.

SCAIZEN sólo espera un código de respuesta `200` para confirmar que la notificación fue recibida exitosamente.

Si el código de respuesta es diferente a `200`, SCAIZEN considerará que la notificación no fue recibida y volverá a intentar enviarla.

# RESUMEN DE REQUERIMIENTOS

Resumen de los requerimientos para el diseño del servidor webhook:

1. Valor de `<HOST_SERVIDOR>`
2. Valor de `<USERNAME>`
3. Valor de `<ENDPOINT>`
4. Valor de `<PASSWORD>`
5. La url para autenticación debe ser `<HOST_SERVIDOR>/token`
6. Los headers de la petición de autenticación deben ser `Content-Type: application/x-www-form-urlencoded` y `accept: application/json`
7. el body de la petición de autenticación debe ser `username=<USERNAME>&password=<PASSWORD>`
8. La url para enviar la notificación de orden finalizada debe ser `<HOST_SERVIDOR>/<ENDPOINT>`
9. El body de la petición de la notificación de orden finalizada debe ser un objeto JSON con los campos mencionaos en el punto 2.2: `timestamp`, `id_orden`, `tipo`, `producto`, `volumen_natural`, `volumen_neto`, `densidad`, `temperatura`, `fecha_inicio`, `fecha_fin`
10. Los headers de la petición de la notificación de orden finalizada deben ser como los mencionados en el punto 2.2: `Authorization`, `Content-Type`, `accept`
11. La respuesta de la petición de la notificación de orden finalizada debe ser un código de respuesta `200` si la notificación fue recibida exitosamente, de lo contrario, debe responder con un código HTTP `400` u otro correspondiente al error.
