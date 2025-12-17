#!/usr/bin/env python3
import os
import socket
import struct
import time
import select

BASE_PORT = int(os.environ.get("BASE_PORT", "5005"))
NUM_PORTS = 4  # listen on BASE_PORT..BASE_PORT+3
UDP_IP = "0.0.0.0"

# Per-port state
stats = {}
sockets = []

for i in range(NUM_PORTS):
    port = BASE_PORT + i
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, port))
    sock.setblocking(False)

    sockets.append(sock)
    stats[port] = {
        "expected_seq": 0,
        "received": 0,
        "lost": 0,
        "bytes": 0,
        "start_time": None,
        "last_report": None,
        "last_bytes": 0,
        "line_position": i,  # track which line this port should update
    }

    print(f"Listening on {UDP_IP}:{port} (UDP only)")


def update_stats_for_port(port, payload_len, seq):
    now = time.time()
    s = stats[port]

    # First packet on this port: initialize without counting loss
    if s["start_time"] is None:
        s["start_time"] = now
        s["last_report"] = now
        s["last_bytes"] = 0
        s["expected_seq"] = seq + 1  # start from the next expected seq
        s["received"] = 1
        s["bytes"] = payload_len
        # s["lost"] stays 0
        return

    # Subsequent packets: normal loss accounting
    if seq > s["expected_seq"]:
        s["lost"] += (seq - s["expected_seq"])
        s["expected_seq"] = seq + 1
    elif seq == s["expected_seq"]:
        s["expected_seq"] += 1
    else:
        # out-of-order/duplicate
        pass

    s["received"] += 1
    s["bytes"] += payload_len



def reset_port_stats(port):
    """Reset all metrics for a port when throughput drops to 0."""
    s = stats[port]
    line_pos = s["line_position"]  # preserve line position
    stats[port] = {
        "expected_seq": 0,
        "received": 0,
        "lost": 0,
        "bytes": 0,
        "start_time": None,
        "last_report": None,
        "last_bytes": 0,
        "line_position": line_pos,
    }


def maybe_print_stats():
    now = time.time()

    for port, s in stats.items():
        if s["start_time"] is None:
            continue  # no traffic yet on this port

        # Check if enough time has passed since last report
        if now - s["last_report"] < 1.0:
            continue  # print at most once a second per port

        elapsed_total = now - s["start_time"]
        interval = now - s["last_report"]
        interval_bytes = s["bytes"] - s["last_bytes"]

        inst_mbits = (interval_bytes * 8) / (1e6 * interval) if interval > 0 else 0

        # Reset all metrics when throughput drops to 0
        if inst_mbits == 0 or interval_bytes == 0:
            # Clear the line for this port
            line_pos = s["line_position"]
            lines_up = NUM_PORTS - line_pos
            output = (
                f"\033[{lines_up}A"  # Move cursor up to the port's line
                f"\r"  # Move to beginning of line
                f"\033[K"  # Clear the line
                f"Port {port} | Waiting for traffic..."
                f"\033[{lines_up}B"  # Move cursor back down
            )
            print(output, end='', flush=True)

            reset_port_stats(port)
            continue

        total_pkts = s["received"] + s["lost"]
        loss_pct = 100 * s["lost"] / total_pkts if total_pkts > 0 else 0.0

        # Update the line in place using ANSI escape codes
        line_pos = s["line_position"]
        # Calculate how many lines to move up from current position
        lines_up = NUM_PORTS - line_pos

        output = (
            f"\033[{lines_up}A"  # Move cursor up to the port's line
            f"\r"  # Move to beginning of line
            f"\033[K"  # Clear the line
            f"Port {port} | Time {elapsed_total:.1f}s "
            f"| rx_pkts={s['received']} lost_pkts={s['lost']} loss_pct={loss_pct:.3f}% "
            f"| inst={inst_mbits:.2f} Mbit/s"
            f"\033[{lines_up}B"  # Move cursor back down
        )
        print(output, end='', flush=True)

        s["last_report"] = now
        s["last_bytes"] = s["bytes"]


def main():
    # Initialize display with placeholder lines for each port
    print()  # blank line
    for i in range(NUM_PORTS):
        port = BASE_PORT + i
        print(f"Port {port} | Waiting for traffic...")

    while True:
        # wait for data or timeout every 1s to print stats
        readable, _, _ = select.select(sockets, [], [], 1.0)

        for sock in readable:
            try:
                data, addr = sock.recvfrom(65535)
            except BlockingIOError:
                continue

            if len(data) < 8:
                continue

            (seq,) = struct.unpack("!Q", data[:8])
            payload_len = len(data)

            local_port = sock.getsockname()[1]
            update_stats_for_port(local_port, payload_len, seq)

        maybe_print_stats()


if __name__ == "__main__":
    main()
