# TCS2IoT — Overview del proceso

Breve descripción del flujo end-to-end: cómo se obtiene el dato, cómo se arma el documento y cómo se publica en AWS IoT Core.

## Secuencia

1. **Obtención del dato**
   Un proceso Python monitorea el archivo de log de captura TCS-GPS y toma cada nueva línea que se agrega al final del archivo.

2. **Creación del documento**
   Cada línea se decodifica y se transforma en un documento JSON con los campos de la captura (fecha, identificador, mensaje y coordenadas).

3. **Publicación en IoT Core**
   El documento JSON se publica mediante MQTT sobre TLS (autenticación mutua con certificados X.509) al broker de AWS IoT Core, en el topic configurado.

## Diagrama

El detalle visual del flujo está en [`tcs2iot-pipeline.drawio`](./tcs2iot-pipeline.drawio).
