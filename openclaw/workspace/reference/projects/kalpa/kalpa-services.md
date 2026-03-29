# Kalpa Services - Project Context

## Company
Kalpa Inovasi Digital - Indonesian healthcare technology startup (5 employees)

## Product
WellMed Backend Services - microservices powering WellMed Clinic OS

## Tech Stack
- **Languages**: Go (new services), PHP/Laravel (legacy), Node.js
- **Communication**: REST primary, gRPC/Protobuf for internal high-perf calls
- **Database**: PostgreSQL
- **Instance types**: m5.large (consistent performance for APIs)

## Architecture
Migrating monolithic Laravel → microservices:
- Move modules 1-at-a-time as microservices
- Adaptive layer between frontend/backend for shared resources
- Single communication framework per module (inbound/outbound)
- Gateway service in Go handles routing

## Shared Proto Definitions
Cross-service data contracts in Protocol Buffers:
- `patient.proto` - Indonesian-specific fields (NIK, kelurahan, etc.)
- `visit.proto` - Visit status, diagnosis (ICD10), prescriptions
- `bill.proto` - Line items, payment status, insurance

Repository pattern: `github.com/kalpa-inovasi/wellmed-protos`

## Key Services
- **Gateway**: Go, handles auth/routing/rate-limiting
- **Patient Service**: Patient records, demographics
- **Visit Service**: Encounters, diagnoses, prescriptions
- **Billing Service**: Invoicing, payment tracking
- **SATU SEHAT Bridge**: FHIR resource transformation, API proxy

## FHIR/SATU SEHAT Integration
- MedicationStatement - individual per medication (no grouper like DiagnosticReport)
- Required fields: Patient ref, Medication CodeableConcept, status
- Indonesian extensions: KFA codes, IHS numbers
- Encounters: Must include all FHIR R4 expected elements

## Performance Targets
- 40-50 concurrent users current
- Scaling to 200 → 400 → 600 users planned
- Connection pooling critical before 400 users
- Session management via Redis (already deployed)

## Infrastructure
- AWS Singapore (primary)
- Multi-AZ deployment
- r5.large for PostgreSQL (memory-optimized)
- m5.large for services (consistent CPU)

## Development Practices
- All internal docs in Bahasa Indonesia
- Compliance/audit logging critical
- SDLC culture building in progress
