# Setup Guide: Running the Gateway Plan in Claude Code

**For**: Alex
**Date**: 25 February 2026
**Prereqs**: Claude Code installed, gateway repo downloaded

---

## 1. What You're Setting Up

Three things:

1. **The ralph-loop plugin** — makes Claude Code loop through tasks automatically until it hits a checkpoint
2. **The task-runner skill** — tells Claude Code how to read PLAN.md and track progress
3. **The project directory** — where the gateway code and plan files live together

## 2. Step-by-Step Setup

### 2.1 Install the Ralph Loop Plugin

Open Claude Code (in your terminal, run `claude`). Then run:

```
/plugin install ralph-wiggum@claude-plugins-official
```

This installs the official Anthropic ralph loop plugin. It gives you two commands:
- `/ralph-loop "prompt"` — starts the loop
- `/cancel-ralph` — stops the loop

**Verify it installed**: Run `/help` and look for ralph-loop in the command list.

**Note**: You need `jq` installed on your Mac. Check with `which jq`. If not installed:
```bash
brew install jq
```

### 2.2 Install the Task Runner Skill

The task-runner skill is the `SKILL.md` file packaged as a `.skill` file. To install it:

1. In Claude Code, use the plugin/skill install method, OR
2. Place the `task-runner/SKILL.md` file in your project's `.claude/skills/` directory:

```bash
# From your project directory
mkdir -p .claude/skills/task-runner
cp ~/path/to/task-runner/SKILL.md .claude/skills/task-runner/SKILL.md
```

Alternatively, if you're using Claude Code's skill upload:
```
/skill install path/to/task-runner.skill
```

### 2.3 Set Up the Project Directory

```bash
# Navigate to your projects directory
cd ~/Projects

# If you downloaded the gateway as a zip, unzip it
unzip gateway-main.zip -d gateway
cd gateway

# Or if you cloned it
# cd gateway

# Copy the plan file into the project root
cp ~/path/to/PLAN.md ./PLAN.md

# Initialize git if not already (the plan commits after each task)
git status  # should show you're in a git repo
```

Your directory should now look like:
```
~/Projects/gateway/
├── PLAN.md              ← The execution plan
├── cmd/                 ← Gateway source code
├── internal/            ← Gateway source code
├── go.mod
├── go.sum
├── .claude/
│   └── skills/
│       └── task-runner/
│           └── SKILL.md
└── ... (rest of gateway code)
```

## 3. Running the Plan

### 3.1 Human-in-the-Loop Mode (Recommended for First Run)

Open Claude Code in the gateway directory:

```bash
cd ~/Projects/gateway
claude
```

Then say:
```
Run the plan. Start from the beginning.
```

Claude Code will:
1. Read PLAN.md
2. Create PROGRESS.md
3. Execute Task 0.1
4. Log the result
5. Move to Task 0.2
6. Continue until it hits the Phase 0 CHECKPOINT
7. Stop and ask you to review

**This is the safest way to start.** You watch each task execute, review the output, and say "continue the plan" when ready.

### 3.2 Ralph Loop Mode (Autonomous, Use After You're Comfortable)

Once you've done a few tasks manually and trust the pattern:

```
/ralph-loop "Read PLAN.md and PROGRESS.md. Execute the next available AI task. After completing each task, update PROGRESS.md and commit. Continue until you hit a HUMAN task, CHECKPOINT, or end of phase. If all tasks in the current phase are complete, output <promise>PHASE_COMPLETE</promise>. If blocked on a human task, output <promise>WAITING_HUMAN</promise>." --max-iterations 20 --completion-promise "PHASE_COMPLETE"
```

This will run through an entire phase autonomously, stopping at checkpoints.

**Important**: Set `--max-iterations` conservatively. 20 is plenty for one phase. If it loops more than that, something is wrong.

### 3.3 Resuming After a Break

If you close Claude Code and come back later:

```bash
cd ~/Projects/gateway
claude
```

Then say:
```
Continue the plan. Pick up where we left off.
```

Claude Code reads PROGRESS.md and knows exactly where you stopped.

## 4. What to Watch For

### 4.1 Normal Flow
```
📋 Plan: Gateway Service — Documentation, Testing & CI/CD Dry Run
📍 Current: Phase 0, Task 0.1 — Validate project structure
✅ Completed: 0/17 tasks
⏸️ Status: Ready to execute
```
Then it works, logs progress, and continues.

### 4.2 Checkpoint Stop
```
🔲 CHECKPOINT: Orientation Complete
Review the four docs produced in Phase 0...
Say "continue the plan" when ready.
```
This is expected. Review and continue.

### 4.3 Task Failure
```
❌ Task 2.2 FAILED: go test compilation error — missing interface method
```
This is also expected, especially in Phase 2 (tests). Claude may not get the mock interfaces right on the first try. Review the error, and either fix it manually or say "retry task 2.2."

### 4.4 Things That Might Go Wrong

- **Go toolchain not installed**: You need Go installed locally for test compilation. Check with `go version`.
- **golangci-lint not installed**: Needed for Phase 3. Install with `brew install golangci-lint`.
- **Tests fail because of missing dependencies**: The gateway might need Postgres/Redis to compile some packages. If so, we may need to skip integration-heavy packages in the unit test phase.

## 5. Cost Awareness

Each ralph loop iteration uses Claude Code API credits. For this plan:
- Phase 0 (orientation): ~4 iterations, light token usage
- Phase 1 (documentation): ~4 iterations, moderate token usage (reading lots of source files)
- Phase 2 (testing): ~5 iterations, heavier token usage (generating and running code)
- Phase 3 (CI/CD): ~5 iterations, moderate token usage
- Phase 4 (meeting prep): ~3 iterations, light token usage

**Estimated total**: ~20 iterations. On the Max plan this is well within limits. On the Pro plan, this might use a meaningful chunk of your daily allowance — consider spreading across 2-3 days.

## 6. Quick Reference

| Action | Command |
|--------|---------|
| Start plan | "Run the plan" |
| Continue after checkpoint | "Continue the plan" |
| Retry a failed task | "Retry task X.Y" |
| Skip a task | "Skip task X.Y and continue" |
| Check status | "What's the plan status?" |
| Start ralph loop | `/ralph-loop "..." --max-iterations 20` |
| Stop ralph loop | `/cancel-ralph` |
