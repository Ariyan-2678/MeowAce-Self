import sys

try:
    import socks
    HAS_SOCKS = True
except ImportError:
    HAS_SOCKS = False

try:
    from telethon.network.connection import ConnectionTcpMTProxyIntermediate
    HAS_TELETHON = True
except ImportError:
    HAS_TELETHON = False


def get_proxy_kwargs(cfg: dict) -> dict:
    """
    Parses proxy settings from config dictionary and returns kwargs for Telethon TelegramClient.
    Supported types: 'socks5', 'socks4', 'http', 'https', 'mtproto'.
    """
    if not isinstance(cfg, dict):
        return {}

    p_cfg = cfg.get("proxy")
    if not isinstance(p_cfg, dict) or not p_cfg.get("enabled", False):
        return {}

    p_type = str(p_cfg.get("type", "socks5")).strip().lower()
    host = str(p_cfg.get("host") or p_cfg.get("addr") or "127.0.0.1").strip()
    
    try:
        port = int(p_cfg.get("port", 1080))
    except (ValueError, TypeError):
        print(f"[!] Invalid proxy port: '{p_cfg.get('port')}'. Disabling proxy.")
        return {}

    username = p_cfg.get("username") or None
    password = p_cfg.get("password") or None
    secret = p_cfg.get("secret") or None
    rdns = bool(p_cfg.get("rdns", True))

    if p_type in ("socks5", "socks", "socks4", "http", "https"):
        if not HAS_SOCKS:
            print("[!] Warning: 'PySocks' library is missing! SOCKS/HTTP proxies require PySocks.")
            print("[!] Please run: pip install PySocks")
            return {}

        if p_type in ("socks5", "socks"):
            proxy_type = socks.SOCKS5
            type_str = "SOCKS5"
        elif p_type == "socks4":
            proxy_type = socks.SOCKS4
            type_str = "SOCKS4"
        else:
            proxy_type = socks.HTTP
            type_str = "HTTP"

        auth_str = f" (user: {username})" if username else ""
        print(f"[+] Enabling {type_str} Proxy -> {host}:{port}{auth_str}")
        return {
            "proxy": (proxy_type, host, port, rdns, username, password)
        }

    elif p_type == "mtproto":
        if not HAS_TELETHON:
            print("[!] Error: Telethon library not found when configuring MTProto proxy.")
            return {}

        if not secret:
            print("[!] Warning: MTProto proxy requires a secret! Disabling proxy.")
            return {}

        secret_str = str(secret).strip()
        print(f"[+] Enabling MTProto Proxy -> {host}:{port}")
        return {
            "connection": ConnectionTcpMTProxyIntermediate,
            "proxy": (host, port, secret_str)
        }

    else:
        print(f"[!] Unknown proxy type '{p_type}'. Proxy disabled.")
        return {}
