"""RabbitMQ queue metrics collector.

Polls the RabbitMQ Management API at a fixed interval and writes CSV rows
with queue depth, consumer count, publish/deliver rates, and node memory.
Designed to run in parallel with Locust on the master instance.

Usage (standalone):
    uv run python -m codabench_loadtest.monitors.rabbitmq_monitor \
        --duration 600 --interval 5 --output runs/rabbit_metrics.csv

Usage (from Python):
    monitor = RabbitMQMonitor(settings)
    monitor.start(duration=600, output_path="runs/rabbit_metrics.csv")
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, ClassVar

import requests

from codabench_loadtest.setup import Settings


@dataclass
class QueueSnapshot:
    timestamp: str
    queue_name: str
    messages_total: int = 0
    messages_ready: int = 0
    messages_unacked: int = 0
    consumers: int = 0
    publish_rate: float = 0.0
    deliver_rate: float = 0.0
    ack_rate: float = 0.0
    node_memory_bytes: int = 0

    CSV_HEADERS: ClassVar[list[str]] = [
        "timestamp",
        "queue_name",
        "messages_total",
        "messages_ready",
        "messages_unacked",
        "consumers",
        "publish_rate",
        "deliver_rate",
        "ack_rate",
        "node_memory_bytes",
    ]

    def as_row(self) -> list[Any]:
        return [
            self.timestamp,
            self.queue_name,
            self.messages_total,
            self.messages_ready,
            self.messages_unacked,
            self.consumers,
            f"{self.publish_rate:.2f}",
            f"{self.deliver_rate:.2f}",
            f"{self.ack_rate:.2f}",
            self.node_memory_bytes,
        ]


class RabbitMQMonitor:
    def __init__(self, settings: Settings):
        self.base_url = settings.rabbitmq_url.rstrip("/")
        self.auth = (
            settings.rabbitmq_user,
            settings.rabbitmq_password.get_secret_value(),
        )
        self.session = requests.Session()
        self.session.auth = self.auth

    def _get(self, path: str) -> Any:
        resp = self.session.get(f"{self.base_url}/api{path}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _rate(self, details: dict, key: str = "rate") -> float:
        if not details:
            return 0.0
        return details.get(key, 0.0)

    def snapshot_queue(self, queue_name: str, vhost: str = "%2F") -> QueueSnapshot:
        data = self._get(f"/queues/{vhost}/{queue_name}")
        return QueueSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            queue_name=queue_name,
            messages_total=data.get("messages", 0),
            messages_ready=data.get("messages_ready", 0),
            messages_unacked=data.get("messages_unacknowledged", 0),
            consumers=data.get("consumers", 0),
            publish_rate=self._rate(
                data.get("message_stats", {}).get("publish_details", {})
            ),
            deliver_rate=self._rate(
                data.get("message_stats", {}).get("deliver_get_details", {})
            ),
            ack_rate=self._rate(data.get("message_stats", {}).get("ack_details", {})),
            node_memory_bytes=self._get_node_memory(data.get("node", "")),
        )

    def snapshot_all_queues(self) -> list[QueueSnapshot]:
        queues = self._get("/queues")
        snapshots = []
        for q in queues:
            name = q.get("name", "")
            snapshots.append(
                QueueSnapshot(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    queue_name=name,
                    messages_total=q.get("messages", 0),
                    messages_ready=q.get("messages_ready", 0),
                    messages_unacked=q.get("messages_unacknowledged", 0),
                    consumers=q.get("consumers", 0),
                    publish_rate=self._rate(
                        q.get("message_stats", {}).get("publish_details", {})
                    ),
                    deliver_rate=self._rate(
                        q.get("message_stats", {}).get("deliver_get_details", {})
                    ),
                    ack_rate=self._rate(
                        q.get("message_stats", {}).get("ack_details", {})
                    ),
                    node_memory_bytes=self._get_node_memory(q.get("node", "")),
                )
            )
        return snapshots

    def _get_node_memory(self, node_name: str) -> int:
        if not node_name:
            return 0
        try:
            node = self._get(f"/nodes/{node_name}")
            return node.get("mem_used", 0)
        except requests.RequestException:
            return 0

    def start(
        self,
        duration: int = 600,
        interval: float = 5.0,
        output_path: str = "runs/rabbit_metrics.csv",
        queue_name: str | None = None,
    ) -> None:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        print(f"RabbitMQ monitor: writing to {output}")
        print(f"  Target:   {self.base_url}")
        print(f"  Queue:    {queue_name or 'all'}")
        print(f"  Duration: {duration}s, interval: {interval}s")
        print()

        start_time = time.monotonic()
        first_write = True

        while time.monotonic() - start_time < duration:
            try:
                if queue_name:
                    snapshots = [self.snapshot_queue(queue_name)]
                else:
                    snapshots = self.snapshot_all_queues()

                with open(output, "a", newline="") as f:
                    writer = csv.writer(f)
                    if first_write:
                        writer.writerow(snapshots[0].CSV_HEADERS)
                        first_write = False
                    for snap in snapshots:
                        writer.writerow(snap.as_row())

                elapsed = time.monotonic() - start_time
                remaining = duration - elapsed
                for snap in snapshots:
                    print(
                        f"[{elapsed:6.0f}s/{duration}s] "
                        f"{snap.queue_name}: "
                        f"depth={snap.messages_total} "
                        f"ready={snap.messages_ready} "
                        f"unacked={snap.messages_unacked} "
                        f"consumers={snap.consumers} "
                        f"pub={snap.publish_rate:.1f}/s "
                        f"del={snap.deliver_rate:.1f}/s "
                        f"mem={snap.node_memory_bytes / 1024 / 1024:.0f}MB "
                        f"({remaining:.0f}s left)"
                    )

            except requests.RequestException as e:
                print(f"[warning] RabbitMQ poll failed: {e}", file=sys.stderr)

            time.sleep(interval)

        print(f"\nDone. Metrics saved to {output}")


def main():
    parser = argparse.ArgumentParser(description="RabbitMQ queue metrics collector")
    parser.add_argument(
        "--queue",
        type=str,
        default=None,
        help="Specific queue name to monitor. If omitted, monitors all queues.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=600,
        help="Duration in seconds (default: 600)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Poll interval in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="runs/rabbit_metrics.csv",
        help="Output CSV path (default: runs/rabbit_metrics.csv)",
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to .env file (default: auto-detect)",
    )
    args = parser.parse_args()

    kwargs = {}
    if args.env_file:
        kwargs["_env_file"] = args.env_file

    settings = Settings(**kwargs)  # type: ignore[arg-type]
    monitor = RabbitMQMonitor(settings)
    monitor.start(
        duration=args.duration,
        interval=args.interval,
        output_path=args.output,
        queue_name=args.queue,
    )


if __name__ == "__main__":
    main()
