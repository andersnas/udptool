FROM python:3.11-slim

WORKDIR /app

COPY udp_receiver.py /app/udp_receiver.py

ENV PYTHONUNBUFFERED=1

CMD ["python", "udp_receiver.py"]
