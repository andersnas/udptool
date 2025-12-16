Reads and writes streams of data over UDP.

BUILD FOR LKE:
docker buildx build \
  --platform linux/amd64 \
  -t DOCKERUSERNAME/udp-receiver:latest \
  --push .

INSTALL IN K8S:
kubectl apply -f deployment.yaml

CHECK POD:
kubectl get pods -l app=udp-receiver

DELETE IN K8S:
kubectl delete deployment udp-receiver

CHECK POD logs:
kubectl logs -f deploy/udp-receiver

CHECK PORTS: 
kubectl get svc udp-receiver

CHECK IPS:
kubectl get nodes -o wide

TO TEST:
python3 udp_sender.py EXTERNAL-IP EXTERNAL-PORT 300 10
