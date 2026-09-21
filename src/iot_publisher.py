#!/usr/bin/env python3
"""Publish JSON payloads to AWS IoT Core over MQTT using X.509 certificates.

Uses the AWS IoT Device SDK for Python v2 (awsiotsdk / awscrt).

Configuration is read from the config file (see config.py / config.ini) so
the same image works across devices/things without code changes. Environment
variables of the same name still override the file values:

    IOT_ENDPOINT      AWS IoT Core ATS endpoint
                      (e.g. xxxxxxxx-ats.iot.us-east-1.amazonaws.com)
    IOT_TOPIC         MQTT topic to publish to (default: tcs/gps)
    IOT_CLIENT_ID     MQTT client id (default: tcs2iot-<pid>)
    IOT_CERT_PATH     Path to the device certificate (PEM)
    IOT_KEY_PATH      Path to the private key (PEM)
    IOT_CA_PATH       Path to the Amazon Root CA (PEM)
    IOT_QOS           0 or 1 (default: 1)

If IOT_ENDPOINT is empty, the publisher runs in "dry-run" mode and simply
prints payloads. This lets you exercise the full pipeline before the Thing
and its certificates exist.
"""
from __future__ import annotations

import os
import sys
import time
from typing import Optional

from config import CONFIG


class Publisher:
    """Thin wrapper around an MQTT connection to AWS IoT Core."""

    def __init__(self) -> None:
        self.endpoint = CONFIG.iot_endpoint
        self.topic = CONFIG.iot_topic
        self.client_id = CONFIG.iot_client_id
        self.cert_path = CONFIG.iot_cert_path
        self.key_path = CONFIG.iot_key_path
        self.ca_path = CONFIG.iot_ca_path
        self.qos_level = CONFIG.iot_qos

        self._connection = None
        self._dry_run = not self.endpoint

    # -- lifecycle ---------------------------------------------------------
    def connect(self) -> None:
        """Establish the MQTT connection (no-op in dry-run mode)."""
        if self._dry_run:
            print(
                "[iot] IOT_ENDPOINT not set -> DRY-RUN mode "
                "(payloads will be printed, not published).",
                flush=True,
            )
            return

        # Imported lazily so dry-run works even without the SDK installed.
        from awscrt import io, mqtt
        from awsiot import mqtt_connection_builder

        for path, label in (
            (self.cert_path, "certificate"),
            (self.key_path, "private key"),
            (self.ca_path, "root CA"),
        ):
            if not os.path.exists(path):
                raise FileNotFoundError(f"missing {label} at {path}")

        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

        self._connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=self.cert_path,
            pri_key_filepath=self.key_path,
            ca_filepath=self.ca_path,
            client_bootstrap=client_bootstrap,
            client_id=self.client_id,
            clean_session=False,
            keep_alive_secs=30,
        )
        self._qos = mqtt.QoS(self.qos_level)

        print(
            f"[iot] connecting to {self.endpoint} as {self.client_id}...",
            flush=True,
        )
        self._connection.connect().result()
        print(f"[iot] connected. publishing to topic '{self.topic}'.", flush=True)

    def publish(self, payload: str) -> None:
        """Publish a JSON string to the configured topic."""
        if self._dry_run:
            print(f"[dry-run] {self.topic} <- {payload}", flush=True)
            return

        self._connection.publish(
            topic=self.topic,
            payload=payload,
            qos=self._qos,
        )
        print(f"[iot] published to {self.topic}", flush=True)

    def disconnect(self) -> None:
        if self._dry_run or self._connection is None:
            return
        try:
            self._connection.disconnect().result()
            print("[iot] disconnected.", flush=True)
        except Exception as exc:  # pragma: no cover - best-effort cleanup
            print(f"[iot] disconnect error: {exc}", flush=True)


if __name__ == "__main__":
    # Simple smoke test: publish one payload.
    pub = Publisher()
    pub.connect()
    pub.publish('{"test":true}')
    time.sleep(0.5)
    pub.disconnect()
