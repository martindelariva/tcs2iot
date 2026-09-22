#!/usr/bin/env python3
"""Central configuration for TCS2IoT, loaded from an INI config file.

Parameters are read from a config file (default: config.ini next to this
module). An environment variable of the same name, when set, overrides the
value from the file so the existing Docker/compose workflow keeps working.

Resolution order for each key (first match wins):
    1. environment variable
    2. value in the config file
    3. built-in default below

Point the app at a different file with the CONFIG_FILE environment variable.

Usage:
    from config import CONFIG
    CONFIG.iot_endpoint
    CONFIG.get("IOT_TOPIC")
"""
from __future__ import annotations

import configparser
import os
from typing import Optional

_SECTION = "tcs2iot"

# Built-in fallbacks used when a key is absent from both env and file.
_DEFAULTS = {
    "GIS_LAYER": "TETRA",
    "WATCH_FILE": "/data/test-out.txt",
    # Daily-rotating log support: directory to scan and the glob pattern of
    # the rotating files. The "current" file is the newest matching name.
    "WATCH_DIR": "/data",
    "FILE_PATTERN": "DataLog_*.csv",
    "POLL_INTERVAL": "0.25",
    "SOURCE_FILE": "/data/captura-tcs-gps.txt",
    "OUT_FILE": "/data/test-out.txt",
    "INTERVAL": "10.0",
    "IOT_ENDPOINT": "",
    "IOT_TOPIC": "tcs/gps",
    "IOT_CLIENT_ID": f"tcs2iot-{os.getpid()}",
    "IOT_QOS": "1",
    "IOT_CERT_PATH": "/certs/device.pem.crt",
    "IOT_KEY_PATH": "/certs/private.pem.key",
    "IOT_CA_PATH": "/certs/AmazonRootCA1.pem",
}


class Config:
    """Reads settings from an INI file with environment-variable overrides."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or os.getenv(
            "CONFIG_FILE",
            os.path.join(os.path.dirname(__file__), "config.ini"),
        )

        parser = configparser.ConfigParser()
        self._file_values: dict[str, str] = {}
        if os.path.exists(self.path):
            parser.read(self.path)
            if parser.has_section(_SECTION):
                # Keys are stored case-insensitively by configparser; normalize
                # to upper-case to match env-var / default naming.
                self._file_values = {
                    k.upper(): v for k, v in parser.items(_SECTION)
                }
        else:
            print(
                f"[config] file not found at {self.path}; "
                "using environment variables and defaults.",
                flush=True,
            )

    # -- generic access ----------------------------------------------------
    def get(self, key: str, default: Optional[str] = None) -> str:
        """Return the value for `key` (env > file > built-in default)."""
        env = os.getenv(key)
        if env is not None and env.strip() != "":
            return env.strip()
        if key in self._file_values and self._file_values[key].strip() != "":
            return self._file_values[key].strip()
        if default is not None:
            return default
        return _DEFAULTS.get(key, "")

    def get_int(self, key: str) -> int:
        return int(float(self.get(key)))

    # -- typed convenience properties -------------------------------------
    @property
    def gis_layer(self) -> str:
        return self.get("GIS_LAYER")

    @property
    def watch_file(self) -> str:
        return self.get("WATCH_FILE")

    @property
    def watch_dir(self) -> str:
        return self.get("WATCH_DIR")

    @property
    def file_pattern(self) -> str:
        return self.get("FILE_PATTERN")

    @property
    def poll_interval(self) -> float:
        return float(self.get("POLL_INTERVAL"))

    @property
    def source_file(self) -> str:
        return self.get("SOURCE_FILE")

    @property
    def out_file(self) -> str:
        return self.get("OUT_FILE")

    @property
    def interval(self) -> float:
        return float(self.get("INTERVAL"))

    @property
    def iot_endpoint(self) -> str:
        return self.get("IOT_ENDPOINT")

    @property
    def iot_topic(self) -> str:
        return self.get("IOT_TOPIC")

    @property
    def iot_client_id(self) -> str:
        return self.get("IOT_CLIENT_ID")

    @property
    def iot_qos(self) -> int:
        return self.get_int("IOT_QOS")

    @property
    def iot_cert_path(self) -> str:
        return self.get("IOT_CERT_PATH")

    @property
    def iot_key_path(self) -> str:
        return self.get("IOT_KEY_PATH")

    @property
    def iot_ca_path(self) -> str:
        return self.get("IOT_CA_PATH")


# Shared singleton for the application.
CONFIG = Config()


if __name__ == "__main__":
    print(f"[config] loaded from: {CONFIG.path}")
    for key in _DEFAULTS:
        print(f"  {key} = {CONFIG.get(key)!r}")
