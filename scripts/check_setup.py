"""
scripts/check_setup.py - パイプラインのセットアップ検証
Python・ffmpeg・フォント・環境変数・API疎通を順番に確認します。

実行:
  python scripts/check_setup.py
  python scripts/check_setup.py --no-api   # APIテストをスキップ
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def check(name: str, ok: bool, detail: str = ""):
    mark = "[OK]" if ok else "[NG]"
    print(f"{mark} {name}" + (f" -- {detail}" if detail else ""))
    return ok


def check_python():
    v = sys.version_info
    return check("Python >= 3.10", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}")


def check_ffmpeg():
    path = shutil.which("ffmpeg")
    if not path:
        return check("ffmpeg installed", False, "not found in PATH")
    try:
        out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        ver = out.stdout.splitlines()[0] if out.stdout else ""
        return check("ffmpeg installed", True, ver)
    except Exception as e:
        return check("ffmpeg installed", False, str(e))


def check_font():
    import config
    p = Path(config.FONT_PATH)
    return check(f"font {p.name}", p.exists(), str(p) if not p.exists() else "")


def check_python_packages():
    required = [
        "anthropic", "dotenv", "requests",
        "googleapiclient", "google.auth",
    ]
    missing = []
    for m in required:
        try:
            __import__(m)
        except ImportError:
            missing.append(m)
    return check(
        f"required packages",
        not missing,
        f"missing: {', '.join(missing)}" if missing else "all OK",
    )


def check_env_vars():
    import config
    ok = True
    for key in ["CLAUDE_API_KEY", "SUNO_API_KEY", "STABILITY_API_KEY"]:
        present = bool(getattr(config, key, ""))
        if not check(f"env {key}", present, "set" if present else "missing"):
            ok = False
    yt = bool(config.YOUTUBE_CREDENTIALS_JSON)
    check("env YOUTUBE_CREDENTIALS_JSON", yt, "set" if yt else "missing (upload will skip)")
    if yt:
        try:
            json.loads(config.YOUTUBE_CREDENTIALS_JSON)
            check("YOUTUBE_CREDENTIALS_JSON is valid JSON", True)
        except Exception as e:
            ok = check("YOUTUBE_CREDENTIALS_JSON is valid JSON", False, str(e))
    return ok


def check_ambient():
    import config
    found = []
    missing = []
    for key, path in config.AMBIENT_FILES.items():
        if path is None:
            continue
        if Path(path).exists():
            found.append(key)
        else:
            missing.append(key)
    ok = len(found) > 0
    return check(
        f"ambient sounds in {config.AMBIENT_DIR}",
        ok,
        f"found: {found}; missing: {missing}",
    )


def check_claude_api():
    import config
    if not config.CLAUDE_API_KEY:
        return check("Claude API ping", False, "no key")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.CLAUDE_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Reply with just OK"}],
        )
        text = msg.content[0].text.strip()
        return check("Claude API ping", True, f"reply: {text[:30]}")
    except Exception as e:
        return check("Claude API ping", False, str(e)[:100])


def check_suno_api():
    import config
    import requests
    if not config.SUNO_API_KEY:
        return check("Suno API reachable", False, "no key")
    try:
        r = requests.get(
            f"{config.SUNO_API_BASE_URL}/api/v1/generate/credit",
            headers={"Authorization": f"Bearer {config.SUNO_API_KEY}"},
            timeout=10,
        )
        return check("Suno API reachable", r.status_code in (200, 401, 403), f"HTTP {r.status_code}")
    except Exception as e:
        return check("Suno API reachable", False, str(e)[:100])


def check_stability_api():
    import config
    import requests
    if not config.STABILITY_API_KEY:
        return check("Stability API reachable", False, "no key")
    try:
        r = requests.get(
            f"{config.STABILITY_API_BASE_URL}/v1/user/account",
            headers={"Authorization": f"Bearer {config.STABILITY_API_KEY}"},
            timeout=10,
        )
        return check("Stability API reachable", r.status_code == 200, f"HTTP {r.status_code}")
    except Exception as e:
        return check("Stability API reachable", False, str(e)[:100])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-api", action="store_true", help="skip live API pings")
    args = parser.parse_args()

    print("=" * 50)
    print("BGM Pipeline Setup Check")
    print("=" * 50)

    results = [
        check_python(),
        check_ffmpeg(),
        check_python_packages(),
        check_font(),
        check_env_vars(),
        check_ambient(),
    ]
    if not args.no_api:
        print("\n-- live API checks (use --no-api to skip) --")
        results += [
            check_claude_api(),
            check_suno_api(),
            check_stability_api(),
        ]

    print("=" * 50)
    if all(results):
        print("All checks passed. Ready to run main.py")
        return 0
    failed = sum(1 for r in results if not r)
    print(f"{failed} check(s) failed. Fix above issues before running main.py")
    return 1


if __name__ == "__main__":
    sys.exit(main())
