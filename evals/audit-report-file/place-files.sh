#!/usr/bin/env bash
# Copies the case's files into a git repository with one commit on main, dated 2026-09-01.
# A case's .after-start.sh, if any, runs after that, to make later commits or uncommitted changes.
set -eu
cp -R "$(dirname "$0")/files/." .
after=""
if [ -e .after-start.sh ]; then after="$(mktemp)"; mv .after-start.sh "$after"; fi
git init -q -b main
git config user.name "Eval"
git config user.email "eval@example.com"
git add -A
GIT_COMMITTER_DATE="2026-09-01T12:00:00Z" GIT_AUTHOR_DATE="2026-09-01T12:00:00Z" git commit -q -m "Start"
if [ -n "$after" ]; then sh "$after"; rm "$after"; fi
