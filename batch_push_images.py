#!/usr/bin/env python3
"""
FAAM batch uploader
===================
Copies optimized images from a staging folder into a local clone of the FAAM
repository, then commits and pushes them in batches that stay safely below
GitHub's 2 GB-per-push limit.

    staging/{score-id}/{file}.jpg
        -->  <repo>/data/faam/assets/scores/{score-id}/{file}.jpg

Properties
  * Batches always contain whole scores (a score folder is never split).
  * Resumable: finished scores are recorded in a JSON state file, and
    commits that were made but not pushed are pushed first on restart.
  * Push failures are retried with back-off; the script then stops cleanly.
  * `--verify` checks that every staged image is tracked in the repo with
    the same size.

Examples
  python batch_push_images.py --staging ../data --repo ../faam-new --dry-run
  python batch_push_images.py --staging ../data --repo ../faam-new --max-batches 1
  python batch_push_images.py --staging ../data --repo ../faam-new
  python batch_push_images.py --staging ../data --repo ../faam-new --verify
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

GB = 1024 ** 3
IMAGE_EXTS = {".jpg", ".jpeg"}
HARD_PUSH_LIMIT_GB = 1.8   # GitHub rejects pushes larger than 2 GiB


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def git(repo: Path, *args: str, check: bool = True, capture: bool = True):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=check, text=True, capture_output=capture,
    )


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


def list_images(score_dir: Path) -> list[Path]:
    return sorted(
        p for p in score_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def load_state(path: Path) -> set[str]:
    if path.exists():
        return set(json.loads(path.read_text(encoding="utf-8")).get("done", []))
    return set()


def save_state(path: Path, done: set[str]) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"done": sorted(done)}, indent=1), encoding="utf-8")
    tmp.replace(path)


def plan_batches(scores: list[tuple[str, int]], batch_bytes: int):
    """Greedy grouping of (score_id, size) into batches <= batch_bytes."""
    batches, current, size = [], [], 0
    for sid, sz in scores:
        if current and size + sz > batch_bytes:
            batches.append((current, size))
            current, size = [], 0
        current.append(sid)
        size += sz
    if current:
        batches.append((current, size))
    return batches


def push_with_retry(repo: Path, remote: str, branch: str, retries: int = 3) -> bool:
    wait = 30
    for attempt in range(1, retries + 1):
        print(f"    pushing (attempt {attempt}/{retries})...", flush=True)
        # no capture: let git show its own progress bar
        rc = subprocess.run(["git", "-C", str(repo), "push", "-u", remote, branch]).returncode
        if rc == 0:
            return True
        if attempt < retries:
            print(f"    push failed, retrying in {wait}s", flush=True)
            time.sleep(wait)
            wait *= 2
    return False


def unpushed_commits(repo: Path, remote: str, branch: str) -> int:
    r = git(repo, "rev-list", "--count", f"{remote}/{branch}..HEAD", check=False)
    if r.returncode != 0:      # remote branch does not exist yet
        r = git(repo, "rev-list", "--count", "HEAD", check=False)
    try:
        return int(r.stdout.strip())
    except ValueError:
        return 0


# --------------------------------------------------------------------------- #
# Verify mode
# --------------------------------------------------------------------------- #
def verify(staging: Path, repo: Path, dest: Path) -> int:
    tracked = set(git(repo, "ls-files", "--", dest.as_posix()).stdout.splitlines())
    missing, wrong_size, total = [], [], 0
    for score_dir in sorted(p for p in staging.iterdir() if p.is_dir()):
        for img in list_images(score_dir):
            total += 1
            rel = dest / score_dir.name / img.relative_to(score_dir)
            if rel.as_posix() not in tracked:
                missing.append(rel.as_posix())
                continue
            target = repo / rel
            if not target.exists() or target.stat().st_size != img.stat().st_size:
                wrong_size.append(rel.as_posix())
    print(f"Checked {total} staged images.")
    print(f"  not tracked in repo : {len(missing)}")
    print(f"  size mismatch       : {len(wrong_size)}")
    for m in (missing + wrong_size)[:20]:
        print("   -", m)
    return 0 if not missing and not wrong_size else 1


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="Batch-commit and push images to GitHub.")
    ap.add_argument("--staging", required=True, help="Folder with {score-id}/*.jpg")
    ap.add_argument("--repo", required=True, help="Local clone of the FAAM repo")
    ap.add_argument("--dest", default="data/faam/assets/scores",
                    help="Destination inside the repo (default data/faam/assets/scores)")
    ap.add_argument("--batch-gb", type=float, default=1.0,
                    help="Target size per commit/push in GB (default 1.0, max 1.8)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="main")
    ap.add_argument("--state", default="batch_state.json",
                    help="JSON file remembering finished scores")
    ap.add_argument("--pause", type=int, default=60,
                    help="Seconds to wait between pushes (default 60)")
    ap.add_argument("--max-batches", type=int, default=0,
                    help="Stop after this many batches (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Show the plan only")
    ap.add_argument("--verify", action="store_true",
                    help="Check staged images against the repo and exit")
    args = ap.parse_args()

    staging, repo, dest = Path(args.staging), Path(args.repo), Path(args.dest)
    state_path = Path(args.state)

    if not staging.is_dir():
        sys.exit(f"Staging folder not found: {staging}")
    if not (repo / ".git").exists():
        sys.exit(f"Not a git repository: {repo}")
    if args.batch_gb > HARD_PUSH_LIMIT_GB:
        sys.exit(f"--batch-gb must be <= {HARD_PUSH_LIMIT_GB} (GitHub limit is 2 GiB per push)")

    if args.verify:
        return verify(staging, repo, dest)

    # Safety: no staged or modified tracked files (untracked files are fine)
    dirty = (git(repo, "diff", "--quiet", check=False).returncode != 0
             or git(repo, "diff", "--cached", "--quiet", check=False).returncode != 0)
    if dirty:
        sys.exit("Repo has uncommitted changes to tracked files. Commit or stash them first.")

    current_branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if current_branch != args.branch:
        sys.exit(f"Repo is on branch '{current_branch}', expected '{args.branch}'.")

    # Push anything committed earlier but never pushed
    if not args.dry_run and unpushed_commits(repo, args.remote, args.branch) > 0:
        print("Found unpushed commits from an earlier run; pushing them first.")
        if not push_with_retry(repo, args.remote, args.branch):
            sys.exit("Could not push the pending commits. Fix connectivity and re-run.")

    done = load_state(state_path)
    scores = []
    for score_dir in sorted(p for p in staging.iterdir() if p.is_dir()):
        if score_dir.name in done:
            continue
        imgs = list_images(score_dir)
        if imgs:
            scores.append((score_dir.name, sum(i.stat().st_size for i in imgs)))

    batches = plan_batches(scores, int(args.batch_gb * GB))
    total_bytes = sum(s for _, s in scores)
    print(f"{len(scores)} scores left ({human(total_bytes)}), "
          f"{len(done)} already done -> {len(batches)} batches of ~{args.batch_gb} GB")

    if args.dry_run:
        for i, (ids, sz) in enumerate(batches[:10], 1):
            print(f"  batch {i:03d}: {len(ids)} scores, {human(sz)}  [{ids[0]} ... {ids[-1]}]")
        if len(batches) > 10:
            print(f"  ... and {len(batches) - 10} more")
        return 0

    for i, (ids, sz) in enumerate(batches, 1):
        if args.max_batches and i > args.max_batches:
            print("Reached --max-batches, stopping.")
            break
        print(f"\n[batch {i}/{len(batches)}] {len(ids)} scores, {human(sz)} "
              f"({ids[0]} ... {ids[-1]})", flush=True)

        # 1. copy
        n_files = 0
        for sid in ids:
            src_dir = staging / sid
            for img in list_images(src_dir):
                target = repo / dest / sid / img.relative_to(src_dir)
                if target.exists() and target.stat().st_size == img.stat().st_size:
                    n_files += 1
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img, target)
                n_files += 1
        print(f"    copied {n_files} files")

        # 2. add + commit
        paths = [(dest / sid).as_posix() for sid in ids]
        git(repo, "add", "--", *paths)
        if git(repo, "diff", "--cached", "--quiet", check=False).returncode != 0:
            msg = (f"Add scores batch {len(done) + 1}-{len(done) + len(ids)}: "
                   f"{ids[0]} .. {ids[-1]} ({n_files} images, {human(sz)})")
            git(repo, "commit", "-m", msg)
            print("    committed")
        else:
            print("    nothing new to commit (already in repo)")

        # 3. push
        if not push_with_retry(repo, args.remote, args.branch):
            print("\nPush failed. Nothing is lost: fix the problem and re-run the "
                  "same command; the script will resume.", file=sys.stderr)
            return 1

        # 4. remember
        done.update(ids)
        save_state(state_path, done)
        print(f"    done. Total finished scores: {len(done)}", flush=True)

        if i < len(batches):
            time.sleep(args.pause)

    print("\nFinished. Run with --verify to check the result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
