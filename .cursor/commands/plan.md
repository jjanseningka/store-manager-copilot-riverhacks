# Plan

Produce a plan before any change that touches more than two files or more
than fifty lines.

1. State the goal in one sentence.
2. List the files you intend to touch and what changes each one.
3. State acceptance criteria the change must meet.
4. State the verification command(s) you will run.
5. State the rollback strategy.

Save substantive plans to `.cursor/plans/<slug>.md` so the work can be
resumed by a different session or sub-agent.

Do not start editing until the user (or a reviewing sub-agent) has agreed
to the plan.
