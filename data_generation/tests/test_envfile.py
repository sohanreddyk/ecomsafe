""".env loading. Run: python tests/test_envfile.py"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ecomsafe_datagen.envfile import load_env, parse_env  # noqa: E402
from ecomsafe_datagen.llm import resolve_role  # noqa: E402
from ecomsafe_datagen.pipeline import load_config  # noqa: E402

# key variable of whichever provider single_turn.yaml currently uses for the generator
KEY = resolve_role(load_config(str(ROOT / "config" / "single_turn.yaml"))["generator"]).get("api_key_env")


def test_parse_formats():
    env = parse_env('''
# comment
XAI_API_KEY=xai-abc
export GEMINI_API_KEY="gm 123"
QUOTED='single'
INLINE=value # trailing comment
EMPTY=
not a line
''')
    assert env == {"XAI_API_KEY": "xai-abc", "GEMINI_API_KEY": "gm 123", "QUOTED": "single",
                   "INLINE": "value", "EMPTY": ""}


def test_terminal_export_wins_and_empty_values_ignored():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / ".env"
        p.write_text("T_KEY_A=from_file\nT_KEY_B=from_file\nT_KEY_C=\n")
        os.environ["T_KEY_A"] = "from_terminal"
        os.environ.pop("T_KEY_B", None)
        os.environ.pop("T_KEY_C", None)
        assert load_env(str(p)) == p
        assert os.environ["T_KEY_A"] == "from_terminal"
        assert os.environ["T_KEY_B"] == "from_file"
        assert "T_KEY_C" not in os.environ


def _check(cwd, extra_env, *args):
    env = {k: v for k, v in os.environ.items() if not k.endswith("_API_KEY")}
    env.update(extra_env, PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, "-m", "ecomsafe_datagen.run", "check",
                           "--config", str(ROOT / "config" / "single_turn.yaml"), *args],
                          cwd=str(ROOT), env=env, capture_output=True, text=True)


def test_cli_reads_key_from_dotenv():
    with tempfile.TemporaryDirectory() as d:
        empty = Path(d) / "empty.env"
        empty.write_text("")
        r = _check(d, {}, "--env-file", str(empty))
        assert f"{KEY}=... to .env" in r.stdout and r.returncode == 1, r.stdout
        dotenv = Path(d) / ".env"
        dotenv.write_text(f"{KEY}=secret-from-dotenv\n")
        r = _check(d, {}, "--env-file", str(dotenv))
        assert "[env] loaded keys from" in r.stdout, r.stdout
        assert "generator API key" not in r.stdout, r.stdout
        assert "secret-from-dotenv" not in r.stdout + r.stderr


def test_explicit_env_file_flag():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "keys.env"
        p.write_text(f"{KEY}=secret-explicit\n")
        r = _check(d, {}, "--env-file", str(p))
        assert f"loaded keys from {p}" in r.stdout and "generator API key" not in r.stdout, r.stdout


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)