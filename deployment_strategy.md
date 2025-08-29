# Project Guardian 2.0  
## PII Detection & Redaction - Deployment Strategy  

### Overview  
Project Guardian 2.0 introduces a **multi-layered PII detection and redaction system** to stop sensitive data leaks at different points of the data lifecycle. Instead of relying on a single checkpoint, the system is deployed at multiple layers:  
- **Ingress/Egress APIs**  
- **Service-to-Service traffic**  
- **Centralized logging pipelines**  
- **Database persistence layer**  

This approach ensures that even if one layer misses something, another layer will catch it. The goal is **security with minimal latency impact**.  

---

### Architecture Layers  

#### 1. API Gateway Plugin (Primary Defense)  
- **Location:** Kong / Envoy / AWS API Gateway  
- **Purpose:** First line of defense for external API requests  
- **Implementation:** Lua script (Kong) or WASM filter (Envoy)  
- **Notes:**  
  - Adds ~2-5ms latency  
  - Centralized policy management  
  - Async logging of detection events  

#### 2. Service Mesh Sidecar (Application Layer)  
- **Location:** Istio / Linkerd sidecar containers  
- **Purpose:** Protects service-to-service traffic without app code changes  
- **Implementation:** Envoy filters in sidecars  
- **Notes:**  
  - Adds ~1-3ms latency  
  - Granular policies per service  
  - Integrated observability (metrics + tracing)  

#### 3. Log Processing Pipeline (Centralized Layer)  
- **Location:** Kafka Streams / Apache Flink / AWS Kinesis  
- **Purpose:** Sanitize logs before they reach data lakes/warehouses  
- **Implementation:** Stream processors that redact PII in real-time  
- **Notes:**  
  - Near real-time (<100ms delay)  
  - Redacted logs stored, original PII never enters warehouse  
  - Audit trail maintained in a dedicated PII Audit DB  

#### 4. Database Proxy Layer (Persistence Layer)  
- **Location:** ProxySQL / PgBouncer with middleware  
- **Purpose:** Last defense before sensitive data is persisted  
- **Implementation:** Query parsing + PII redaction middleware  
- **Notes:**  
  - <2ms added latency  
  - Transparent to existing applications  
  - Can cache redaction rules for performance  

---

### Rollout Plan  

- **Phase 1 (Weeks 1-2):**  
  Deploy API Gateway plugin in staging → run traffic replay tests → roll out gradually in production.  

- **Phase 2 (Weeks 3-4):**  
  Add sidecars to non-critical microservices → validate latency → expand coverage across services.  

- **Phase 3 (Weeks 5-6):**  
  Deploy log processing pipeline → integrate with Kafka/Flink → connect sanitized logs to data warehouse → enable audit dashboards.  

- **Phase 4 (Weeks 7-8):**  
  Deploy database proxy in staging → run load tests → implement production rollout with failover support.  

---

### Performance & Scalability  

- **Latency targets:**  
  - Gateway: <5ms  
  - Sidecar: <3ms  
  - Log pipeline: <100ms  
  - DB proxy: <2ms  

- **Scalability:**  
  - 10,000+ requests/sec per instance  
  - Horizontal auto-scaling based on CPU/memory  
  - Memory footprint <256MB per instance  
  - CPU overhead <10%  

---

### Monitoring & Alerting  

- **Key Metrics:**  
  - Detection rate (instances/hour)  
  - False positive rate (<1%)  
  - P95/P99 latency for detection  
  - Throughput per service  
  - Error rate  

- **Alerting Thresholds:**  
  - High detection rate (>1000/hr)  
  - Latency >10ms at P95  
  - Error rate >1%  
  - CPU >80% or Memory >90%  

---

### Security & Compliance  

- **Data Protection:**  
  - All detection logs encrypted (in transit + at rest)  
  - RBAC for access control  
  - Configurable data retention policies  
  - Immutable audit logs  

- **Regulatory Alignment:**  
  - **GDPR**: right to erasure, portability  
  - **PCI DSS**: cardholder data redaction  
  - **SOX**: audit + financial data protection  
  - **Indian DPDP Act**: local compliance requirements  

---

### Risks & Mitigation  

- **Performance Degradation:** Use circuit breakers and bypass fallback.  
- **False Positives:** Start with conservative rules, tune gradually.  
- **Single Point of Failure:** Multi-region deployment with failover.  
- **Operational Gaps:** Developer/ops training sessions and runbooks.  

---

### Success Criteria  

- **Primary:**  
  - Zero raw PII leakage in APIs/logs/db  
  - Average latency overhead <5ms  
  - 99.9% uptime across layers  
  - False positive rate <1%  

- **Secondary:**  
  - 100% regulatory compliance (GDPR, PCI DSS, Indian DPDP)  
  - ROI >500% (cost vs. fraud prevention + compliance savings)  
  - Increased customer trust & reduced incident reports  

---

### Conclusion  

The proposed deployment ensures that PII is filtered at **multiple critical control points** — API boundary, service-to-service communication, centralized logging, and database persistence. The phased rollout reduces operational risk, while monitoring and audit systems ensure compliance. This layered defense significantly reduces the chance of another large-scale breach while keeping performance overhead minimal.  

---
