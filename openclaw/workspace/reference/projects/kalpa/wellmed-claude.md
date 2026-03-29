# Project: WellMed Clinic Management System

## Overview
WellMed is a healthcare clinic management system serving Indonesian clinics with SATU SEHAT government integration.

## Tech Stack
- **Backend**: Node.js with Express, TypeScript
- **Database**: PostgreSQL with Prisma ORM
- **Frontend**: Next.js 14 with App Router
- **Infrastructure**: AWS (ECS, RDS, VPC)
- **Queue**: AWS SQS for async tasks
- **Cache**: Redis for session management

## Project Structure
```
src/
├── api/           # Express routes and controllers
├── services/      # Business logic layer
├── repositories/  # Data access layer
├── integrations/  # External API integrations (SATU SEHAT, etc.)
├── queue/         # SQS job processors
└── utils/         # Shared utilities
```

## Go Conventions

### Module Naming
- All Go module paths and GitHub repo references **must be fully lowercase**: `github.com/kalpa-health/repo-name`
- Mixed-case paths (e.g. `github.com/Kalpa-Health/...`) cause Go import resolution failures — Go module paths are case-sensitive and the toolchain normalizes to lowercase
- This applies to `go.mod` module declarations, all `import` statements, and any docs or config referencing Go package paths

## Code Conventions

### TypeScript
- Use strict mode always
- Prefer `interface` over `type` for object shapes
- Use Zod for runtime validation
- No `any` types - use `unknown` and narrow

### Naming
- Files: `kebab-case.ts`
- Classes: `PascalCase`
- Functions/variables: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE`
- Database tables: `snake_case`

### Error Handling
- Use custom error classes extending `AppError`
- Always include error codes for API responses
- Log errors with structured JSON (pino)

### Testing
- Unit tests: `*.test.ts` colocated with source
- Integration tests: `__tests__/integration/`
- Use Vitest, not Jest
- Minimum 80% coverage for new code

## SATU SEHAT Integration

### Critical Notes
- All patient data must include NIK (national ID)
- Use staging environment for development: `https://api-satusehat-stg.kemkes.go.id`
- OAuth tokens expire in 1 hour - implement refresh logic
- Bundle submissions have strict validation - test locally first

### Environment Variables
Required for SATU SEHAT:
- `SATUSEHAT_CLIENT_ID`
- `SATUSEHAT_CLIENT_SECRET`
- `SATUSEHAT_ORG_ID`

## Common Commands
```bash
# Development
pnpm dev              # Start dev server
pnpm db:migrate       # Run migrations
pnpm db:seed          # Seed test data

# Testing
pnpm test             # Run all tests
pnpm test:coverage    # With coverage report

# Deployment
pnpm build            # Production build
pnpm db:migrate:prod  # Production migrations
```

