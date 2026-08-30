# Shared agent context

This directory is the agent-neutral home for local maintainer memory and
portable workflows.

## Required reading

- `../AGENTS.md`: canonical instructions for every agent.
- `PRIVATE_RELEASE_PLAN.md`: private roadmap and release gates. Read the entire
  file for any release, roadmap, or release-readiness request. It is excluded
  from Git intentionally.
- `FAILURE_RETROSPECTIVE.md`: mistakes that must not recur during release work.
- `commands/release-prepare.md`: portable release-candidate preparation prompt.
- `commands/release-verify.md`: portable release verification prompt.

removed-provider still reads the root `removed-provider.md` and `.removed-provider/commands/`, but their
shared instructions are mirrored here or in `../AGENTS.md` so other agents have
the same context. `.removed-provider/.env` remains private environment configuration and
must not be copied into prompts, logs, commits, or agent memory.
