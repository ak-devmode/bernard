# Kalpa Infrastructure - Project Context

## Company
Kalpa Inovasi Digital - Indonesian healthcare technology startup
Alex Knecht: Founder & Infrastructure Lead

## AWS Architecture

### Multi-VPC Setup
- **Production VPC**: Singapore (primary)
- **Dev/Staging VPC**: Singapore
- **Jakarta Proxy**: Minimal footprint for SATU SEHAT compliance

### Instance Strategy
| Layer | Type | Rationale |
|-------|------|-----------|
| Frontend | t3.medium/large | Burstable, web traffic is naturally bursty |
| Backend | m5.large | Consistent performance for APIs |
| Database | r5.large | Memory-optimized for PostgreSQL |
| VPN | t3.small | Sporadic admin access |
| Jakarta Proxy | t3.micro | Minimal compliance footprint |

### Networking
- **OpenVPN CloudConnexa** for admin access
- **ALB** in front of services
- **CloudFront** for Indonesian edge presence (Jakarta)
- Cross-account DNS management
- SSL certificates via ACM for kalpahealth.com

### Compliance Architecture
```
Indonesian Users → CloudFront (Jakarta Edge) → Singapore Origin
                          ↓
                   Jakarta Proxy → SATU SEHAT APIs
```
- Private operators can process/store offshore with proper monitoring
- CloudFront provides Indonesian IP presence
- Jakarta proxy handles only SATU SEHAT integration

## SATU SEHAT Compliance
- Registration complete but FSO vendor selection tool gap
- Contact: Aang Jatnika (Platform Onboarding Head)
- Playbook: https://satusehat.kemkes.go.id/platform/docs/id/playbook/
- Postman: https://www.postman.com/satusehat/satusehat-public/overview
- Targeting 100% compliance with SS roadmap
- Padma Bahtera as live lab workbench

## Cost Structure
- Current: ~$600/month baseline
- Phase 1 (200 users): ~$640/month
- Phase 2 (400 users): ~$840/month (add RDS)
- Phase 3 (600 users): ~$1,000/month
- S3 growth: ~10GB per 100 users per year

## Scaling Triggers
- CPU >70% sustained → scale up
- Redis memory >80% → scale up
- DB connections approaching limit → move to RDS Multi-AZ
- 400+ users → connection pooling architecture

## Key Technical Decisions
- Singapore bias justified: better connectivity, regulatory compliant for private operators
- Self-managed PostgreSQL acceptable until 400 users
- Go migration improves concurrency handling (no session limitations)
- Redis for sessions already in baseline

## Security
- VPC Flow Logs for audit trails
- WAF in front of ALB
- Secrets Manager for credentials
- IAM roles (not access keys)
- MFA for admin access

## BAZNAS Opportunity
- 32-clinic government contract
- Self-hosted deployment
- Separate from SaaS infrastructure
