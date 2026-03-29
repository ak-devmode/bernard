# Ralph Loop: Autonomous AI Development Cycles

## What is a Ralph Loop?

A Ralph Loop is a technique for running Claude Code autonomously in a continuous loop until a task is complete. Instead of Claude stopping after one attempt, it keeps iterating—reviewing its own work, finding issues, and fixing them—until it meets defined success criteria.

The name comes from Ralph Wiggum (The Simpsons), embodying the philosophy: **persistent iteration despite setbacks**.

> "Ralph is a Bash loop" — Geoffrey Huntley (creator)

## The Core Philosophy

```
Don't aim for perfect on first try.
Let the loop refine the work.
Failures are data, not disasters.
Keep trying until success.
```

This inverts the typical AI coding workflow:

**Traditional:** Prompt → Claude works → Output → Human reviews → Repeat manually

**Ralph Loop:** Prompt → Claude works → Fails → Sees failure → Fixes → Repeat automatically → Success

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                      RALPH LOOP CYCLE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│    ┌──────────┐                                                │
│    │  START   │                                                │
│    └────┬─────┘                                                │
│         │                                                       │
│         ▼                                                       │
│    ┌──────────────────────────────────────────┐                │
│    │  1. Claude reads prompt + PRD/task       │                │
│    └────────────────┬─────────────────────────┘                │
│                     │                                           │
│                     ▼                                           │
│    ┌──────────────────────────────────────────┐                │
│    │  2. Claude works on next unchecked task  │                │
│    └────────────────┬─────────────────────────┘                │
│                     │                                           │
│                     ▼                                           │
│    ┌──────────────────────────────────────────┐                │
│    │  3. Claude runs tests / validates        │                │
│    └────────────────┬─────────────────────────┘                │
│                     │                                           │
│              ┌──────┴──────┐                                   │
│              │  Success?   │                                   │
│              └──────┬──────┘                                   │
│                     │                                           │
│         ┌─────NO────┴────YES─────┐                             │
│         │                        │                              │
│         ▼                        ▼                              │
│    ┌─────────┐          ┌──────────────────┐                   │
│    │ Iterate │          │ Output <promise> │                   │
│    │  again  │          │     DONE         │                   │
│    └────┬────┘          └────────┬─────────┘                   │
│         │                        │                              │
│         └────────┐    ┌──────────┘                             │
│                  │    │                                         │
│                  ▼    ▼                                         │
│              ┌─────────────┐                                   │
│              │  COMPLETE   │                                   │
│              └─────────────┘                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

Ralph is an official Claude Code plugin:

```bash
# Install the plugin
/plugin marketplace add anthropics/claude-code
/plugin install ralph-wiggum@claude-plugins-official
```

## Basic Usage

```bash
# Simple loop
/ralph-loop "Fix all TypeScript errors in src/" --max-iterations 10

# With completion promise (explicit success signal)
/ralph-loop "Implement user authentication. Output <promise>AUTH_DONE</promise> when complete." \
  --max-iterations 20 \
  --completion-promise "AUTH_DONE"

# Cancel a running loop
/ralph-loop:cancel-ralph
```

## Where Does It Sit?

Ralph is a **plugin**, not a skill. It extends Claude Code's behavior rather than providing knowledge.

```
~/.claude/
├── plugins/
│   └── ralph-wiggum/      # Plugin lives here after installation
│       ├── index.js
│       └── manifest.json

your-repo/.claude/
├── CLAUDE.md              # Project context (Ralph reads this)
├── skills/                # Domain knowledge (Ralph can use these)
│   └── testing.md
└── commands/              # Can trigger Ralph loops
    └── test-all.md
```

---

# Practical Example: WellMed Testing Loop

Here's a real example for your testing workflow:

## The PRD (Product Requirements Document)

Create `PRD-testing.md` in your repo root:

```markdown
# WellMed Integration Testing PRD

## Objective
Implement integration tests for the Patient service with full database coverage.

## Tasks

### Phase 1: Setup
- [ ] Create test database configuration in `tests/integration/config.go`
- [ ] Implement test database cleanup helper
- [ ] Add test fixtures for Patient entity

### Phase 2: Repository Tests
- [ ] Test `PatientRepository.Create` - happy path
- [ ] Test `PatientRepository.Create` - duplicate NIK error
- [ ] Test `PatientRepository.FindByNIK` - found
- [ ] Test `PatientRepository.FindByNIK` - not found
- [ ] Test `PatientRepository.Update` - success
- [ ] Test `PatientRepository.Update` - concurrent modification

### Phase 3: Service Tests  
- [ ] Test `PatientService.RegisterPatient` - valid NIK
- [ ] Test `PatientService.RegisterPatient` - invalid NIK format
- [ ] Test `PatientService.RegisterPatient` - existing patient
- [ ] Test `PatientService.GetPatient` - with SATU SEHAT enrichment
- [ ] Test `PatientService.GetPatient` - SATU SEHAT timeout handling

### Phase 4: Validation
- [ ] All tests pass: `go test ./tests/integration/... -v`
- [ ] Coverage > 80% for patient package
- [ ] No race conditions: `go test -race ./...`

## Success Criteria
All boxes checked. Tests run green. Coverage met.
```

## The Ralph Prompt

```bash
/ralph-loop "
You are implementing integration tests for WellMed.

Read PRD-testing.md to understand the full scope.
Read PROGRESS.md to see what's already done.

Your job:
1. Find the next unchecked task in PRD-testing.md
2. Implement it following our patterns in .claude/skills/coding-standards.md
3. Run the tests to verify
4. If tests pass, check off the task in PROGRESS.md and commit
5. If tests fail, fix and retry

Key patterns:
- Use testcontainers-go for Postgres
- Follow table-driven test style
- Clean up test data after each test
- Use t.Parallel() where safe

When ALL tasks are complete and tests pass:
Output <promise>TESTING_COMPLETE</promise>

If stuck after 5 attempts on same task:
- Document the blocker in PROGRESS.md
- Move to next task
- Output <promise>BLOCKED</promise> if all remaining tasks blocked
" --max-iterations 30 --completion-promise "TESTING_COMPLETE"
```

## Progress Tracking

Claude will maintain `PROGRESS.md`:

```markdown
# Testing Progress

## Completed
- [x] Create test database configuration - commit abc123
- [x] Implement test database cleanup helper - commit def456
- [x] Add test fixtures for Patient entity - commit ghi789

## In Progress
- [ ] Test PatientRepository.Create - happy path
  - Attempt 1: Missing foreign key constraint
  - Attempt 2: Fixed, now passing

## Blocked
(none yet)

## Current Status
Phase 2, Task 1 of 6
Last updated: 2026-01-21 12:34:56
```

## A Complete Skill for Testing (Optional Enhancement)

You can add a skill to help Ralph understand your testing patterns:

```markdown
# .claude/skills/integration-testing.md

# WellMed Integration Testing Patterns

## Test Structure

All integration tests follow this structure:

```go
func TestPatientRepository_Create(t *testing.T) {
    // Setup
    ctx := context.Background()
    db := setupTestDB(t)
    repo := NewPatientRepository(db)
    
    tests := []struct {
        name    string
        input   CreatePatientInput
        wantErr error
    }{
        {
            name: "valid patient",
            input: CreatePatientInput{
                NIK:  "3374010101900001",
                Name: "Test Patient",
            },
            wantErr: nil,
        },
        {
            name: "duplicate NIK",
            input: CreatePatientInput{
                NIK:  "3374010101900001", // same as above
                Name: "Another Patient",
            },
            wantErr: ErrDuplicateNIK,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Execute
            _, err := repo.Create(ctx, tt.input)
            
            // Assert
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("got %v, want %v", err, tt.wantErr)
            }
        })
    }
}
```

## Database Setup

Use testcontainers for real Postgres:

```go
func setupTestDB(t *testing.T) *sql.DB {
    t.Helper()
    
    ctx := context.Background()
    container, err := postgres.Run(ctx,
        "postgres:15-alpine",
        postgres.WithDatabase("wellmed_test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready").
                WithStartupTimeout(30*time.Second)),
    )
    require.NoError(t, err)
    
    t.Cleanup(func() {
        container.Terminate(ctx)
    })
    
    connStr, _ := container.ConnectionString(ctx, "sslmode=disable")
    db, err := sql.Open("postgres", connStr)
    require.NoError(t, err)
    
    // Run migrations
    runMigrations(db)
    
    return db
}
```

## Common Test Fixtures

```go
// tests/fixtures/patient.go
func ValidPatient() *Patient {
    return &Patient{
        NIK:       "3374010101900001",
        Name:      "Test Patient",
        BirthDate: time.Date(1990, 1, 1, 0, 0, 0, 0, time.UTC),
        Gender:    "male",
    }
}

func InvalidNIK() string {
    return "123" // Too short, will fail validation
}
```

## SATU SEHAT Mock

For service tests that call SATU SEHAT:

```go
func mockSatuSehatServer(t *testing.T) *httptest.Server {
    return httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        switch r.URL.Path {
        case "/oauth2/v1/token":
            json.NewEncoder(w).Encode(map[string]string{
                "access_token": "test-token",
                "expires_in":   "3600",
            })
        case "/fhir-r4/v1/Patient":
            // Return FHIR Patient bundle
            w.Write([]byte(patientBundleFixture))
        default:
            w.WriteHeader(404)
        }
    }))
}
```
```

---

## Best Practices for Ralph Loops

### Do's ✅

1. **Always set `--max-iterations`** — Prevents runaway loops
2. **Use clear completion promises** — `<promise>DONE</promise>` not vague success
3. **Run in git-tracked directory** — Easy to revert if things go wrong
4. **Start with human-in-the-loop** — Watch a few iterations before going AFK
5. **Write good PRDs** — Clear tasks that Claude can pick off one by one

### Don'ts ❌

1. **Don't expect perfect first try** — The whole point is iteration
2. **Don't use for exploratory tasks** — Ralph needs clear success criteria
3. **Don't ignore costs** — 50 iterations on large codebase = $50-100+
4. **Don't skip the safety limits** — Circuit breakers exist for a reason

### When to Use Ralph

| Good For | Not Good For |
|----------|--------------|
| Large refactors | Exploratory coding |
| Test implementation | Architecture decisions |
| Linting/formatting fixes | Ambiguous requirements |
| Migration scripts | Creative tasks |
| Dependency upgrades | Tasks needing human judgment |

---

## Summary

Ralph Loop = while(true) + clear success criteria + automatic retry

It's not magic. It's just persistent iteration with good prompts. The skill shifts from "directing Claude step by step" to "writing prompts that converge toward correct solutions."

For your WellMed testing sprint: define the tests you want in a PRD, let Ralph iterate overnight, come back to green tests.
