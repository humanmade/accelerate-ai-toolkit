#!/usr/bin/env python3
"""Write local connection credentials and run bounded, secret-safe probes."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_CONNECT_TIMEOUT = 5
DEFAULT_MAX_TIME = 15


def atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    """Replace a private file without exposing a partially written secret."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        os.chmod(path, mode)
    except BaseException:
        # Keep a private temporary file for recovery rather than deleting a file
        # that may contain credentials. A successful write always replaces it.
        raise


def quoted_env(value: str) -> str:
    """Encode a value for the POSIX shell env file without executing it."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    escaped = escaped.replace("$", "\\$").replace("`", "\\`")
    return f'"{escaped}"'


def read_credentials() -> tuple[str, str, str]:
    lines = [line.rstrip("\r\n") for line in sys.stdin]
    if len(lines) != 3 or not all(lines):
        raise ValueError("expected exactly three non-empty credential lines on standard input")
    return lines[0], lines[1], lines[2]


def write_credentials(settings_path: Path, env_path: Path) -> None:
    url, username, password = read_credentials()
    settings: dict[str, object] = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"cannot preserve invalid settings file: {settings_path}") from error
        if not isinstance(settings, dict):
            raise ValueError(f"cannot preserve non-object settings file: {settings_path}")

    environment = settings.setdefault("env", {})
    if not isinstance(environment, dict):
        raise ValueError(f"cannot preserve non-object env settings: {settings_path}")
    environment.update(
        {
            "WP_API_URL": url,
            "WP_API_USERNAME": username,
            "WP_API_PASSWORD": password,
            "OAUTH_ENABLED": "false",
        }
    )

    settings_text = json.dumps(settings, indent=2) + "\n"
    env_text = "".join(
        f"{name}={quoted_env(value)}\n"
        for name, value in (
            ("WP_API_URL", url),
            ("WP_API_USERNAME", username),
            ("WP_API_PASSWORD", password),
            ("OAUTH_ENABLED", "false"),
        )
    )
    atomic_write(settings_path, settings_text)
    atomic_write(env_path, env_text)
    print("Credentials saved.")


def read_env_file(env_path: Path) -> dict[str, str]:
    def unquote(value: str) -> str:
        if len(value) < 2 or value[0] != '"' or value[-1] != '"':
            raise ValueError(f"cannot read credential line in {env_path}")
        decoded: list[str] = []
        index = 1
        while index < len(value) - 1:
            if value[index] == "\\" and index + 1 < len(value) - 1:
                following = value[index + 1]
                if following in {'\\', '"', '$', '`'}:
                    decoded.append(following)
                    index += 2
                    continue
            decoded.append(value[index])
            index += 1
        return "".join(decoded)

    values: dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"cannot read credential line in {env_path}")
        name, value = line.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"cannot read credential line in {env_path}")
        values[name] = unquote(value)
    required = ("WP_API_URL", "WP_API_USERNAME", "WP_API_PASSWORD")
    if any(not values.get(name) for name in required):
        raise ValueError(f"missing credentials in {env_path}")
    return values


def toml_quoted(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def configure_codex(config_path: Path, env_path: Path) -> None:
    values = read_env_file(env_path)
    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    without_wordpress = re.sub(
        r"(?ms)^\[mcp_servers\.wordpress(?:\.[^\]]+)?\].*?(?=^\[(?!mcp_servers\.wordpress(?:\.|\]))|\Z)",
        "",
        existing,
    ).rstrip()
    prefix = f"{without_wordpress}\n\n" if without_wordpress else ""
    block = (
        "[mcp_servers.wordpress]\n"
        'command = "npx"\n'
        'args = ["-y", "@automattic/mcp-wordpress-remote@0.4.0"]\n'
        'env = { WP_API_URL = "%s", WP_API_USERNAME = "%s", WP_API_PASSWORD = "%s", OAUTH_ENABLED = "false" }\n'
        % (
            toml_quoted(values["WP_API_URL"]),
            toml_quoted(values["WP_API_USERNAME"]),
            toml_quoted(values["WP_API_PASSWORD"]),
        )
    )
    atomic_write(config_path, prefix + block)
    print("Codex connection saved.")


def curl_quoted(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def request(url: str, username: str | None, password: str | None, connect_timeout: int, max_time: int) -> str:
    config = f'url = "{curl_quoted(url)}"\n'
    if username is not None and password is not None:
        config = f'user = "{curl_quoted(username)}:{curl_quoted(password)}"\n' + config
    completed = subprocess.run(
        [
            "curl",
            "-sS",
            "-o",
            os.devnull,
            "-w",
            "%{http_code}",
            "--connect-timeout",
            str(connect_timeout),
            "--max-time",
            str(max_time),
            "--config",
            "-",
        ],
        input=config,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        return "timeout" if completed.returncode == 28 else "unreachable"
    return completed.stdout.strip() or "unreachable"


def probe(site: str, check: str, connect_timeout: int, max_time: int) -> None:
    parsed = urlparse(site)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("site must be an http or https site root")
    root = site.rstrip("/")
    username = password = None
    if check != "site":
        username = os.environ.get("WP_API_USERNAME")
        password = os.environ.get("WP_API_PASSWORD")
        if not username or not password:
            raise ValueError("WP_API_USERNAME and WP_API_PASSWORD must be set for this probe")

    urls = {
        "site": [("site", f"{root}/wp-json/")],
        "auth": [("auth", f"{root}/wp-json/wp/v2/users/me")],
        "accelerate": [("accelerate", f"{root}/wp-json/accelerate/v1")],
        "routes": [
            ("adapter", f"{root}/wp-json/mcp/mcp-adapter-default-server"),
            ("legacy", f"{root}/wp-json/wp/v2/wpmcp"),
        ],
    }[check]
    results = [
        f"{name}={request(url, username, password, connect_timeout, max_time)}"
        for name, url in urls
    ]
    print(" ".join(results))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    writer = commands.add_parser("write")
    writer.add_argument("--settings", type=Path, required=True)
    writer.add_argument("--env-file", type=Path, required=True)
    codex = commands.add_parser("configure-codex")
    codex.add_argument("--config", type=Path, required=True)
    codex.add_argument("--env-file", type=Path, required=True)
    checker = commands.add_parser("probe")
    checker.add_argument("--site", required=True)
    checker.add_argument("--check", choices=("site", "auth", "accelerate", "routes"), required=True)
    checker.add_argument("--connect-timeout", type=int, default=DEFAULT_CONNECT_TIMEOUT)
    checker.add_argument("--max-time", type=int, default=DEFAULT_MAX_TIME)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "write":
            write_credentials(args.settings, args.env_file)
        elif args.command == "configure-codex":
            configure_codex(args.config, args.env_file)
        else:
            if args.connect_timeout <= 0 or args.max_time <= 0 or args.connect_timeout > args.max_time:
                raise ValueError("timeouts must be positive and connect timeout cannot exceed overall timeout")
            probe(args.site, args.check, args.connect_timeout, args.max_time)
    except (OSError, ValueError) as error:
        print(f"Connection setup failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
