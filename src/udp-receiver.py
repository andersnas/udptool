# udp_receiver.py
import socket
import struct
import time

UDP_IP = "0.0.0.0"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
sock.setblocking(True)

print(f"Listening on {UDP_IP}:{UDP_PORT} (UDP only)")

expected_seq = 0
received = 0
lost = 0
bytes_received = 0
start_time = time.time()
last_report = start_time
last_bytes = 0


while True:
    data, addr = sock.recvfrom(65535)
    now = time.time()

    if len(data) < 8:
        # ignore malformed packets
        continue

    (seq,) = struct.unpack("!Q", data[:8])  # 8-byte unsigned big-endian
    payload_len = len(data)

    # Count loss by missing sequence numbers
    if seq > expected_seq:
        lost += (seq - expected_seq)
        expected_seq = seq + 1
    elif seq == expected_seq:
        expected_seq += 1
    else:
        # out-of-order/duplicate; ignore for loss stats
        pass

    received += 1
    bytes_received += payload_len

    # Print stats every second
    if now - last_report >= 1.0:
        elapsed_total = now - start_time
        interval = now - last_report
        interval_bytes = bytes_received - last_bytes

        # instant (per-interval) throughput
        inst_mbits = (interval_bytes * 8) / (1e6 * interval) if interval > 0 else 0

        print(
            f"Time {elapsed_total:.1f}s "
            f"| rx_pkts={received} lost_pkts={lost} loss_pct={100*lost/(received+lost):.3f}% "
            f"| inst={inst_mbits:.2f} Mbit/s"
        )

        last_report = now
        last_bytes = bytes_received
