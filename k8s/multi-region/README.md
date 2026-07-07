# Nexus Framework - Multi-Region Kubernetes Deployment

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │      AWS Global Accelerator         │
                    │    (Anycast IP + Geo Routing)       │
                    └─────────────┬───────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
   ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
   │ us-east-1   │◄──────►│ eu-west-1   │◄──────►│ me-south-1  │
   │ (Primary)   │        │ (Secondary) │        │ (Secondary) │
   │             │        │             │        │             │
   │  EKS Cluster│        │  EKS Cluster│        │  EKS Cluster│
   │  ┌───────┐  │        │  ┌───────┐  │        │  ┌───────┐  │
   │  │Backend│  │        │  │Backend│  │        │  │Backend│  │
   │  │  x3   │  │        │  │  x2   │  │        │  │  x2   │  │
   │  └───────┘  │        │  └───────┘  │        │  └───────┘  │
   │  ┌───────┐  │        │  ┌───────┐  │        │  ┌───────┐  │
   │  │Frontend│  │        │  │Frontend│  │        │  │Frontend│  │
   │  │  x2   │  │        │  │  x2   │  │        │  │  x2   │  │
   │  └───────┘  │        │  └───────┘  │        │  └───────┘  │
   │             │        │             │        │             │
   │  ┌───────┐  │        │  ┌───────┐  │        │  ┌───────┐  │
   │  │Aurora │  │◄──────►│  │Aurora │  │◄──────►│  │Aurora │  │
   │  │Primary│  │  Async │  │Replica│  │  Async │  │Replica│  │
   │  └───────┘  │        │  └───────┘  │        │  └───────┘  │
   │             │        │             │        │             │
   │  ┌───────┐  │        │  ┌───────┐  │        │  ┌───────┐  │
   │  │Elasti │  │◄──────►│  │Elasti │  │◄──────►│  │Elasti │  │
   │  │Cache  │  │ Global │  │Cache  │  │ Global │  │Cache  │  │
   │  └───────┘  │        │  └───────┘  │        │  └───────┘  │
   │             │        │             │        │             │
   │  ┌───────┐  │        │  ┌───────┐  │        │  ┌───────┐  │
   │  │Kafka  │  │◄──────►│  │Kafka  │  │◄──────►│  │Kafka  │  │
   │  │MSK    │  │ Mirror │  │MSK    │  │ Mirror │  │MSK    │  │
   │  └───────┘  │        │  └───────┘  │        │  └───────┘  │
   └─────────────┘        └─────────────┘        └─────────────┘
```

## Deployment

### Prerequisites
- Terraform >= 1.5
- kubectl
- helm
- aws-cli

### 1. Deploy Infrastructure
```bash
cd k8s/multi-region
terraform init
terraform plan
terraform apply
```

### 2. Configure kubectl
```bash
aws eks update-kubeconfig --region us-east-1 --name nexus-us-east-1
aws eks update-kubeconfig --region eu-west-1 --name nexus-eu-west-1
aws eks update-kubeconfig --region me-south-1 --name nexus-me-south-1
```

### 3. Deploy with ArgoCD
```bash
kubectl apply -f argocd-appset.yaml
```

### 4. Verify Deployment
```bash
kubectl get pods -n nexus --all-namespaces
kubectl get svc -n nexus
```

## Regional Configuration

| Region | Priority | Replicas | DB Role | Cache Role |
|--------|----------|----------|---------|------------|
| us-east-1 | Primary | 3 | Primary (Write) | Primary |
| eu-west-1 | Secondary | 2 | Replica (Read) | Replica |
| me-south-1 | Secondary | 2 | Replica (Read) | Replica |

## Failover Strategy

1. **Database**: Aurora Global Database automatic failover (RTO < 1 min)
2. **Cache**: ElastiCache Global Datastore automatic promotion
3. **Application**: Istio locality-based load balancing with failover
4. **Traffic**: AWS Global Accelerator health-based routing

## Monitoring

- Prometheus + Thanos for global metrics aggregation
- Loki for centralized logging
- Jaeger for distributed tracing
- Grafana dashboards per region
