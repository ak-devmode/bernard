# 1 PBMC VPC System Map

> **VPC:** `vpc-016c6beb95c8bd6d6` | **Region:** ap-southeast-1 (Singapore) | **CIDR:** 10.10.0.0/16
> **Account:** 777086446426 | **Last updated:** 2026-03-28

---

## 1.1 Network Topology Overview

```
                        ┌─────────────────────────────────────────────────────────────────────────────┐
                        │  VPC: 10.10.0.0/16  (vpc-016c6beb95c8bd6d6)                                │
                        │                                                                             │
  ┌──────────┐          │  ┌─── Public Subnet 10.10.1.0/24 ──────────────────────────────────────┐   │
  │ Internet │◄────────►│  │                                                                     │   │
  │          │   IGW    │  │  alb-pbmc-public    alb-tm-prod-app    alb-tm-integration   NAT GW  │   │
  └──────────┘   igw-   │  │  (public sites)     (eKlinik prod)    (integrations)       18.142.  │   │
                 0bec..  │  │  sg: alb-pbmc-      sg: alb-his-      sg: alb-             12.57   │   │
                         │  │      public-sg          production-sg     integration-sg            │   │
                         │  └────────┬──────────────────┬───────────────────┬─────────────────────┘   │
                         │           │                  │                   │                          │
                         │  ┌────────▼──────────┐ ┌─────▼────────────┐ ┌───▼──────────────────┐      │
                         │  │ Webhost/Portal     │ │ Prod App         │ │ Staging App          │      │
                         │  │ 10.10.3.0/24       │ │ 10.10.4.0/24     │ │ 10.10.12.0/24        │      │
                         │  │                    │ │                  │ │                      │      │
                         │  │ pmg-prod-webhost   │ │ pmg-prod-app-tm  │ │ pmg-staging-app      │      │
                         │  │ 10.10.3.42 (t4g.L) │ │ 10.10.4.123     │ │ 10.10.12.90 (r5.xl)  │      │
                         │  │ sg: portal-app-sg  │ │ (r5.xlarge)     │ │ sg: staging-app-sg   │      │
                         │  │                    │ │ sg: production-  │ │                      │      │
                         │  │ pmg-prod-chatwoot  │ │     app-sg       │ │ 15_ProjectX_Padma    │      │
                         │  │ 10.10.3.112(t4g.M) │ │                  │ │ 10.10.12.187(stopped)│      │
                         │  │ sg: portal-app-sg  │ │                  │ │ sg: staging-app-sg   │      │
                         │  └────────────────────┘ └────────┬─────────┘ └──────────┬───────────┘      │
                         │                                  │                      │                   │
                         │                         ┌────────▼──────────┐ ┌─────────▼───────────┐      │
                         │                         │ Prod DB            │ │ Staging DB           │      │
                         │                         │ 10.10.6.0/24       │ │ 10.10.13.0/24        │      │
                         │                         │                    │ │                      │      │
                         │                         │ pmg-prod-db-tm     │ │ pmg-staging-db       │      │
                         │                         │ 10.10.6.109        │ │ 10.10.13.172         │      │
                         │                         │ (r5.xlarge)        │ │ (r5.xlarge)          │      │
                         │                         │ sg: production-    │ │ sg: staging-db-sg    │      │
                         │                         │     db-sg          │ │ 4x MySQL instances   │      │
                         │                         │ 4x MySQL instances │ │                      │      │
                         │                         └────────────────────┘ └──────────────────────┘      │
                         │                                                                             │
                         │  ┌─── VPN Subnet 10.10.15.0/24 ───────────────────────────────────────┐   │
  ┌──────────────┐       │  │                                                                     │   │
  │ VPN Clients  │◄─────►│  │  pmg-infra-openvpn                                                  │   │
  │ (remote)     │  1194  │  │  10.10.15.46 / EIP 52.221.215.105                                   │   │
  └──────────────┘       │  │  sg: Client-VPN-Sg       Routes 0.0.0.0/0 → IGW                     │   │
                         │  └─────────────────────────────────────────────────────────────────────┘   │
                         │                                                                             │
                         │  ┌─── Public Subnet 10.10.1.0/24 (bastion, stopped) ──────────────────┐   │
                         │  │  pmg-infra-bastion  10.10.1.250 (t2.micro, STOPPED)                 │   │
                         │  │  sg: jumphost                                                       │   │
                         │  └─────────────────────────────────────────────────────────────────────┘   │
                         │                                                                             │
                         │  Dormant: 10.10.2.0/24 (Public C), 10.10.5.0/24, 10.10.7.0/24             │
                         └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1.2 Subnets

| Subnet ID | CIDR | Name | Route Table | Default Route |
|-----------|------|------|-------------|---------------|
| `subnet-02f5a9a5d836974ef` | 10.10.1.0/24 | Subnet Public A | `rtb-051341102005a94f0` | IGW |
| `subnet-0651c357adfbaea66` | 10.10.2.0/24 | Subnet Public C (dormant) | `rtb-051341102005a94f0` | IGW |
| `subnet-0ba0c5af138413e4c` | 10.10.3.0/24 | Subnet Private Webhost A | `rtb-05c9a16c1c6507143` | NAT |
| `subnet-095491539c1cc3a18` | 10.10.4.0/24 | Subnet Private Production App A | `rtb-05c9a16c1c6507143` | NAT |
| `subnet-02cf1a3c3d6c6d5dd` | 10.10.5.0/24 | Subnet Private Unused 5 C | `rtb-03e8355fa0e9ae2d3` | NAT |
| `subnet-0348049c22bc029ba` | 10.10.6.0/24 | Subnet Private DB Production A | `rtb-05c9a16c1c6507143` | NAT |
| `subnet-0b2c280f8fac0f227` | 10.10.7.0/24 | Subnet Private unused 7 C | `rtb-03e8355fa0e9ae2d3` | NAT |
| `subnet-04fad726ddc6e5d04` | 10.10.12.0/24 | Subnet Private Staging App A | `rtb-05c9a16c1c6507143` | NAT |
| `subnet-0c99d81bbde55d6fa` | 10.10.13.0/24 | Subnet Private Staging Database A | `rtb-05c9a16c1c6507143` | NAT |
| `subnet-05bc9fc3f75c148d6` | 10.10.15.0/24 | Subnet-Private-VPN-Clients | `rtb-00fa96f83e24234e1` | IGW |

---

## 1.3 Route Tables

### 1.3.1 `rtb-051341102005a94f0` — Public subnets (10.10.1.0/24, 10.10.2.0/24)
| Destination | Target |
|-------------|--------|
| 10.10.0.0/16 | local |
| 0.0.0.0/0 | igw-0bec39fb7871659be |

### 1.3.2 `rtb-05c9a16c1c6507143` — Private app/db subnets (3, 4, 6, 12, 13)
| Destination | Target |
|-------------|--------|
| 10.10.0.0/16 | local |
| 100.96.0.0/11 | (VPN client CIDR) |
| 0.0.0.0/0 | nat-0189cac60a5a3e583 |

### 1.3.3 `rtb-00fa96f83e24234e1` — VPN subnet (10.10.15.0/24)
| Destination | Target |
|-------------|--------|
| 10.10.0.0/16 | local |
| 0.0.0.0/0 | igw-0bec39fb7871659be |

### 1.3.4 `rtb-03e8355fa0e9ae2d3` — Unused subnets (5, 7)
| Destination | Target |
|-------------|--------|
| 10.10.0.0/16 | local |
| 0.0.0.0/0 | nat-0189cac60a5a3e583 |

---

## 1.4 Gateways

| Resource | ID | Details |
|----------|----|---------|
| Internet Gateway | `igw-0bec39fb7871659be` | VPC-PBMC-IGW |
| NAT Gateway | `nat-0189cac60a5a3e583` | Subnet Public A, EIP **18.142.12.57**, private 10.10.1.249 |

---

## 1.5 EC2 Instances

| Name | Instance ID | Private IP | Public IP | Type | State | Subnet | SG |
|------|-------------|------------|-----------|------|-------|--------|----|
| pmg-infra-openvpn | `i-0f106dccc8d087fd0` | 10.10.15.46 | 52.221.215.105 | t3.medium | running | 10.10.15.0/24 | Client-VPN-Sg |
| pmg-prod-app-tm | `i-0ed02aee47c5160fa` | 10.10.4.123 | — | r5.xlarge | running | 10.10.4.0/24 | production-app-sg |
| pmg-staging-app | `i-0dc21e5a90328797e` | 10.10.12.90 | — | r5.xlarge | running | 10.10.12.0/24 | staging-app-sg |
| pmg-prod-db-tm | `i-000049a147a7e1c24` | 10.10.6.109 | — | r5.xlarge | running | 10.10.6.0/24 | production-db-sg |
| pmg-staging-db | `i-09ee28108d1666fb1` | 10.10.13.172 | — | r5.xlarge | running | 10.10.13.0/24 | staging-db-sg |
| pmg-prod-chatwoot | `i-053b3845a7aa0850d` | 10.10.3.112 | — | t4g.medium | running | 10.10.3.0/24 | portal-app-sg |
| pmg-prod-webhost | `i-0d508d2d8912a00e5` | 10.10.3.42 | — | t4g.large | running | 10.10.3.0/24 | portal-app-sg |
| pmg-infra-bastion | `i-00b9fd2f93a192e3c` | 10.10.1.250 | — | t2.micro | **stopped** | 10.10.1.0/24 | jumphost |
| 15_ProjectX_Padma | `i-0d70f15d221965a3c` | 10.10.12.187 | — | r5.xlarge | **stopped** | 10.10.12.0/24 | staging-app-sg |

---

## 1.6 Application Load Balancers

### 1.6.1 `alb-pbmc-public` — Public websites & Chatwoot
- **Scheme:** internet-facing
- **SG:** `alb-pbmc-public-sg` (`sg-0fda4fa1994aef24a`) — open 80/443 from 0.0.0.0/0
- **Listeners:** HTTP 80 → redirect to HTTPS | HTTPS 443 → host-based routing

| Priority | Host | Target Group | Port | Target |
|----------|------|-------------|------|--------|
| 2 | chat.pbmcgroup.com | chat-production | 3002 | pmg-prod-chatwoot |
| 4 | whatsapp.pbmcgroup.com | whatsapp-router | 3000 | pmg-prod-chatwoot |
| 5 | pbmcgroup.com | pmg-prod-webhost | 80 | pmg-prod-webhost |
| 7 | www.pbmcgroup.com | pmg-prod-webhost | 80 | pmg-prod-webhost |
| 9 | staging-chat.pbmcgroup.com | tg-chatwoot-staging | 3001 | pmg-prod-chatwoot |
| 29 | dashboard.pbmcgroup.com | pmg-dashboard-webhost-3000 | 3000 | pmg-prod-webhost |
| 50 | whatsapp.pbmcgroup.com/webhook | pmg-webhook-dlq | Lambda | — |
| default | * | pmg-prod-webhost | 80 | pmg-prod-webhost |

### 1.6.2 `alb-tm-prod-app` — eKlinik Production (HIS)
- **Scheme:** internet-facing
- **SG:** `alb-his-production-sg` (`sg-050e16a5bb409521e`) — IP-whitelisted (see 1.7.2)
- **Listeners:** HTTP 80 → forward | HTTPS 443 → host-based routing

| Priority | Host | Target Group | Port | Target |
|----------|------|-------------|------|--------|
| 10 | staging-eklinik.pbmcgroup.com | alb-tm-staging-app | 4002 | pmg-staging-app |
| 20 | projectx.pbmcgroup.com | projectX | 80 | pmg-staging-app |
| default | (eklinik.pbmcgroup.com) | alb-tm-prod | 4002 | pmg-prod-app-tm |

### 1.6.3 `alb-tm-integration` — Integration APIs
- **Scheme:** internet-facing
- **SG:** `alb-integration-sg` (`sg-0121f622359fe5caf`) — open 443 from 0.0.0.0/0
- **Listeners:** HTTPS 443 → host-based routing

| Priority | Host | Target Group | Port | Target |
|----------|------|-------------|------|--------|
| 5 | integrations.pbmcgroup.com | pmg-integrations | 3012 | pmg-prod-webhost |
| 10 | staging-integration-eklinik.pbmcgroup.com | tg-integration-tm-staging | 4010 | pmg-staging-app |
| 20 | api-projectx.pbmcgroup.com | api-projectX | 9002 | pmg-staging-app |
| default | (integration-eklinik.pbmcgroup.com) | tg-tm-integration-prod | 4010 | pmg-prod-app-tm |

---

## 1.7 Security Groups

### 1.7.1 `Client-VPN-Sg` (`sg-034506ce2ba937820`)
**Attached to:** pmg-infra-openvpn (10.10.15.46)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | 0.0.0.0/0 | all SSH |
| 22 | TCP | 100.96.0.0/12 | VPN client CIDR |
| 80 | TCP | 0.0.0.0/0 | all HTTP |
| 443 | TCP | 0.0.0.0/0 | all HTTPS |
| 8443 | TCP | 0.0.0.0/0 | production app access |
| ICMP | ICMP | 0.0.0.0/0 | ping |

**Egress:** All traffic (0.0.0.0/0)

### 1.7.2 `alb-his-production-sg` (`sg-050e16a5bb409521e`)
**Attached to:** alb-tm-prod-app

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 80 | TCP | 103.225.151.144/29 | PBMC Bali Whitelist |
| ~~80~~ | ~~TCP~~ | ~~18.142.12.57/32~~ | ~~Removed 2026-03-28 — unnecessary, backend doesn't call own ALB~~ |
| 80 | TCP | 52.221.215.105/32 | OpenVPN server public IP - VPN user access |
| 80 | TCP | 10.10.15.0/24 | VPN subnet - direct access |
| 80 | TCP | 203.210.87.87/32 | TM remote access (SBY) |
| 80 | TCP | 203.210.87.88/32 | TM remote access (SBY) |
| 80 | TCP | 203.210.87.89/32 | TM remote access (SBY) |
| 80 | TCP | 103.117.205.112/30 | SBY Maxindo ISP |
| 443 | TCP | 103.225.151.144/29 | PBMC Bali Whitelist |
| ~~443~~ | ~~TCP~~ | ~~18.142.12.57/32~~ | ~~Removed 2026-03-28 — unnecessary, backend doesn't call own ALB~~ |
| 443 | TCP | 54.251.203.204/32 | NAT gateway (Integration account) |
| 443 | TCP | 52.221.215.105/32 | OpenVPN server public IP - VPN user access |
| 443 | TCP | 10.10.15.0/24 | VPN subnet - direct access (frontend) |
| 443 | TCP | 203.210.87.87/32 | TM remote access (SBY) |
| 443 | TCP | 203.210.87.88/32 | TM remote access (SBY) |
| 443 | TCP | 203.210.87.89/32 | TM remote access (SBY) |
| 443 | TCP | 103.117.205.112/30 | SBY Maxindo ISP |
| ICMP | ICMP | 54.251.203.204/32 | Integration NAT ping |

### 1.7.3 `production-app-sg` (`sg-057af43651da1a4de`)
**Attached to:** pmg-prod-app-tm (10.10.4.123)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Client-VPN-Sg | SSH from VPN |
| 443 | TCP | alb-his-production-sg | TLS from prod ALB |
| 443 | TCP | Client-VPN-Sg | TLS from VPN |
| 443 | TCP | alb-integration-sg | TLS from integration ALB |
| 3306 | TCP | production-db-sg | MySQL from DB |
| 4002 | TCP | alb-his-production-sg | App port from prod ALB |
| 4002 | TCP | Client-VPN-Sg | App port from VPN |
| 4010 | TCP | Client-VPN-Sg | Integration port from VPN (LIS) |
| 4010 | TCP | alb-integration-sg | Integration from ALB |
| 8001-8003 | TCP | production-db-sg | App access from DB |
| 8001-8003 | TCP | Client-VPN-Sg | App access from VPN |
| ICMP | ICMP | 10.10.0.0/20 | Ping within VPC |

**Egress:**
| Port | Protocol | Destination | Description |
|------|----------|-------------|-------------|
| 53 | TCP/UDP | 0.0.0.0/0 | DNS |
| 80 | TCP | 0.0.0.0/0 | HTTP |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 1024-65535 | TCP | 0.0.0.0/0 | Ephemeral ports |
| 1433 | TCP | 10.10.6.0/24, 10.10.7.0/24 | MSSQL to DB subnets |
| 9462 | TCP | 0.0.0.0/0 | Custom |
| All | All | 0.0.0.0/0 | Open all |

### 1.7.4 `production-db-sg` (`sg-085853354d11adf36`)
**Attached to:** pmg-prod-db-tm (10.10.6.109)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Client-VPN-Sg | SSH from VPN |
| 3306 | TCP | production-app-sg | MySQL from prod app |
| 8001-8003 | TCP | production-app-sg | App access from prod app |
| ICMP | ICMP | 10.10.0.0/20 | Ping within VPC |

### 1.7.5 `staging-app-sg` (`sg-09bdb37860c0d72ce`)
**Attached to:** pmg-staging-app (10.10.12.90), 15_ProjectX_Padma (10.10.12.187)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Client-VPN-Sg | SSH from VPN |
| 443 | TCP | Client-VPN-Sg | TLS from VPN |
| 443 | TCP | staging-db-sg | TLS from staging DB |
| 3306 | TCP | staging-db-sg | MySQL from staging DB |
| 4002 | TCP | Client-VPN-Sg | App port from VPN |
| 4002 | TCP | alb-his-production-sg | App port from prod ALB |
| 4010 | TCP | Client-VPN-Sg | Integration from VPN |
| 4010 | TCP | alb-integration-sg | Integration from ALB |
| 8001-8003 | TCP | staging-db-sg | DB access TM |
| 8001-8003 | TCP | Client-VPN-Sg | App access from VPN |
| 8401-8403 | TCP | staging-db-sg | DB access control TM |
| 9001 | TCP | alb-his-production-sg | ProjectX from prod ALB |
| 9002 | TCP | alb-integration-sg | ProjectX API from integration ALB |
| ICMP | ICMP | 10.10.0.0/20 | Ping within VPC |

### 1.7.6 `staging-db-sg` (`sg-02d05064d4a6e6a22`)
**Attached to:** pmg-staging-db (10.10.13.172)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Client-VPN-Sg | SSH from VPN |
| 3306 | TCP | staging-app-sg | MySQL from staging app |
| 8401-8403 | TCP | staging-app-sg | TM DB access control |
| ICMP | ICMP | 10.10.0.0/20 | Ping from VPC |

### 1.7.7 `alb-pbmc-public-sg` (`sg-0fda4fa1994aef24a`)
**Attached to:** alb-pbmc-public

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 80 | TCP | 0.0.0.0/0 | Public HTTP |
| 443 | TCP | 0.0.0.0/0 | Public HTTPS |

**Egress:** All traffic (0.0.0.0/0)

### 1.7.8 `alb-integration-sg` (`sg-0121f622359fe5caf`)
**Attached to:** alb-tm-integration

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 443 | TCP | 0.0.0.0/0 | HTTPS from internet |

**Egress:** All traffic (0.0.0.0/0)

### 1.7.9 `portal-app-sg` (`sg-01dfbe31fddf69ba1`)
**Attached to:** pmg-prod-chatwoot (10.10.3.112), pmg-prod-webhost (10.10.3.42)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | Client-VPN-Sg | SSH from VPN |
| 80 | TCP | Client-VPN-Sg | HTTP from VPN (testing) |
| 80 | TCP | alb-pbmc-public-sg | HTTP from public ALB |
| 443 | TCP | alb-pbmc-public-sg | HTTPS from public ALB |
| 3000 | TCP | alb-pbmc-public-sg | WhatsApp router from ALB |
| 3001 | TCP | alb-pbmc-public-sg | Chatwoot staging from ALB |
| 3002 | TCP | alb-pbmc-public-sg | Chatwoot production from ALB |
| 3012 | TCP | alb-integration-sg | padma-integrations from integration ALB |
| ICMP | ICMP | 10.10.0.0/20 | Ping within VPC |

### 1.7.10 `jumphost` (`sg-0b64c38d3b404a222`)
**Attached to:** pmg-infra-bastion (10.10.1.250, STOPPED)

**Ingress:**
| Port | Protocol | Source | Description |
|------|----------|--------|-------------|
| 22 | TCP | 139.255.22.211/32 | Alex personal IP |

---

## 1.8 Traffic Flow Reference

### 1.8.1 VPN User → eKlinik Production (eklinik.pbmcgroup.com)
```
Laptop → OpenVPN (10.10.15.46) → IGW → ALB public IP
     source: 52.221.215.105
     ALB SG: allows 52.221.215.105 ✓
     ALB forwards :443 → 10.10.4.123:4002
     Prod App SG: allows from alb-his-production-sg ✓
```

### 1.8.2 VPN User → eKlinik Direct (bypass ALB)
```
Laptop → OpenVPN (10.10.15.46) → local route → 10.10.4.123:8001
     source SG: Client-VPN-Sg
     Prod App SG: allows 8001-8003 from Client-VPN-Sg ✓
```

### 1.8.3 On-site Staff → eKlinik Production
```
Clinic PC → ISP (103.225.151.144/29) → ALB public IP
     ALB SG: allows PBMC Bali whitelist ✓
     ALB forwards :443 → 10.10.4.123:4002
```

### 1.8.4 Private Subnet → Internet (app updates, API calls)
```
EC2 (10.10.4.x) → NAT GW (10.10.1.249) → IGW → Internet
     source: 18.142.12.57
```

### 1.8.5 Public Internet → Chatwoot / Website
```
Browser → ALB (alb-pbmc-public) :443
     ALB SG: allows 0.0.0.0/0 ✓
     Host routing → target group → pmg-prod-chatwoot or pmg-prod-webhost
```

---

## 1.9 DNS → ALB Mapping

| Domain | ALB | Notes |
|--------|-----|-------|
| pbmcgroup.com | alb-pbmc-public | Corporate website |
| www.pbmcgroup.com | alb-pbmc-public | Corporate website |
| chat.pbmcgroup.com | alb-pbmc-public | Chatwoot production |
| staging-chat.pbmcgroup.com | alb-pbmc-public | Chatwoot staging |
| whatsapp.pbmcgroup.com | alb-pbmc-public | WhatsApp webhook router |
| dashboard.pbmcgroup.com | alb-pbmc-public | Grafana dashboard |
| eklinik.pbmcgroup.com | alb-tm-prod-app | eKlinik production (HIS) |
| staging-eklinik.pbmcgroup.com | alb-tm-prod-app | eKlinik staging |
| projectx.pbmcgroup.com | alb-tm-prod-app | ProjectX frontend |
| integration-eklinik.pbmcgroup.com | alb-tm-integration | eKlinik integration API (prod) |
| staging-integration-eklinik.pbmcgroup.com | alb-tm-integration | eKlinik integration API (staging) |
| integrations.pbmcgroup.com | alb-tm-integration | PMG integrations service |
| api-projectx.pbmcgroup.com | alb-tm-integration | ProjectX API |

---

## 1.10 IP Address Quick Reference

| IP | Type | Resource |
|----|------|----------|
| 52.221.215.105 | EIP | OpenVPN server (outbound VPN traffic) |
| 18.142.12.57 | EIP | NAT Gateway (outbound private subnet traffic) |
| 54.251.203.204 | EIP | Integration account NAT (cross-account) |
| 103.225.151.144/29 | Static | PBMC Bali office ISP |
| 203.210.87.87-89 | Static | TM Surabaya remote access |
| 103.117.205.112/30 | Static | SBY Maxindo ISP |
| 139.255.22.211 | Static | Alex personal IP (bastion SSH) |
| 100.96.0.0/12 | VPN CIDR | OpenVPN client address pool |

---

## 1.11 Application Ports

### 1.11.1 eKlinik TM (pmg-prod-app-tm / pmg-staging-app)

| Port | Service | Notes |
|------|---------|-------|
| 4002 | eKlinik main app | ALB target port (prod & staging) |
| 4010 | eKlinik integration API | LIS, external system integrations |
| 8001 | User frontend | Direct access port |
| 8002 | TBD | Mapped in SG but undocumented |
| 8003 | TBD | Mapped in SG but undocumented |
| 8401-8403 | Staging DB access | Staging-only access control ports |
| 9001 | ProjectX frontend | Via prod ALB |
| 9002 | ProjectX API | Via integration ALB |

### 1.11.2 Chatwoot & Router (pmg-prod-chatwoot — 10.10.3.112)

| Port | Service | Notes |
|------|---------|-------|
| 3000 | WhatsApp webhook router | Node.js service (pmg-router), receives Meta webhooks |
| 3001 | Chatwoot staging web | Rails app (internal :3000 → exposed :3001) |
| 3002 | Chatwoot production web | Rails app (internal :3000 → exposed :3002) |

### 1.11.3 Webhost & Integrations (pmg-prod-webhost — 10.10.3.42)

| Port | Service | Notes |
|------|---------|-------|
| 80 | Corporate website | pbmcgroup.com, www.pbmcgroup.com |
| 3000 | Grafana dashboard | dashboard.pbmcgroup.com |
| 3012 | Padma integrations service | integrations.pbmcgroup.com, via integration ALB |

---

## 1.12 Changelog

| Date | Change | Reason |
|------|--------|--------|
| 2026-03-28 | Added `52.221.215.105/32` to `alb-his-production-sg` (80, 443) | VPN users couldn't reach eKlinik after VPN subnet moved from NAT to IGW routing |
| 2026-03-28 | Replaced stale `10.10.14.0/24` with `10.10.15.0/24` in `alb-his-production-sg` (80, 443) | Wrong VPN subnet CIDR (14 vs 15) — 10.10.14.0/24 was never the active VPN subnet |
| 2026-03-28 | Removed `18.142.12.57/32` (NAT GW) from `alb-his-production-sg` (80, 443) | Unnecessary — backend instances behind this ALB don't call their own ALB by hostname |
