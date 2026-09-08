from __future__ import annotations

from io import StringIO
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import connection  # noqa: E402


class ConnectionTests(unittest.TestCase):
    def test_write_preserves_settings_and_locks_both_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = root / ".claude" / "settings.local.json"
            settings.parent.mkdir()
            settings.write_text('{"keep": true, "env": {"OTHER": "value"}}\n', encoding="utf-8")
            captured = StringIO()
            original_stdin = sys.stdin
            try:
                sys.stdin = StringIO(
                    "https://example.test/wp-json/mcp/mcp-adapter-default-server\n"
                    "marketer\n"
                    "secret words\n"
                )
                with redirect_stdout(captured):
                    connection.write_credentials(settings, root / "env")
            finally:
                sys.stdin = original_stdin

            self.assertEqual(settings.stat().st_mode & 0o777, 0o600)
            self.assertEqual((root / "env").stat().st_mode & 0o777, 0o600)
            self.assertIn('"keep": true', settings.read_text(encoding="utf-8"))
            self.assertIn('"OTHER": "value"', settings.read_text(encoding="utf-8"))
            self.assertNotIn("secret words", captured.getvalue())

    def test_env_file_round_trips_quoted_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            settings = root / "settings.local.json"
            env_file = root / "env"
            original_stdin = sys.stdin
            try:
                sys.stdin = StringIO("https://example.test/path\nmarketer\nsecret $value `marker` \\\"quoted\\\"\n")
                with redirect_stdout(StringIO()):
                    connection.write_credentials(settings, env_file)
            finally:
                sys.stdin = original_stdin

            self.assertEqual(connection.read_env_file(env_file)["WP_API_PASSWORD"], 'secret $value `marker` \\"quoted\\"')

    @patch("connection.subprocess.run")
    def test_probe_passes_password_only_through_standard_input(self, run: object) -> None:
        run.return_value = subprocess.CompletedProcess([], 0, stdout="405", stderr="")
        result = connection.request("https://example.test/", "marketer", "secret words", 5, 15)

        self.assertEqual(result, "405")
        command = run.call_args.args[0]
        self.assertNotIn("secret words", command)
        self.assertIn('user = "marketer:secret words"', run.call_args.kwargs["input"])
        self.assertEqual(command[command.index("--connect-timeout") + 1], "5")
        self.assertEqual(command[command.index("--max-time") + 1], "15")

    def test_codex_writer_preserves_other_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            env_file = root / "env"
            env_file.write_text(
                'WP_API_URL="https://example.test/wp-json/mcp/mcp-adapter-default-server"\n'
                'WP_API_USERNAME="marketer"\n'
                'WP_API_PASSWORD="secret words"\n',
                encoding="utf-8",
            )
            config = root / "config.toml"
            config.write_text(
                '[mcp_servers.wordpress]\ncommand = "old"\n\n'
                '[mcp_servers.wordpress.env]\nOLD = "value"\n\n'
                '[mcp_servers.other]\ncommand = "other"\n',
                encoding="utf-8",
            )
            captured = StringIO()
            with redirect_stdout(captured):
                connection.configure_codex(config, env_file)

            content = config.read_text(encoding="utf-8")
            self.assertIn('[mcp_servers.other]', content)
            self.assertNotIn('[mcp_servers.wordpress.env]', content)
            self.assertIn('@automattic/mcp-wordpress-remote@0.4.0', content)
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("secret words", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
