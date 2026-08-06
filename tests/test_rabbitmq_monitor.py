import requests_mock

from codabench_loadtest.monitors.rabbitmq_monitor import QueueSnapshot, RabbitMQMonitor


def test_queue_snapshot_as_row_formats_rates() -> None:
    snapshot = QueueSnapshot(
        timestamp="2026-08-06T12:00:00+00:00",
        queue_name="jobs",
        messages_total=12,
        messages_ready=3,
        messages_unacked=9,
        consumers=2,
        publish_rate=1.234,
        deliver_rate=5.678,
        ack_rate=9.876,
        node_memory_bytes=1024,
    )

    assert snapshot.as_row() == [
        "2026-08-06T12:00:00+00:00",
        "jobs",
        12,
        3,
        9,
        2,
        "1.23",
        "5.68",
        "9.88",
        1024,
    ]


def test_snapshot_queue_uses_rabbitmq_api_and_node_memory(config) -> None:
    monitor = RabbitMQMonitor(config)

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"{config.rabbitmq_url}/api/queues/%2F/loadtest",
            json={
                "messages": 7,
                "messages_ready": 4,
                "messages_unacknowledged": 3,
                "consumers": 2,
                "message_stats": {
                    "publish_details": {"rate": 1.5},
                    "deliver_get_details": {"rate": 2.5},
                    "ack_details": {"rate": 3.5},
                },
                "node": "rabbit@node-1",
            },
        )
        mocker.get(
            f"{config.rabbitmq_url}/api/nodes/rabbit@node-1",
            json={"mem_used": 4096},
        )

        snapshot = monitor.snapshot_queue("loadtest")

    assert snapshot.queue_name == "loadtest"
    assert snapshot.messages_total == 7
    assert snapshot.messages_ready == 4
    assert snapshot.messages_unacked == 3
    assert snapshot.consumers == 2
    assert snapshot.publish_rate == 1.5
    assert snapshot.deliver_rate == 2.5
    assert snapshot.ack_rate == 3.5
    assert snapshot.node_memory_bytes == 4096


def test_snapshot_all_queues_returns_all_snapshots(config) -> None:
    monitor = RabbitMQMonitor(config)

    with requests_mock.Mocker() as mocker:
        mocker.get(
            f"{config.rabbitmq_url}/api/queues",
            json=[
                {
                    "name": "queue-a",
                    "messages": 1,
                    "messages_ready": 1,
                    "messages_unacknowledged": 0,
                    "consumers": 1,
                    "message_stats": {"publish_details": {"rate": 0.1}},
                    "node": "rabbit@node-1",
                },
                {
                    "name": "queue-b",
                    "messages": 2,
                    "messages_ready": 2,
                    "messages_unacknowledged": 0,
                    "consumers": 0,
                    "message_stats": {"deliver_get_details": {"rate": 0.2}},
                    "node": "rabbit@node-2",
                },
            ],
        )
        mocker.get(
            f"{config.rabbitmq_url}/api/nodes/rabbit@node-1", json={"mem_used": 111}
        )
        mocker.get(
            f"{config.rabbitmq_url}/api/nodes/rabbit@node-2", json={"mem_used": 222}
        )

        snapshots = monitor.snapshot_all_queues()

    assert [snap.queue_name for snap in snapshots] == ["queue-a", "queue-b"]
    assert [snap.node_memory_bytes for snap in snapshots] == [111, 222]


def test_get_node_memory_returns_zero_when_api_call_fails(config) -> None:
    monitor = RabbitMQMonitor(config)

    with requests_mock.Mocker() as mocker:
        mocker.get(f"{config.rabbitmq_url}/api/nodes/rabbit@node-1", status_code=500)

        assert monitor._get_node_memory("rabbit@node-1") == 0
