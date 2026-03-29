# WellMed Saga Framework PRD
## Version 1.0 | January 2025

---

## Document Purpose

This PRD defines the design and implementation plan for WellMed's Saga Framework - a pattern for maintaining data consistency across microservices. This framework will support the migration from Laravel Lite to Go microservices and scale to support Plus and Enterprise tiers.

**Owner:** Hamzah (CTO)  
**Priority:** Critical path for Lite migration  
**Status:** Draft for team review

---

## 1. Problem Statement

### 1.1 The Challenge

WellMed is migrating from a Laravel monolith (Lite) to a Go microservices architecture. In the monolith, operations like "create visit" were single database transactions. In microservices, the same operation spans multiple services with separate databases:

```
Create Visit (Monolith)          Create Visit (Microservices)
─────────────────────────        ────────────────────────────
Single DB Transaction            EMR Service (emr schema)
  └── visits table                   └── visits table
  └── billing_accounts table     Cashier Service (cashier schema)
                                     └── billing_accounts table
                                 
                                 NO SHARED TRANSACTION POSSIBLE
```

If the Cashier service fails after EMR succeeds, we have inconsistent state.

### 1.2 Known Pain Point

In the previous Laravel iteration, sequential visit creation steps caused UX issues - staff had to wait for all downstream operations (billing setup, notifications, etc.) before seeing the patient in queue. This delay is unacceptable for clinic workflow.

### 1.3 Requirements

1. **Data consistency** across services without distributed transactions
2. **Immediate UI feedback** - patient visible in queue before all operations complete
3. **Compensation capability** - ability to undo operations (technical failures + business cancellations)
4. **24-hour cancellation window** - visits can be cancelled until real services are rendered
5. **Blocking rules** - once diagnostics/services are performed, cancellation is blocked

---

## 2. Solution: Hybrid Sync/Async Saga Pattern

### 2.1 Pattern Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  SYNC PHASE (user waits)                                        │
│  ─────────────────────────────────────────────────────────────  │
│  • Critical operations that must complete before response       │
│  • Patient/staff visibility (queue entry)                       │
│  • Saga state persisted to Redis                                │
│                                                                 │
│  HTTP 200 returned to user                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ASYNC PHASE (background)                                       │
│  ─────────────────────────────────────────────────────────────  │
│  • Non-critical operations                                      │
│  • External system sync (Satu Sehat, Jurnal)                    │
│  • Notifications                                                │
│  • Retries on failure                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  24-HOUR CANCELLATION WINDOW                                    │
│  ─────────────────────────────────────────────────────────────  │
│  • Saga state retained in Redis                                 │
│  • Manual cancellation possible if no blocking activities       │
│  • After 24h or blocking activity: saga state archived/flushed  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Compensation Types

| Type | Trigger | Timing | Example |
|------|---------|--------|---------|
| **Technical** | System failure mid-saga | Immediate, automatic | Cashier fails → rollback EMR |
| **Business** | User requests cancellation | Manual, within 24h window | Admin cancels visit created in error |

### 2.3 Blocking Activities

Once certain activities occur, the saga cannot be compensated:

| Activity | Why It Blocks |
|----------|---------------|
| Lab sample collected | Real cost incurred |
| Diagnostic performed | Doctor time spent |
| Consultation started | Service rendered |
| Medication dispensed | Inventory consumed |
| Payment processed | Money moved |

---

## 3. Scope: Lite Tier Sagas

For the initial Lite migration, we need 5 sagas:

### 3.1 Saga Definitions

| # | Saga | Services | Sync Steps | Async Steps |
|---|------|----------|------------|-------------|
| 1 | **Create Visit** | EMR + Cashier | Create visit record, init billing account | (Future: notifications) |
| 2 | **Complete Visit** | EMR + Cashier | Update status, finalize charges | Satu Sehat Encounter sync |
| 3 | **Cancel Visit** | EMR + Cashier | Compensation: reverse visit + billing | Satu Sehat status update |
| 4 | **Process Payment** | Cashier + Jurnal | Create payment record | Jurnal posting |
| 5 | **Create Staff User** | Backbone + EMR | Create user, create practitioner | Satu Sehat Practitioner sync |

### 3.2 Future Sagas (Plus/Enterprise)

The framework must support future expansion:

| Tier | Sagas |
|------|-------|
| **Plus** | Dispense Medication, Order Lab, Record Lab Result, Order Imaging, Record Imaging Result, Book/Cancel Appointment |
| **Enterprise** | Admit/Discharge/Transfer Inpatient, MCU Package, Inventory Restock |
| **Infrastructure** | EOD Reconciliation, Credential Rotation, Master Data Sync |

---

## 4. Technical Design

### 4.1 Core Interfaces

```go
// Step represents a single operation in a saga
type Step interface {
    Name() string
    Execute(ctx context.Context, state *SagaState) error
    Compensate(ctx context.Context, state *SagaState) error
}

// SagaDefinition defines the structure of a saga type
type SagaDefinition struct {
    Name          string
    SyncSteps     []Step           // Must complete before response
    AsyncSteps    []Step           // Background processing
    BlockingRules []BlockingRule   // What prevents cancellation
    TTL           time.Duration    // Cancellation window (default 24h)
}

// Orchestrator manages saga execution
type Orchestrator interface {
    // Execute runs sync steps, persists state, queues async steps
    Execute(ctx context.Context, sagaType string, input any) (result any, sagaID string, err error)
    
    // Cancellation
    CanCancel(sagaID string) (bool, string)
    Cancel(ctx context.Context, sagaID string) error
    
    // Called by services when blocking activities occur
    AddBlockingActivity(sagaID string, activity Activity) error
    
    // Called by async worker
    ContinueAsync(sagaID string) error
}
```

### 4.2 State Storage (Redis)

```go
type SagaState struct {
    ID                 string              `json:"id"`
    Type               string              `json:"type"`      // "create_visit", etc.
    Status             SagaStatus          `json:"status"`    // pending|active|locked|completed|compensated
    Input              json.RawMessage     `json:"input"`
    Output             json.RawMessage     `json:"output"`    // Result from sync phase
    
    // Tracking
    CompletedSteps     []CompletedStep     `json:"completed_steps"`
    PendingAsyncSteps  []string            `json:"pending_async_steps"`
    BlockingActivities []Activity          `json:"blocking_activities"`
    
    // Tracing (X-Ray)
    TraceID            string              `json:"trace_id"`
    ParentID           string              `json:"parent_id"`
    
    // Timing
    CreatedAt          time.Time           `json:"created_at"`
    ExpiresAt          time.Time           `json:"expires_at"`
}

type SagaStatus string
const (
    SagaStatusPending     SagaStatus = "pending"      // Created, not started
    SagaStatusActive      SagaStatus = "active"       // In progress, can cancel
    SagaStatusLocked      SagaStatus = "locked"       // Has blocking activities
    SagaStatusCompleted   SagaStatus = "completed"    // Finished successfully
    SagaStatusCompensated SagaStatus = "compensated"  // Rolled back
    SagaStatusFailed      SagaStatus = "failed"       // Failed, needs attention
)

type CompletedStep struct {
    Name        string          `json:"name"`
    CompletedAt time.Time       `json:"completed_at"`
    Result      json.RawMessage `json:"result"`  // For compensation context
}

type Activity struct {
    Type        string    `json:"type"`
    ID          string    `json:"id"`
    Description string    `json:"description"`
    RecordedAt  time.Time `json:"recorded_at"`
}
```

### 4.3 Package Structure

```
saga/
├── orchestrator.go      // Main orchestrator implementation
├── store.go             // Redis persistence layer
├── worker.go            // Async step processor (RabbitMQ consumer)
├── types.go             // Saga, Step, Activity structs
├── registry.go          // Saga definition registry
│
├── definitions/         // Saga definitions by domain
│   ├── visit.go         // Create, Complete, Cancel Visit
│   ├── payment.go       // Process Payment
│   └── user.go          // Create Staff User
│
└── steps/               // Reusable step implementations
    ├── emr/
    │   ├── create_visit.go
    │   └── update_visit_status.go
    ├── cashier/
    │   ├── init_billing.go
    │   └── finalize_charges.go
    └── external/
        └── satu_sehat_sync.go
```

### 4.4 Flow Example: Create Visit

```
API Request: POST /visits
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Gateway                                                         │
│  └── Identifies as saga-eligible operation                      │
│  └── Calls Orchestrator.Execute("create_visit", input)          │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator.Execute (SYNC PHASE)                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Generate saga ID                                            │
│  2. Create initial SagaState in Redis (status: pending)         │
│  3. Execute sync steps sequentially:                            │
│     a. CreateVisitStep.Execute() → EMR service                  │
│        └── On success: record in CompletedSteps                 │
│        └── On failure: compensate completed steps, return error │
│     b. InitBillingStep.Execute() → Cashier service              │
│        └── On success: record in CompletedSteps                 │
│        └── On failure: compensate CreateVisit, return error     │
│  4. Update SagaState (status: active, async steps pending)      │
│  5. Publish to async queue: "saga:continue:{saga_id}"           │
│  6. Return result + saga_id to Gateway                          │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  HTTP 200 Response (patient now visible in queue)               │
└─────────────────────────────────────────────────────────────────┘

        ┌───────────────────────────────────────────┐
        │  Meanwhile, async worker picks up job...  │
        └───────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Saga Worker (ASYNC PHASE)                                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Load SagaState from Redis                                   │
│  2. Execute async steps:                                        │
│     a. NotifyStep.Execute() → Send notifications                │
│        └── On failure: log, retry later (non-critical)          │
│  3. Update SagaState (all async steps complete)                 │
│  4. Saga remains in Redis for 24h cancellation window           │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 Compensation Flow

```
API Request: POST /visits/{id}/cancel
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator.CanCancel(sagaID)                                 │
├─────────────────────────────────────────────────────────────────┤
│  1. Load SagaState from Redis                                   │
│  2. Check: state != nil (within 24h window)                     │
│  3. Check: len(BlockingActivities) == 0                         │
│  4. Return (true, "") or (false, "reason")                      │
└─────────────────────────────────────────────────────────────────┘
                │
                ▼ (if can cancel)
┌─────────────────────────────────────────────────────────────────┐
│  Orchestrator.Cancel(sagaID)                                    │
├─────────────────────────────────────────────────────────────────┤
│  1. Load SagaState                                              │
│  2. Compensate in REVERSE order:                                │
│     a. InitBillingStep.Compensate() → Delete billing account    │
│     b. CreateVisitStep.Compensate() → Soft delete visit         │
│  3. Update SagaState (status: compensated)                      │
│  4. Trigger external cleanup (Satu Sehat status → cancelled)    │
│  5. Return success                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Infrastructure Requirements

### 5.1 Redis

- **Purpose:** Saga state storage
- **Key pattern:** `saga:{saga_id}`
- **TTL:** 24 hours (configurable per saga type)
- **Requirements:** Already available in WellMed infrastructure

### 5.2 RabbitMQ

- **Purpose:** Async step processing
- **Queue:** `saga.async.steps`
- **DLQ:** `saga.async.steps.dlq` (for failed steps requiring attention)
- **Requirements:** Already available in WellMed infrastructure

### 5.3 No New Infrastructure Required

The saga framework uses existing Redis and RabbitMQ infrastructure.

---

## 6. External System Handling

### 6.1 Satu Sehat

| Operation | Saga Integration |
|-----------|------------------|
| Create Encounter | Async step after visit completion |
| Update to Cancelled | Compensation step (PUT with status: cancelled) |

**Note:** Satu Sehat supports FHIR R4 status codes including `cancelled` and `entered-in-error`. Compensation is possible via status update, not deletion.

### 6.2 Jurnal

| Operation | Saga Integration |
|-----------|------------------|
| Create Posting | Async step after payment |
| Reversal | Compensation step (create reversal entry) |

**Note:** Jurnal is fully compensatable via reversal postings.

### 6.3 External Systems Are NOT Part of Saga Scope

External API calls (Satu Sehat, Jurnal) are triggered by the saga but have their own retry/error handling. They do not block the saga's sync phase or prevent user response.

---

## 7. Implementation Plan

### Phase 1: Framework Core

- [ ] Define `Step` interface and base implementations
- [ ] Implement `SagaState` struct and Redis store
- [ ] Implement `Orchestrator` with sync phase execution
- [ ] Implement compensation logic (reverse order execution)
- [ ] Add X-Ray trace context to `SagaState`
- [ ] Implement trace propagation through sync steps
- [ ] Write unit tests for orchestrator

### Phase 2: Visit Sagas

- [ ] Implement `CreateVisitStep` (EMR service call)
- [ ] Implement `InitBillingStep` (Cashier service call)
- [ ] Implement `UpdateVisitStatusStep`
- [ ] Implement `FinalizeChargesStep`
- [ ] Register Create Visit and Complete Visit saga definitions
- [ ] Implement Cancel Visit as compensation saga
- [ ] Implement blocking activity tracking
- [ ] Implement `CanCancel` and `Cancel` methods
- [ ] Write integration tests for visit sagas

### Phase 3: Payment + User Sagas

- [ ] Implement `ProcessPaymentStep`
- [ ] Implement Jurnal posting as async step
- [ ] Register Payment saga definition
- [ ] Implement `CreateUserStep` (Backbone service call)
- [ ] Implement `CreatePractitionerStep` (EMR service call)
- [ ] Implement Satu Sehat Practitioner sync as async step
- [ ] Write integration tests

### Phase 4: Async Worker

- [ ] Implement RabbitMQ async worker
- [ ] Implement X-Ray trace continuation from saga state
- [ ] Implement retry logic for async steps
- [ ] Implement DLQ routing (hand off to Gateway/API client layer)
- [ ] Write integration tests

### Phase 5: Integration + Migration

- [ ] End-to-end testing of all 5 sagas
- [ ] Test compensation scenarios (mid-saga failures)
- [ ] Test blocking activity rules
- [ ] Test 24-hour window expiration
- [ ] Integrate saga framework with Gateway routing
- [ ] Document error scenarios and recovery procedures

---

## 8. Success Criteria

| Criteria | Measurement |
|----------|-------------|
| Data consistency | Zero orphaned records across services |
| UX responsiveness | Visit creation returns in <500ms (sync phase) |
| Compensation reliability | 100% successful rollback on technical failures |
| Cancellation accuracy | Blocking rules correctly prevent invalid cancellations |
| Observability | All saga state transitions logged and queryable |

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Redis failure mid-saga | Orphaned state | Use Redis persistence (AOF), implement recovery sweep |
| Service timeout during sync | User sees error | Clear timeout + compensation, retry guidance |
| Async step repeatedly fails | Data inconsistency | DLQ + alerting + manual intervention tooling |
| Blocking activity race condition | Cancel succeeds when it shouldn't | Pessimistic locking on blocking activity check |

---

## 10. Decisions Log

| Item | Decision |
|------|----------|
| **Saga ID format** | ULID (not UUID) - sortable, URL-safe |
| **Monitoring** | Logs to CloudWatch, hooks for future HQ-Pusat dashboard |
| **Admin UI** | CLI only for now |
| **External system retries** | Handled by Gateway/API client layer (see API client docs), not saga framework |

---

## 11. Logging Strategy

Two log levels for saga operations:

### Level 1: Summary (Dashboard-ready)

For future HQ-Pusat dashboard consumption. Structured, minimal, state-transition focused.

```json
{
  "saga_id": "01HQ3K...",
  "type": "create_visit",
  "event": "saga_completed",
  "status": "active",
  "duration_ms": 245,
  "visit_id": "v_123",
  "tenant_id": "tenant_abc"
}
```

Events to log:
- `saga_started`
- `saga_completed`
- `saga_failed`
- `saga_compensated`
- `blocking_activity_added`
- `cancellation_attempted`
- `cancellation_blocked`

### Level 2: Verbose (Troubleshooting)

For debugging failures. Full context, step-by-step detail.

```json
{
  "saga_id": "01HQ3K...",
  "type": "create_visit",
  "event": "step_executed",
  "step": "create_visit",
  "duration_ms": 120,
  "input": {...},
  "output": {...},
  "trace_id": "xray-trace-id"
}
```

### X-Ray Integration

Integrate trace context propagation now. This is low effort and enables full X-Ray tracing without refactoring later.

**Implementation requirements:**

- [ ] Add X-Ray trace ID to saga state
- [ ] Propagate trace context through all sync steps
- [ ] Propagate trace context to async worker via message headers
- [ ] Include trace ID in all log entries (Level 1 and Level 2)

```go
type SagaState struct {
    // ... existing fields ...
    
    // Tracing
    TraceID    string `json:"trace_id"`     // X-Ray trace ID
    ParentID   string `json:"parent_id"`    // Parent segment ID
}
```

**Step context propagation:**

```go
func (o *Orchestrator) Execute(ctx context.Context, sagaType string, input any) (...) {
    // Extract or create X-Ray segment
    seg := xray.GetSegment(ctx)
    if seg == nil {
        ctx, seg = xray.BeginSegment(ctx, "saga:"+sagaType)
        defer seg.Close(nil)
    }
    
    state.TraceID = seg.TraceID
    state.ParentID = seg.ID
    
    // Each step gets a subsegment
    for _, step := range definition.SyncSteps {
        ctx, subseg := xray.BeginSubsegment(ctx, "step:"+step.Name())
        err := step.Execute(ctx, state)
        subseg.Close(err)
        // ...
    }
}
```

**Async worker trace continuation:**

```go
func (w *Worker) ContinueAsync(msg Message) {
    state := w.store.Get(msg.SagaID)
    
    // Continue trace from saga state
    ctx := xray.ContextWithTraceHeader(context.Background(), state.TraceID, state.ParentID)
    ctx, seg := xray.BeginSegment(ctx, "saga:async:"+state.Type)
    defer seg.Close(nil)
    
    // Execute async steps with tracing
    // ...
}
```

---

## 12. Out of Scope

Explicitly not part of this framework (handled elsewhere):

| Item | Where It Lives |
|------|----------------|
| External API retries (Satu Sehat, Jurnal) | Gateway / API client layer |
| DLQ handling for external calls | Gateway / API client layer |
| Monitoring dashboard | Future HQ-Pusat (hooks ready in logging) |
| Tenant provisioning saga | Backbone service (DB-level, not cross-service) |

---

## Appendix A: Saga Definition Example

```go
// definitions/visit.go

package definitions

import (
    "time"
    "wellmed/saga"
    "wellmed/saga/steps/emr"
    "wellmed/saga/steps/cashier"
)

var CreateVisitSaga = saga.SagaDefinition{
    Name: "create_visit",
    SyncSteps: []saga.Step{
        emr.CreateVisitStep{},
        cashier.InitBillingStep{},
    },
    AsyncSteps: []saga.Step{
        // Future: notification steps
    },
    BlockingRules: []saga.BlockingRule{
        {ActivityType: "diagnostic", Message: "Cannot cancel: diagnostic performed"},
        {ActivityType: "lab_sample", Message: "Cannot cancel: lab sample collected"},
        {ActivityType: "medication_dispensed", Message: "Cannot cancel: medication dispensed"},
        {ActivityType: "payment_processed", Message: "Cannot cancel: payment processed"},
    },
    TTL: 24 * time.Hour,
}

func init() {
    saga.Register(CreateVisitSaga)
}
```

---

## Appendix B: Step Implementation Example

```go
// steps/emr/create_visit.go

package emr

import (
    "context"
    "wellmed/saga"
    "wellmed/services/emr"
)

type CreateVisitStep struct {
    emrClient emr.Client
}

func (s CreateVisitStep) Name() string {
    return "create_visit"
}

func (s CreateVisitStep) Execute(ctx context.Context, state *saga.SagaState) error {
    var input CreateVisitInput
    if err := json.Unmarshal(state.Input, &input); err != nil {
        return err
    }
    
    visit, err := s.emrClient.CreateVisit(ctx, input)
    if err != nil {
        return err
    }
    
    // Store result for compensation context
    state.SetStepResult(s.Name(), visit)
    return nil
}

func (s CreateVisitStep) Compensate(ctx context.Context, state *saga.SagaState) error {
    var visit Visit
    if err := state.GetStepResult(s.Name(), &visit); err != nil {
        return err
    }
    
    return s.emrClient.SoftDeleteVisit(ctx, visit.ID)
}
```

---

*Document Owner: Hamzah (CTO)*  
*Last Updated: January 2025*  
*Status: Draft for team review*
