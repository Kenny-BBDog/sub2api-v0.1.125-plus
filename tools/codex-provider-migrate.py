#!/usr/bin/env python3
"""Migrate Codex local session provider metadata.

This tool is intentionally conservative:
- dry-run is the default;
- --apply creates a timestamped backup before changing anything;
- only session metadata and Codex state indexes are touched;
- auth.json, config.toml, API keys, and login credentials are never modified.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_FROM_PROVIDER = "openai"
DEFAULT_TO_PROVIDER = "OpenAI"


@dataclass
class SessionChange:
    path: Path
    session_id: str
    provider: str


@dataclass
class SQLiteChange:
    path: Path
    count: int


def default_codex_home() -> Path:
    if os.environ.get("CODEX_HOME"):
        return Path(os.environ["CODEX_HOME"]).expanduser()
    return Path.home() / ".codex"


def iter_session_files(codex_home: Path, include_archived: bool) -> Iterable[Path]:
    roots = [codex_home / "sessions"]
    if include_archived:
        roots.append(codex_home / "archived_sessions")
    for root in roots:
        if not root.exists():
            continue
        yield from sorted(root.rglob("*.jsonl"))


def read_session_meta(path: Path) -> tuple[str, str] | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                if item.get("type") != "session_meta":
                    continue
                payload = item.get("payload") or {}
                session_id = str(payload.get("id") or "")
                provider = str(payload.get("model_provider") or "")
                return session_id, provider
    except (OSError, json.JSONDecodeError) as exc:
        print(f"WARN session scan failed: {path}: {exc}", file=sys.stderr)
    return None


def find_session_changes(codex_home: Path, from_provider: str, include_archived: bool) -> list[SessionChange]:
    changes: list[SessionChange] = []
    for path in iter_session_files(codex_home, include_archived):
        meta = read_session_meta(path)
        if not meta:
            continue
        session_id, provider = meta
        if provider == from_provider:
            changes.append(SessionChange(path=path, session_id=session_id, provider=provider))
    return changes


def migrate_session_file(path: Path, from_provider: str, to_provider: str) -> bool:
    changed = False
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with path.open("r", encoding="utf-8") as src, tmp_path.open("w", encoding="utf-8", newline="\n") as dst:
            for line in src:
                stripped = line.strip()
                if not stripped:
                    dst.write(line)
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    dst.write(line)
                    continue
                if item.get("type") == "session_meta":
                    payload = item.get("payload")
                    if isinstance(payload, dict) and payload.get("model_provider") == from_provider:
                        payload["model_provider"] = to_provider
                        line = json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n"
                        changed = True
                dst.write(line)
        if changed:
            os.replace(tmp_path, path)
        else:
            tmp_path.unlink(missing_ok=True)
        return changed
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise


def iter_state_dbs(codex_home: Path) -> Iterable[Path]:
    yield from sorted(codex_home.glob("state_*.sqlite"))


def find_sqlite_changes(codex_home: Path, from_provider: str) -> list[SQLiteChange]:
    changes: list[SQLiteChange] = []
    for path in iter_state_dbs(codex_home):
        try:
            con = sqlite3.connect(path)
            try:
                has_threads = con.execute(
                    "select 1 from sqlite_master where type='table' and name='threads'"
                ).fetchone()
                if not has_threads:
                    continue
                count = con.execute(
                    "select count(*) from threads where model_provider = ?",
                    (from_provider,),
                ).fetchone()[0]
                if count:
                    changes.append(SQLiteChange(path=path, count=int(count)))
            finally:
                con.close()
        except sqlite3.Error as exc:
            print(f"WARN sqlite scan failed: {path}: {exc}", file=sys.stderr)
    return changes


def migrate_sqlite(path: Path, from_provider: str, to_provider: str) -> int:
    con = sqlite3.connect(path)
    try:
        con.execute("pragma busy_timeout = 5000")
        cur = con.execute(
            "update threads set model_provider = ? where model_provider = ?",
            (to_provider, from_provider),
        )
        con.commit()
        return int(cur.rowcount if cur.rowcount is not None else 0)
    finally:
        con.close()


def backup_targets(codex_home: Path, session_changes: list[SessionChange], sqlite_changes: list[SQLiteChange]) -> Path:
    backup_dir = codex_home / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"codex-provider-migrate-{stamp}.zip"
    targets: list[Path] = []
    targets.extend(change.path for change in session_changes)
    targets.extend(change.path for change in sqlite_changes)
    for db_change in sqlite_changes:
        for suffix in ("-wal", "-shm"):
            sidecar = Path(str(db_change.path) + suffix)
            if sidecar.exists():
                targets.append(sidecar)
    with zipfile.ZipFile(backup_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        seen: set[Path] = set()
        for target in targets:
            resolved = target.resolve()
            if resolved in seen or not target.exists():
                continue
            seen.add(resolved)
            zf.write(target, target.relative_to(codex_home))
    return backup_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate Codex local session metadata from one model_provider to another."
    )
    parser.add_argument("--codex-home", default=str(default_codex_home()), help="Path to the Codex home directory.")
    parser.add_argument("--from-provider", default=DEFAULT_FROM_PROVIDER, help="Provider id to migrate from.")
    parser.add_argument("--to-provider", default=DEFAULT_TO_PROVIDER, help="Provider id to migrate to.")
    parser.add_argument("--include-archived", action="store_true", help="Also scan archived_sessions.")
    parser.add_argument("--apply", action="store_true", help="Apply changes. Without this flag the tool only reports.")
    parser.add_argument("--yes", action="store_true", help="Do not prompt before applying changes.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    codex_home = Path(args.codex_home).expanduser().resolve()
    if not codex_home.exists():
        print(f"ERROR Codex home does not exist: {codex_home}", file=sys.stderr)
        return 2
    if args.from_provider == args.to_provider:
        print("ERROR from-provider and to-provider must be different", file=sys.stderr)
        return 2

    session_changes = find_session_changes(codex_home, args.from_provider, args.include_archived)
    sqlite_changes = find_sqlite_changes(codex_home, args.from_provider)

    print(f"Codex home: {codex_home}")
    print(f"Provider: {args.from_provider} -> {args.to_provider}")
    print(f"Session files to update: {len(session_changes)}")
    print(f"SQLite thread rows to update: {sum(change.count for change in sqlite_changes)}")
    for change in session_changes[:10]:
        print(f"  session {change.session_id} {change.path}")
    if len(session_changes) > 10:
        print(f"  ... {len(session_changes) - 10} more session files")
    for change in sqlite_changes:
        print(f"  sqlite {change.count} rows {change.path}")

    if not session_changes and not sqlite_changes:
        print("Nothing to migrate.")
        return 0
    if not args.apply:
        print("Dry run only. Re-run with --apply to modify files.")
        return 0
    if not args.yes:
        answer = input("Apply migration now? Type YES to continue: ").strip()
        if answer != "YES":
            print("Cancelled.")
            return 1

    backup_path = backup_targets(codex_home, session_changes, sqlite_changes)
    print(f"Backup written: {backup_path}")

    updated_sessions = 0
    for change in session_changes:
        if migrate_session_file(change.path, args.from_provider, args.to_provider):
            updated_sessions += 1
    updated_rows = 0
    for change in sqlite_changes:
        updated_rows += migrate_sqlite(change.path, args.from_provider, args.to_provider)

    print(f"Updated session files: {updated_sessions}")
    print(f"Updated SQLite rows: {updated_rows}")
    print("Restart Codex CLI after migration so it reloads the session index.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
