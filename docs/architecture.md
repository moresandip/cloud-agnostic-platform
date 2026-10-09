# Cloud-Agnostic Zero-Downtime Deployment Platform



**Architecture Document**



**Status:** Initial design - local Kubernetes implementation in progress

**Repository:** `cloud-agnostic-platform`

**Environment:** Local `kind` cluster and proposed cloud deployment

**Date:** October 2026



## 1. Purpose and Requirements



The goal is to build a cloud-agnostic deployment platform that supports safe application releases, automatic rollback, horizontal scaling, monitoring, and recovery.



The platform contains a stateless API, background job workers, Redis for job queuing, and PostgreSQL for persistent data. Infrastructure is organized into provider, platform, and application layers.



### Key requirements



| Requirement             | Target                                        |

| ----------------------- | --------------------------------------------- |

| API                     | Port 8080; `/healthz`, `/readyz`, `/metrics`  |

| Baseline / peak traffic | 150 / 2,250 requests per second               |

| Background processing   | 20,000 jobs per hour; jobs up to 60 seconds   |

| API latency             | p95 below 400 ms                              |

| Availability            | 99.9% shared; 99.95% dedicated                |

| Budget                  | $9,000/month steady; $16,000/month peak       |

| Data residency          | EU tenant data must remain in the EU          |

| Deployment              | Zero-downtime rollout with automatic rollback |

| Environments            | Shared and dedicated tenant environments      |



These values are design targets, not measured results.



## 2. Architecture Diagram



```mermaid

flowchart TB

&#x20;   U\[Users and Clients] --> ING\[Load Balancer / Ingress]

&#x20;   ING --> API\[Stateless API Pods]

&#x20;   API --> REDIS\[Redis Job Queue]

&#x20;   API --> PG\[(PostgreSQL)]

&#x20;   REDIS --> W\[Background Worker Pods]

&#x20;   W --> PG



&#x20;   API --> MET\[Metrics and Health Endpoints]

&#x20;   W --> MET

&#x20;   MET --> MON\[Monitoring and Alerts]



&#x20;   GIT\[Git Repository] --> CI\[CI: Tests and Build]

&#x20;   CI --> SCAN\[Image Security Scan]

&#x20;   SCAN --> REG\[Container Registry]

&#x20;   REG --> CD\[CD: Deploy and Verify]

&#x20;   CD --> ING



&#x20;   CD --> RB\[Rollback on Failed Gates]

&#x20;   RB --> CD



&#x20;   TF\[Terraform: Provider Layer] --> K8S\[Kubernetes Platform]

&#x20;   K8S --> ING

&#x20;   K8S --> API

&#x20;   K8S --> REDIS

&#x20;   K8S --> W

&#x20;   K8S --> PG

```



### Architecture explanation



* **Ingress/load balancer:** Routes requests to healthy API replicas.

* **API:** Handles HTTP requests without storing session state in local memory.

* **Redis:** Provides the background job queue. Production deployment must use appropriate persistence and recovery settings.

* **Workers:** Process jobs independently and handle retries and graceful shutdown.

* **PostgreSQL:** Stores persistent application data. Managed database services or a properly operated database platform are preferred for production.

* **CI/CD:** Tests code, builds and scans container images, deploys the approved image, checks health and performance, and triggers rollback if release gates fail.

* **Monitoring:** Collects latency, request rate, errors, resource utilization, queue depth, and job processing metrics.

* **Infrastructure as Code:** Terraform provisions provider resources; Kubernetes and Helm manage platform and application resources.



The local implementation currently includes the API, Redis, worker, Kubernetes manifests, Helm chart, unit tests, and a CI workflow. PostgreSQL integration, production-grade monitoring, and automated release gates remain to be implemented or verified.



## 3. Infrastructure Layers



| Layer       | Responsibility                                                       | Proposed tools             |

| ----------- | -------------------------------------------------------------------- | -------------------------- |

| Provider    | Networking, compute, registry, database, IAM and storage             | Terraform                  |

| Platform    | Kubernetes, ingress, autoscaling, monitoring and secrets integration | Kubernetes, Helm           |

| Application | API, worker, configuration, probes and rollout settings              | Docker, Helm values, CI/CD |



The same application image should be promoted between environments using its immutable digest. Environment-specific configuration must not require rebuilding the image.



Shared environments reduce cost through resource sharing and tenant isolation controls. Dedicated environments provide stronger resource and operational isolation for tenants that need a higher availability target.



## 4. Design Decisions and Rejected Alternatives



### Decision 1 - Kubernetes for application orchestration



**Chosen:** Kubernetes, with `kind` for local development and a managed Kubernetes service as the cloud deployment target.



**Reason:** Supports rolling updates, health probes, service discovery, workload scaling, and portable application manifests.



**Rejected alternative:** Managing application containers directly on individual virtual machines. This requires more custom orchestration and recovery automation.



### Decision 2 - Stateless API with multiple replicas



**Chosen:** Run multiple API replicas behind a Service and ingress/load balancer. Use readiness checks to control traffic and a rolling-update strategy with zero unavailable replicas where capacity permits.



**Reason:** Requests can be served by any healthy replica, reducing dependence on individual instances.



**Rejected alternative:** A single API instance, which creates a single point of failure.



**Trade-off:** Additional replicas consume resources, and zero-downtime rollout depends on sufficient capacity, correct probes, and application compatibility.



### Decision 3 - Redis for background jobs



**Chosen:** Keep long-running jobs outside the synchronous HTTP request path and process them using worker replicas.



**Reason:** Allows the API to respond without waiting for jobs that can take up to 60 seconds and allows worker capacity to scale separately.



**Rejected alternative:** Processing every job synchronously inside the API.



**Trade-off:** Redis lists alone do not guarantee exactly-once processing. Production requires durable queue configuration, safe acknowledgement and retry behavior, idempotent job handlers, and crash recovery.



### Decision 4 - PostgreSQL with expand-and-contract migrations



**Chosen:** Use backward-compatible schema expansion before deploying application versions that depend on new fields. Remove obsolete schema elements only after old versions no longer need them.



**Reason:** API replicas may run different application versions during a rolling deployment.



**Rejected alternative:** Applying destructive, incompatible database changes before deploying the new application version.



**Trade-off:** Some schema changes require multiple releases and temporary compatibility code. Database migrations need backups, monitoring, and explicit recovery procedures.



### Decision 5 - Terraform plus Kubernetes/Helm



**Chosen:** Separate infrastructure provisioning from platform and application configuration.



**Reason:** This makes provider-specific infrastructure replaceable while keeping most workload definitions portable.



**Rejected alternative:** Maintaining separate, manually configured environments for every cloud.



**Trade-off:** Cloud-specific networking, identity, storage, and managed database capabilities still require provider-specific modules and testing.



### Decision 6 - Immutable image promotion and metric-based rollback



**Chosen:** Build an image once, scan it, record its digest, and promote the same digest across environments. Verify readiness and release metrics before marking a rollout successful.



**Reason:** Prevents environment drift and makes the deployed artifact traceable.



**Rejected alternative:** Rebuilding images separately for each environment or rolling back solely because a deployment command failed.



**Trade-off:** Rollback requires a compatible previous application version, retained images, observable release health, and database changes that remain compatible with the previous version.



## 5. Top Five Risks and Mitigations



| Risk                                             | Impact                                                        | Mitigation                                                                                                                      |

| ------------------------------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |

| 1. Traffic spikes or resource exhaustion         | High latency, failed requests, or unavailable services        | Load testing, resource requests/limits, autoscaling, capacity headroom, and alerts                                              |

| 2. Database migration incompatibility            | Failed releases, application errors, or data loss             | Expand-and-contract migrations, backups, migration validation, and tested recovery procedures                                   |

| 3. Queue loss or duplicate jobs                  | Lost work, repeated side effects, or delayed processing       | Redis persistence, durable queue design, idempotency, retries, dead-letter handling, and restore testing                        |

| 4. Incorrect release or failed rollback          | Extended outage or incompatible application/database versions | Immutable image digests, progressive rollout, health and metric gates, retained last-known-good version, and rollback drills    |

| 5. Tenant isolation, residency, or cloud failure | Data exposure, residency violations, or prolonged outage      | Tenant-specific access policies, regional placement controls, encryption, audit logs, backups, and tested cross-region recovery |



Risks should be reviewed regularly, with named owners and measurable mitigation status added before production readiness approval.



## 6. Security, Availability and Operations



* Scan application and worker images for vulnerabilities and block releases that violate the agreed severity policy.

* Use least-privilege service accounts and IAM, secret management, TLS, and encryption at rest.

* Keep EU tenant data and its required backups within approved EU regions.

* Configure readiness and liveness probes according to their different purposes; avoid restarting applications solely because of temporary load or dependency delays.

* Use graceful termination and sufficient termination grace periods for workers processing long-running jobs.

* Define alerts for elevated error rates, p95 latency, unavailable replicas, queue backlog, failed jobs, and database health.

* Maintain runbooks for release failure, database recovery, queue recovery, and regional failover.

* Validate backup restoration and monitor actual recovery time and data loss against approved objectives.



## 7. Validation and Acceptance Plan



| Test                  | Acceptance condition                                                 | Current evidence           |

| --------------------- | -------------------------------------------------------------------- | -------------------------- |

| Unit tests            | All API tests pass                                                   | 3 tests passed locally     |

| Helm validation       | Chart lint succeeds                                                  | Passed locally             |

| Deployment under load | No failed requests during the defined rollout test                   | Not yet demonstrated       |

| Automatic rollback    | Deliberately bad release is detected and reverted                    | Not yet demonstrated       |

| 15Ã— load test         | Sustain 2,250 requests/second while measuring errors and p95 latency | Not yet demonstrated       |

| Restore test          | Restore a backup and verify data integrity and recovery time         | Not yet demonstrated       |

| Regional failover     | Traffic and services recover in the approved failover scenario       | Design and testing pending |



Local Kubernetes has shown intermittent API and Redis health-probe timeouts. These issues must be resolved and stability revalidated before claiming successful zero-downtime or load testing.



## 8. Conclusion



The proposed design separates infrastructure, platform operations, and application delivery to improve portability, repeatability, and release safety. Production readiness depends on completing infrastructure automation, database integration, monitoring and release gates, and collecting genuine test evidence. Performance, availability, and failover targets remain unverified until their corresponding tests pass.
