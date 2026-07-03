#!/usr/bin/env python3
"""Read-only production gate for portable agent skill folders and .skill archives."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
TRIGGER_RE = re.compile(r"\b(use when|when|用于|适用|触发|reviewing|auditing)\b", re.I)
LOCAL_PATH_RE = re.compile(
    "("
    + "/" + "Users/" + r"[^\\s`'\"<>]+"
    + "|/home/" + r"[^\\s`'\"<>]+"
    + r"|[A-Za-z]:\\\\[^\\s`'\"<>]+"
    + ")"
)
RISK_PATTERNS = (
    "curl " + "| sh",
    "curl -" + "fsSL",
    "rm " + "-rf",
    "chmod " + "777",
    "su" + "do ",
    "TO" + "KEN",
    "SEC" + "RET",
    "PASS" + "WORD",
)
EXTRA_DOCS = {
    "README.md",
    "INSTALLATION_GUIDE.md",
    "QUICK_REFERENCE.md",
    "CHANGELOG.md",
}
EXPECTED_FRONTMATTER = {"name", "description"}


@dataclass(frozen=True)
class Finding:
    level: str
    area: str
    message: str


def suggested_fix(item: Finding) -> str:
    msg = item.message
    if item.level == "PASS":
        return ""
    if "missing SKILL.md" in msg:
        return "Add a SKILL.md file with valid frontmatter and task instructions."
    if "missing name" in msg:
        return "Add `name` to SKILL.md frontmatter and match it to the folder name."
    if "invalid name" in msg:
        return "Rename the folder and frontmatter to lowercase letters, digits, and hyphens only."
    if "does not match folder" in msg:
        return "Make the folder name and frontmatter `name` identical."
    if "description" in msg and ("missing" in msg or "short" in msg or "trigger" in msg):
        return "Rewrite `description` to state what the skill does, when to use it, supported inputs, and exclusions."
    if "TODO" in msg:
        return "Replace placeholder text with final instructions or remove the incomplete section."
    if "SKILL.md is long" in msg:
        return "Move detailed examples or variant-specific guidance into directly linked reference files."
    if "openai.yaml missing" in msg:
        return "Generate `agents/openai.yaml` only when targeting OpenAI-style skill UIs."
    if "default_prompt should mention" in msg:
        return "Update default_prompt so it explicitly mentions the skill name in the target platform's invocation style."
    if "extra documentation file" in msg:
        return "Move essential content into SKILL.md or referenced resources, then delete the duplicate doc."
    if "exists but is empty" in msg:
        return "Delete the empty resource directory or add the resource it is meant to contain."
    if "not mentioned in SKILL.md" in msg:
        return "Reference the resource directory from SKILL.md and say when to use it."
    if "review `" in msg and "for `" in msg:
        return "Inspect the matched content, remove risky commands/secrets, or document the required safety check."
    if "script lacks shebang" in msg:
        return "Add a shebang or executable bit so the script has a clear runnable entrypoint."
    if "python syntax error" in msg:
        return "Fix the reported Python syntax error, then rerun the strict audit."
    if "no obvious CLI/self-test" in msg:
        return "Add a small `__main__` CLI path or `--self-test` check for the script."
    if "hardcoded local path" in msg:
        return "Replace the user-local absolute path with `$HOME`, an environment variable, a parameter, or documented local config."
    if "not a valid zip" in msg or "not a directory" in msg:
        return "Provide a skill folder or a valid `.skill`/`.zip` archive containing one skill root."
    if "does not contain exactly one SKILL.md" in msg:
        return "Repackage the archive so it contains exactly one top-level skill folder with SKILL.md."
    if "macOS metadata" in msg:
        return "Recreate the archive while excluding `__MACOSX` and `.DS_Store` files."
    if "non-standard keys" in msg:
        return "Remove non-standard frontmatter keys; keep only `name` and `description`."
    return "Add evidence or update the skill so this gate can be verified directly."


def finding(level: str, area: str, message: str) -> Finding:
    return Finding(level, area, message)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta


def body_without_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---", 4)
    if end == -1:
        return text
    return text[end + 4 :]


def file_lines(path: Path) -> int:
    try:
        return len(read_text(path).splitlines())
    except OSError:
        return 0


def detect_skill_root(path: Path) -> Path | None:
    if (path / "SKILL.md").exists():
        return path
    candidates = [p.parent for p in path.rglob("SKILL.md") if "__MACOSX" not in p.parts]
    if len(candidates) == 1:
        return candidates[0]
    return None


def unpack_if_needed(path: Path, temp_root: Path) -> tuple[Path | None, list[Finding]]:
    findings: list[Finding] = []
    if path.is_dir():
        return detect_skill_root(path), findings
    if path.suffix != ".skill" and path.suffix != ".zip":
        return None, [finding("FAIL", "installability", "artifact is not a directory, .skill, or .zip")]
    if not zipfile.is_zipfile(path):
        return None, [finding("FAIL", "installability", "package is not a valid zip archive")]

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any(name.startswith("__MACOSX/") or name.endswith(".DS_Store") for name in names):
            findings.append(finding("WARN", "installability", "package contains macOS metadata files"))
        archive.extractall(temp_root)

    root = detect_skill_root(temp_root)
    if root is None:
        findings.append(finding("FAIL", "installability", "package does not contain exactly one SKILL.md root"))
    else:
        findings.append(finding("PASS", "installability", f"package unpacks to `{root.name}`"))
    return root, findings


def check_optional_openai_yaml(path: Path, name: str) -> list[Finding]:
    findings: list[Finding] = []
    openai_yaml = path / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        return []

    text = read_text(openai_yaml)
    findings.append(finding("PASS", "installability", "agents/openai.yaml present"))
    if "display_name:" not in text:
        findings.append(finding("WARN", "convention", "openai.yaml missing display_name"))
    if "short_description:" not in text:
        findings.append(finding("WARN", "convention", "openai.yaml missing short_description"))
    if name not in text:
        findings.append(finding("WARN", "adaptability", f"openai.yaml default_prompt should mention `{name}`"))
    return findings


def check_python_script(path: Path, rel: Path, current_script: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = read_text(path)
    first = text.splitlines()[0] if text.splitlines() else ""
    mode = os.stat(path).st_mode
    if first.startswith("#!") or mode & 0o111:
        findings.append(finding("PASS", "reliability", f"script is runnable or has shebang: {rel}"))
    else:
        findings.append(finding("WARN", "reliability", f"script lacks shebang/executable bit: {rel}"))

    with tempfile.NamedTemporaryFile(suffix=".pyc") as compiled:
        try:
            py_compile.compile(str(path), cfile=compiled.name, doraise=True)
        except py_compile.PyCompileError as exc:
            findings.append(finding("FAIL", "reliability", f"python syntax error in `{rel}`: {exc.msg}"))
        else:
            findings.append(finding("PASS", "reliability", f"python syntax passes: {rel}"))

    if path.resolve() != current_script and "--self-test" not in text and "__main__" not in text:
        findings.append(finding("WARN", "reliability", f"script has no obvious CLI/self-test entrypoint: {rel}"))
    return findings


def audit_folder(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    skill_md = path / "SKILL.md"
    if not skill_md.exists():
        return [finding("FAIL", "layout", "missing SKILL.md")]

    text = read_text(skill_md)
    body = body_without_frontmatter(text)
    meta = read_frontmatter(text)
    name = meta.get("name", "")
    description = meta.get("description", "")

    extra_meta = sorted(set(meta) - EXPECTED_FRONTMATTER)
    if extra_meta:
        findings.append(finding("WARN", "convention", f"frontmatter has non-standard keys: {', '.join(extra_meta)}"))

    if not name:
        findings.append(finding("FAIL", "frontmatter", "missing name"))
    elif not NAME_RE.match(name):
        findings.append(finding("FAIL", "frontmatter", f"invalid name: {name}"))
    elif name != path.name:
        findings.append(finding("WARN", "frontmatter", f"name does not match folder: {name} != {path.name}"))
    else:
        findings.append(finding("PASS", "frontmatter", f"name matches folder: {name}"))

    if not description or "[TODO" in description:
        findings.append(finding("FAIL", "frontmatter", "missing useful description"))
    elif len(description) < 120:
        findings.append(finding("WARN", "frontmatter", "description may be too short for precise production triggering"))
    elif not TRIGGER_RE.search(description):
        findings.append(finding("WARN", "adaptability", "description does not clearly state when to use the skill"))
    else:
        findings.append(finding("PASS", "adaptability", "description includes trigger guidance"))

    if "[TODO" in body or "TODO:" in body:
        findings.append(finding("FAIL", "convention", "SKILL.md still contains TODO placeholders"))

    skill_lines = file_lines(skill_md)
    if skill_lines > 500:
        findings.append(finding("WARN", "convention", f"SKILL.md is long ({skill_lines} lines); split references"))
    else:
        findings.append(finding("PASS", "convention", f"SKILL.md length is manageable ({skill_lines} lines)"))

    findings.extend(check_optional_openai_yaml(path, name))

    for doc in EXTRA_DOCS:
        if (path / doc).exists():
            findings.append(finding("WARN", "convention", f"extra documentation file present: {doc}"))

    for dirname in ("scripts", "references", "assets"):
        d = path / dirname
        if not d.exists():
            continue
        files = [p for p in d.rglob("*") if p.is_file()]
        if not files:
            findings.append(finding("WARN", "convention", f"{dirname}/ exists but is empty"))
        elif dirname not in text:
            findings.append(finding("WARN", "convention", f"{dirname}/ has files but is not mentioned in SKILL.md"))
        else:
            findings.append(finding("PASS", "convention", f"{dirname}/ is present and referenced"))

    current_script = Path(__file__).resolve()
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(path)
        if ".git" in rel.parts or "__pycache__" in rel.parts:
            continue
        content = read_text(item)
        if item.resolve() != current_script:
            for pattern in RISK_PATTERNS:
                if pattern in content:
                    findings.append(finding("WARN", "trust", f"review `{rel}` for `{pattern}`"))
                    break
        if item.suffix == ".py" and item.parent.name == "scripts":
            findings.extend(check_python_script(item, rel, current_script))
        if item.resolve() != current_script and item.suffix in {".md", ".yaml", ".yml", ".py", ".sh", ".js", ".mjs", ".ts"}:
            match = LOCAL_PATH_RE.search(content)
            if match:
                findings.append(finding("WARN", "installability", f"review hardcoded local path in `{rel}`: {match.group(1)}"))

    return findings


def summarize(findings: list[Finding], strict: bool) -> dict[str, object]:
    counts = {"FAIL": 0, "WARN": 0, "PASS": 0}
    for item in findings:
        counts[item.level] = counts.get(item.level, 0) + 1
    blocked = counts.get("FAIL", 0) > 0 or (strict and counts.get("WARN", 0) > 0)
    return {
        "status": "BLOCKED" if blocked else "PASS",
        "strict": strict,
        "counts": counts,
    }


def make_skill(root: Path, name: str, skill_md: str, openai_yaml: str | None = None) -> Path:
    skill = root / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(skill_md, encoding="utf-8")
    if openai_yaml is not None:
        agents = skill / "agents"
        agents.mkdir()
        (agents / "openai.yaml").write_text(openai_yaml, encoding="utf-8")
    return skill


def has_fix_for_problem(findings: list[Finding]) -> bool:
    return all(item.level == "PASS" or suggested_fix(item) for item in findings)


def run_self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="skill-evaluator-self-test-") as temp:
        root = Path(temp)
        good = make_skill(
            root,
            "good-skill",
            """---
name: good-skill
description: Evaluate demo skills with a clear trigger. Use when auditing a demo skill folder, validating package readiness, or checking installability before reuse.
---

# Good Skill

Use this demo skill only for audit self-tests.

## Workflow

1. Inspect the artifact.
2. Report the result.

## scripts

The directory is intentionally absent for this fixture.
""",
        )
        bad = make_skill(
            root,
            "bad-skill",
            """---
name: bad-skill
description: TODO
---

# Bad Skill

[TODO: missing real instructions]
""",
        )
        package = root / "good-skill.skill"
        shutil.make_archive(str(package.with_suffix("")), "zip", root, "good-skill")
        package.with_suffix(".zip").rename(package)

        good_findings = audit_folder(good)
        bad_findings = audit_folder(bad)
        package_root, package_findings = unpack_if_needed(package, root / "unpacked")
        if package_root is not None:
            package_findings.extend(audit_folder(package_root))

        checks = [
            ("good skill passes strict gate", summarize(good_findings, True)["status"] == "PASS"),
            ("bad skill is blocked", summarize(bad_findings, True)["status"] == "BLOCKED"),
            ("bad skill emits fixes", has_fix_for_problem(bad_findings)),
            ("package passes strict gate", summarize(package_findings, True)["status"] == "PASS"),
        ]

    for label, ok in checks:
        print(f"SELFTEST\t{'PASS' if ok else 'FAIL'}\t{label}")
    return 0 if all(ok for _, ok in checks) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a portable agent skill folder or .skill package without executing its code.")
    parser.add_argument("skill_path", nargs="?", help="Path to a skill folder, .skill archive, or .zip archive")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as production gate blockers")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of tab-separated text")
    parser.add_argument("--self-test", action="store_true", help="Run built-in positive, negative, and package gate checks")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    if not args.skill_path:
        parser.error("skill_path is required unless --self-test is used")

    source = Path(args.skill_path).expanduser().resolve()
    with tempfile.TemporaryDirectory(prefix="skill-audit-") as temp:
        root, findings = unpack_if_needed(source, Path(temp))
        if root is None:
            findings = findings or [finding("FAIL", "path", f"missing skill root: {source}")]
        else:
            findings.extend(audit_folder(root))

    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    findings.sort(key=lambda item: (order.get(item.level, 9), item.area, item.message))
    summary = summarize(findings, args.strict)

    if args.json:
        print(json.dumps({
            "summary": summary,
            "findings": [
                {**item.__dict__, "fix": suggested_fix(item)}
                for item in findings
            ],
        }, ensure_ascii=False, indent=2))
    else:
        for item in findings:
            print(f"{item.level}\t{item.area}\t{item.message}")
            fix = suggested_fix(item)
            if fix:
                print(f"FIX\t{item.area}\t{fix}")
        print(f"SUMMARY\tstatus\t{summary['status']}")
        print(f"SUMMARY\tcounts\tFAIL={summary['counts']['FAIL']} WARN={summary['counts']['WARN']} PASS={summary['counts']['PASS']}")

    return 1 if summary["status"] == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
