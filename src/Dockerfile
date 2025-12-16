FROM python:3.11-slim

WORKDIR /app

# No extra deps needed, stdlib only
COPY udp_receiver.py /app/udp_receiver.py

# Make log flushing more responsive
ENV PYTHONUNBUFFERED=1

CMD ["python", "udp_receiver.py"]
