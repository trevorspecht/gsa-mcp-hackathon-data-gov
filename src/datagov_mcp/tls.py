"""TLS verification against the operating-system trust store."""

import ssl

import truststore


def verified_context() -> ssl.SSLContext:
    # OS trust includes managed enterprise roots (e.g. TLS-inspecting proxies);
    # verification stays enabled, unlike disabling checks.
    return truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
