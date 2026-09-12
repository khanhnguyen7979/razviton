import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATTERNS = {
    "AWS_SECRET": re.compile(r"AKIA[0-9A-Z]{16}"),
    "PRIVATE_KEY": re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH) PRIVATE KEY-----"),
    "TOKEN": re.compile(r"[A-Za-z0-9_]{20,}\.[A-Za-z0-9_]{10,}\.[A-Za-z0-9_-]{10,}"),
}

issues = []
for path in ROOT.rglob("*"):
    if path.is_file() and path.suffix.lower() in {".py", ".md", ".txt", ".json", ".env", ".yml", ".yaml", ".ini"}:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                issues.append(f"{name}: {path}")

for line in issues:
    print(line)
print(f"SECRETS_FOUND={len(issues)}")
