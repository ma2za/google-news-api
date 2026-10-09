# Shared agent context

This directory is the agent-neutral home for shared maintainer context and
portable workflows.

## Required reading

- `../AGENTS.md`: canonical instructions for every agent.
- `../RELEASE_PLAN.md`: tracked roadmap and release gates. Read the entire file
  for any release, roadmap, or release-readiness request. The maintainer approved
  including it in every checkout on 2026-10-09.
- `FAILURE_RETROSPECTIVE.md`: mistakes that must not recur during release work.
- `commands/release-prepare.md`: portable release-candidate preparation prompt.
- `commands/release-verify.md`: portable release verification prompt.

Private environment configuration must not be copied into prompts, logs,
commits, or agent memory.
