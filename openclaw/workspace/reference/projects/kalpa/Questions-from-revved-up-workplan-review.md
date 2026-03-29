### Question after reviewing the advances architecture document from Revved up.

-	Where does the claude_architecture.md doc sit? Inside /docs/ or somewhere else so that claude can access it?
-	Would like to ideally at some point have a bug triage that comes from sentry and scrapes WA (service) conversations and loads bugs in to a triage queue that can be ralph looped with ai driven prs automatically raised for review (daily)
-	First subagents to set up will be the documentation ones – one for each type/level of documentation (technical); then can expand from there (writing test code
-	Claude recommends several levels of decision tracking (changelog, ai-log etc) this seems like overkill for our scale and impossible to maintain – I want to track changes to prompts, key decisions (ADR), and changes that were made automatically (log) but beyond that I don’t think the granularity is helpful.
-	For example what is runbooks and what is it useful for?
-	Plugins (how are they different from subagents or skills?
	- Stealing from mitch (pr-review-toolkit` | **REPLACE** | 6 agents (comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer, code-reviewer, code-simplifier). Useful concepts but too generic |) – good idea to create summary from multiple agents
	- Explore code-explorer, code-architect, code reviewer
	- Also conceptually how do I make a dictionary for our go patterns to avoid duplication (and flag if duplicated in pr) and suggest given the correct context – want to build this with ai help. Also add in traditional patterns that my team is unaware of – like our saga discussion this week
	- Explore testing out a single shot action like /code-review vs having triggers to run several agents who do a job -> report out to a temp.md and then trigger the next agent to do its job against the results.
-	Ralph look – with command – I think this needs to be configured (example user runs `/ralph-loop "task" --completion-promise "DONE" --max-iterations 50`)
-	What are DRY violations in testing?
-	When should documentation step happing in CI/PR? If before then docs are part of CI review – not a bad idea…
-	What is an N+1 pattern – like slow query in a db?
-	Do a bit of work to clarify assign author .yaml for me
-	Consider docs sync agent to make sure docs are adopting patterns, formats and cascade (down) or percolate (up) as appropriate

