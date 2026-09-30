"""Stand-in for the ESP32 LED module (tests only)."""


def connect_arduino(port):
    return {"port": port}


def set_LED(value, arduino):
    pass
