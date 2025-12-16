# udp_sender.py
import socket
import struct
import sys
import time

if len(sys.argv) < 5:
    print("Usage: udp_sender.py <ip> <port> <duration_s> <rate_mbit>")
    sys.exit(1)

IP = sys.argv[1]
PORT = int(sys.argv[2])
DURATION = float(sys.argv[3])
RATE_MBIT = float(sys.argv[4])

PAYLOAD_SIZE = 1400  # bytes total (including 8 bytes seq)
SEQ_SIZE = 8

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

bytes_per_sec = RATE_MBIT * 1e6 / 8
pkt_per_sec = bytes_per_sec / PAYLOAD_SIZE
interval = 1.0 / pkt_per_sec if pkt_per_sec > 0 else 0

print(
    f"Sending to {IP}:{PORT} for {DURATION}s at ~{RATE_MBIT} Mbit/s "
    f"({pkt_per_sec:.0f} pps, packet size={PAYLOAD_SIZE})"
)

seq = 0
start = time.time()
next_send = start

while True:
    now = time.time()
    if now - start >= DURATION:
        break

    if now < next_send:
        # Sleep a bit to shape rate
        time.sleep(min(next_send - now, 0.001))

    payload = struct.pack("!Q", seq) + b"x" * (PAYLOAD_SIZE - SEQ_SIZE)
    sock.sendto(payload, (IP, PORT))
    seq += 1
    next_send += interval

print("Done.")
