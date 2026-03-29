# Kalpa Frontend - Project Context

## Company
Kalpa Inovasi Digital - Indonesian healthcare technology startup

## Product
WellMed Clinic Management System (Clinic OS)
- **WellMed Lite**: Small clinics, basic features
- **WellMed Plus**: Medium clinics, full feature set
- **WellMed Enterprise**: Large/multi-location, SATU SEHAT compliant

## Core Design Philosophy
- "3-click rule" - any action within 3 clicks
- Practitioner-built software (17+ years clinic experience)
- Dramatic performance focus: 11min → 5sec patient visit workflows

## Tech Stack
- **Framework**: Nuxt.js (SSR)
- **Hosting**: AWS Singapore, CloudFront CDN
- **Instance**: t3.medium/large (burstable - appropriate for bursty web traffic)
- **Scaling**: Vertical first (3x t3.large handles ~1000 users before horizontal)

## Architecture Pattern
```
Internet → CloudFront (Jakarta edge) → ALB → Frontend (Singapore)
                                              ↓
                                         Backend APIs
```

Frontend serves as DMZ layer:
- Handles external traffic/attacks
- Backend microservices remain isolated
- WAF/rate limiting at single endpoint
- Independent scaling from backend

## Key Integrations
- Backend via REST/gRPC
- SATU SEHAT compliance UI workflows
- Jakarta proxy for Indonesian IP compliance

## Current Focus Areas
- UI/UX refinements for Indonesian clinic workflows
- Performance optimization
- Multi-tenant architecture
- Mobile responsiveness

## Working Preferences
- Scripts must print verbose per-item progress
- On Mac: use pip3/python3 commands
- Prefer practical solutions over theoretical
