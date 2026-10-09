# Cloud-Agnostic Deployment Platform
A local Kubernetes proof of concept demonstrating a stateless API, Redis-backed worker, Helm deployments, health probes, rolling updates, and CPU-based autoscaling.
## Architecture
- API: Python HTTP server on port 8080
- Endpoints: /healthz, /readyz, /metrics
- Orchestration: Kubernetes using kind
- Packaging: Helm
- API replicas: minimum 2, maximum 10 through HPA
- Queue: Redis list named jobs
- Worker: Python process consuming Redis jobs
- CI workflow: GitHub Actions unit tests, image builds, and Trivy scans
## Prerequisites
- Docker Desktop
- kubectl
- kind
- Helm
- Python 3.13
- Git
## Run Unit Tests
```powershell
python -m unittest discover -s tests -v
```
## Build and Load Images
```powershell
docker build -t devops-sample-api:1.1 app
kind load docker-image devops-sample-api:1.1 --name devops-platform
docker build -t devops-sample-worker:1.0 app/worker
kind load docker-image devops-sample-worker:1.0 --name devops-platform
```
## Deploy Locally
The kind cluster devops-platform and namespace devops must exist.
```powershell
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/worker.yaml
helm upgrade --install devops-api ./helm/devops-api -n devops
kubectl apply -f hpa.yaml
```
## Test a Worker Job
```powershell
kubectl exec -n devops deployment/redis -- redis-cli LPUSH jobs "test-job-001"
kubectl logs deployment/devops-worker -n devops --since=5m
```
## Verify the Deployment
```powershell
kubectl rollout status deployment/devops-api -n devops
kubectl get pods -n devops
kubectl get hpa -n devops
```
## Current Verification
- API unit tests have passed locally.
- API deployment rollout has completed successfully.
- API, Redis, and worker pods were observed running.
- A Redis job was processed and its completion was confirmed.
- CPU-based HPA has been observed scaling locally.
## Known Limitations
This is a local proof of concept, not a production-ready deployment platform.
- Cloud-provider Terraform deployment has not been verified.
- PostgreSQL and database migration handling are not implemented.
- Image signing and immutable digest promotion are not implemented.
- Automated rollback based on deployment metrics is not implemented; manual rollback was tested.
- The 15x load target and p95 latency objective have not been demonstrated.
- Redis high availability, durable job acknowledgements, retries, and dead-letter handling are not implemented.
- Tenant isolation, regional failover, and backup/restore testing remain incomplete.
- The GitHub Actions workflow has been created but must be pushed to GitHub and run before its results can be verified.
## Security Notes
Do not commit credentials, .env files, Terraform state, or cloud secrets. Use protected GitHub secrets or workload identity for future cloud integrations.
