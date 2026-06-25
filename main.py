"""
main.py
--------

Command‑line entry point for the XNative Recursive Learning project. This
script exposes functionality to fetch posts from X (via ``trending.py``),
summarise the content (via ``summarizer.py``), translate the results
(via ``translator.py``) and update the project board (via ``board.py``).

Users can run this module directly to perform ad‑hoc scrapes and
generate summaries without launching the Streamlit UI. See ``--help``
for usage details.

Example invocations::

    # Fetch the latest 5 posts containing "depremler" and summarise them
    python -m xnative_recursive_learning.main --keyword "depremler" --limit 5 --translate en

    # Add a new task to the project board
    python -m xnative_recursive_learning.main --add-task "Refactor translation module" --description "Implement caching"

The CLI is intentionally minimal; more sophisticated workflows are
available via the Streamlit front-end.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .trending import get_posts
from .summarizer import summarize
from .translator import translate, is_translation_available
from .board import ProjectBoard


def handle_scrape(args: argparse.Namespace) -> None:
    # Fetch posts
    print(f"Fetching up to {args.limit} posts for keyword '{args.keyword}'...")
    posts = get_posts(args.keyword, limit=args.limit, lang=args.lang)
    print(f"Retrieved {len(posts)} posts\n")
    board = ProjectBoard(Path(args.board))

    results: List[dict] = []
    for i, post in enumerate(posts, start=1):
        print(f"Post {i} by @{post.user} on {post.date:%Y-%m-%d %H:%M}")
        print(f"URL: {post.url}")
        print(post.content)
        # Summarise
        summary = summarize(post.content, max_length=args.sum_max, min_length=args.sum_min)
        print("Summary:\n", summary)
        # Translate if requested
        if args.translate and is_translation_available():
            translated = translate(summary, target_lang=args.translate)
            print(f"Translated ({args.translate}):\n", translated)
        else:
            translated = summary
        print("\n---\n")
        results.append({
            "id": post.id,
            "url": post.url,
            "content": post.content,
            "summary": summary,
            "translated": translated,
        })
    # Optionally save results to file
    if args.output:
        Path(args.output).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Saved results to {args.output}")
    # Add to board as a completed task for traceability
    board.add_task(
        title=f"Scrape keyword '{args.keyword}'",
        description=f"Fetched {len(posts)} posts and generated summaries",
        status="done",
    )


def handle_add_task(args: argparse.Namespace) -> None:
    board = ProjectBoard(Path(args.board))
    task = board.add_task(args.title, description=args.description or "", status=args.status or "todo")
    print(f"Added task #{task.id}: {task.title} ({task.status})")


def handle_update_task(args: argparse.Namespace) -> None:
    board = ProjectBoard(Path(args.board))
    task = board.update_task(args.task_id, title=args.title, description=args.description, status=args.status)
    if task:
        print(f"Updated task #{task.id}: {task.title} ({task.status})")
    else:
        print(f"Task #{args.task_id} not found")


def handle_list_tasks(args: argparse.Namespace) -> None:
    board = ProjectBoard(Path(args.board))
    tasks = board.list_tasks(status=args.status)
    if not tasks:
        print("No tasks found")
        return
    for task in tasks:
        print(f"#{task.id} [{task.status}] {task.title}\n{task.description}\n")
    summary = board.summary()
    print("Summary:")
    for status, count in summary.items():
        print(f"  {status}: {count}")


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="XNative Recursive Learning CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Fetch posts and summarise them")
    scrape_parser.add_argument("keyword", help="Search keyword or hashtag (omit language filters)")
    scrape_parser.add_argument("--limit", type=int, default=10, help="Number of posts to retrieve")
    scrape_parser.add_argument("--lang", default="tr", help="ISO 639‑1 language code for tweets")
    scrape_parser.add_argument("--sum-max", type=int, default=150, help="Max tokens for summary")
    scrape_parser.add_argument("--sum-min", type=int, default=40, help="Min tokens for summary")
    scrape_parser.add_argument(
        "--translate",
        default=None,
        help="Target language code for translation (e.g. 'en'); leave blank to disable"
    )
    scrape_parser.add_argument("--output", default=None, help="Write scraped posts to this JSON file")
    scrape_parser.add_argument(
        "--board",
        default="board.json",
        help="Path to the project board JSON file (will be created if missing)",
    )
    scrape_parser.set_defaults(func=handle_scrape)

    # Add task command
    add_parser = subparsers.add_parser("add-task", help="Add a task to the project board")
    add_parser.add_argument("title", help="Short title for the task")
    add_parser.add_argument("--description", default="", help="Longer description")
    add_parser.add_argument("--status", default="todo", help="Initial status: todo, in_progress or done")
    add_parser.add_argument("--board", default="board.json", help="Board file path")
    add_parser.set_defaults(func=handle_add_task)

    # Update task command
    update_parser = subparsers.add_parser("update-task", help="Update an existing task on the board")
    update_parser.add_argument("task_id", type=int, help="ID of the task to update")
    update_parser.add_argument("--title", default=None, help="New title")
    update_parser.add_argument("--description", default=None, help="New description")
    update_parser.add_argument("--status", default=None, help="New status")
    update_parser.add_argument("--board", default="board.json", help="Board file path")
    update_parser.set_defaults(func=handle_update_task)

    # List tasks command
    list_parser = subparsers.add_parser("list-tasks", help="List tasks in the project board")
    list_parser.add_argument("--status", default=None, help="Filter by status")
    list_parser.add_argument("--board", default="board.json", help="Board file path")
    list_parser.set_defaults(func=handle_list_tasks)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
