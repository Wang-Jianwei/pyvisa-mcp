# PyVISA MCP Workspace Schema

## Purpose

This repository serves two roles at the same time:

1. It is the implementation workspace for a PyVISA-based MCP server.
2. It is a persistent LLM-maintained project wiki following the pattern in `llm-wiki.md`.

The wiki is not optional project decoration. It is part of the working system for
research, design, implementation, verification, and maintenance.

## Scope Decisions

- Current project scope is Python only. Ignore the earlier C++ mention.
- Phase 1 transport priority is STDIO.
- Design should anticipate later expansion, but implementation may proceed in small stages.
- Prefer PyVISA high-level APIs and object model over raw VISA function exposure.
- Prefer FastMCP for the first server implementation.

## Three-Layer Model

This repository is organized into three layers:

### 1. Raw

`raw/` stores project inputs and durable research notes.

Rules:

- Treat `raw/` as append-oriented and source-oriented.
- Store external facts, research notes, copied excerpts, decision baselines, and supporting artifacts here.
- Do not turn `raw/` into the polished knowledge layer.
- Do not silently rewrite old research notes to match newer conclusions. Add a new note or add a dated correction.

Recommended subdirectories:

- `raw/notes/` for distilled research notes and decision records.
- `raw/external/` for copied or imported external materials.
- `raw/assets/` for downloaded images or binary attachments when needed.
- `raw/sources/` for source inventories or manifests when needed.

### 2. Wiki

`wiki/` stores LLM-maintained, structured, cross-linked markdown pages.

Rules:

- The wiki is the maintained knowledge layer.
- Pages should summarize, synthesize, compare, and connect information.
- Update wiki pages when new raw material changes the project understanding.
- Prefer editing an existing relevant page over creating near-duplicates.

Recommended subdirectories:

- `wiki/overview/` for high-level project orientation.
- `wiki/concepts/` for MCP and related conceptual material.
- `wiki/standards/` for PyVISA, SCPI, VISA, and protocol notes.
- `wiki/project/` for architecture plans, design decisions, and implementation tracking.
- `wiki/sources/` for source registers and provenance helpers.

### 3. Schema

`AGENTS.md` is the schema and workflow definition for this repository.

Rules:

- Update this file when the maintenance workflow, naming rules, or repository conventions change.
- Do not use `llm-wiki.md` as the live operating manual. Use it as the inspiration document.

## File Conventions

### Raw note naming

- Use dated note names for durable research notes: `YYYY-MM-DD-topic.md`
- Keep topics short and stable: `pyvisa-basics`, `mcp-basics`, `scpi-basics`, `project-decisions`

### Wiki page naming

- Use descriptive kebab-case file names.
- Prefer stable page names over date-prefixed wiki page names.
- A page should represent a durable concept, topic, or project area.

### Wiki frontmatter

Wiki pages should use minimal YAML frontmatter when practical:

```yaml
---
title: Human readable title
status: active
updated: 2026-05-08
tags:
	- project
	- pyvisa
source_notes:
	- ../../raw/notes/2026-05-08-pyvisa-basics.md
---
```

Guidelines:

- `title` is required.
- `status` should usually be `active`, `draft`, or `superseded`.
- `updated` should reflect the last substantive edit date.
- `source_notes` should point at the most relevant `raw/` notes when applicable.

## Mandatory Special Files

### `wiki/index.md`

Purpose:

- Main navigation entry for the wiki.
- Organized by category.
- Each entry should include a page link and a one-line summary.

Update rules:

- Update on every new wiki page creation.
- Update when a page meaningfully changes category or scope.

### `wiki/log.md`

Purpose:

- Append-only chronological project and wiki activity log.

Entry format:

- Every entry must start with a level-2 heading in the format:
	`## [YYYY-MM-DD] type | short title`

Supported `type` values:

- `init`
- `ingest`
- `query`
- `design`
- `implementation`
- `verification`
- `lint`
- `decision`

Each log entry should include:

- What changed
- Which files were added or updated
- Why the change matters

## Operating Workflows

### Ingest workflow

Use this when new external information arrives.

Steps:

1. Create or update a relevant note in `raw/`.
2. Update the corresponding wiki pages in `wiki/`.
3. Update `wiki/index.md` if page inventory changed.
4. Append an `ingest` entry to `wiki/log.md`.

Examples of information that should go through ingest:

- External protocol documentation
- PyVISA behavior notes
- MCP SDK research
- SCPI references
- Device-specific command knowledge

### Query workflow

Use this when answering a project question from existing repository knowledge.

Steps:

1. Read `wiki/index.md` first.
2. Read the relevant wiki pages.
3. Read `raw/` notes if provenance or detail is needed.
4. If the answer creates durable project knowledge, file it back into the wiki.
5. Append a `query` entry to `wiki/log.md` when the query materially improves repository knowledge.

### Lint workflow

Use this periodically or after a burst of work.

Check for:

- Missing links from `wiki/index.md`
- Duplicate or overlapping wiki pages
- Stale pages whose conclusions conflict with newer raw notes
- Important concepts with no page
- Pages with weak provenance
- Decisions recorded in chat but not written to repository files

Record meaningful lint outcomes in `wiki/log.md` as `lint` entries.

## Development Workflow Requirements

Before starting substantive implementation work:

1. Make sure the relevant background knowledge exists in `raw/`.
2. Make sure the relevant architecture or scope pages exist in `wiki/`.
3. If a new technical decision is made, record it in `raw/notes/` or a relevant wiki page before it is forgotten.

During implementation:

- Keep code changes and wiki changes aligned.
- When design intent changes, update the relevant wiki page in the same workstream when practical.
- Do not rely on chat history as the only place where important reasoning exists.

After implementation or verification:

1. Update affected wiki pages if understanding changed.
2. Append a `verification` or `implementation` log entry when the change is significant.
3. Add new durable troubleshooting or environment findings to `raw/` if they will matter later.

## Content Placement Rules

Put information in `raw/` when it is:

- Close to an external source
- A research capture
- A decision baseline
- A troubleshooting record
- A temporary but durable working note

Put information in `wiki/` when it is:

- A synthesis across multiple raw notes
- A stable concept page
- A project architecture explanation
- A curated capability list
- A maintained summary that should stay current over time

## Initial Knowledge Priorities

Before beginning server implementation, the repository should contain at least:

- PyVISA basics and architecture notes
- MCP basics and server primitive notes
- SCPI basics and command/query model notes
- Project scope and decision baseline
- A project overview page
- An architecture plan page

## Implementation Mapping For This Project

The expected first implementation track is:

1. Wiki bootstrap and project record setup
2. Python package scaffold
3. FastMCP server entrypoint
4. PyVISA adapter layer
5. Session registry
6. Tools and resources schema design
7. Tests and environment diagnostics

Keep the wiki updated to mirror this progression.

## Things To Avoid

- Do not store important project decisions only in chat.
- Do not create wiki pages without indexing them.
- Do not rewrite `raw/` notes into polished summaries without preserving the raw note layer.
- Do not let implementation get ahead of terminology and scope documentation when those terms are still unstable.
- Do not create duplicate pages for the same concept unless there is a clear split in purpose.

## Definition Of Done For The Current Bootstrap

The initial workspace bootstrap is complete when:

- `raw/` exists and contains the initial PyVISA, MCP, SCPI, and project decision notes.
- `wiki/` exists and contains `index.md`, `log.md`, and first-pass overview and standards pages.
- `AGENTS.md` defines the ongoing maintenance workflow.
- The repository is ready to start code implementation without losing research context.
