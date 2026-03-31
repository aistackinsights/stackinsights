# AGENTS.md
<!-- 
  AGENTS.md is the single source of truth for AI agents (Codex, Claude Code,
  Cursor, Copilot Workspace, etc.) working on this repo.
  
  Keep it honest, opinionated, and short. Agents read this on every task.
  Fluff wastes tokens and dilutes the signal.
  
  HOW TO USE THIS TEMPLATE:
  1. Fill in every section marked with <!-- FILL IN -->
  2. Delete these HTML comments before committing
  3. Run `python spec_linter.py AGENTS.md` to validate
-->

---

## Project Overview
<!-- 
  One paragraph. What does this project do? Who uses it?
  Agents use this to understand scope and avoid out-of-scope changes.
-->

**[Project Name]** is a <!-- FILL IN: e.g., "Next.js SaaS app that lets teams manage X" -->.

Primary users: <!-- FILL IN: e.g., "developers, internal ops team" -->  
Status: <!-- FILL IN: e.g., "production", "beta", "greenfield" -->

---

## Stack
<!--
  Be specific — include versions. "React" tells an agent almost nothing.
  "React 18.3 + Next.js 14 (App Router)" tells it everything.
  Agents use this to pick the right APIs, imports, and patterns.
-->

- **Language**: TypeScript 5.4
- **Runtime**: Node.js 20 LTS
- **Framework**: Next.js 14 (App Router) <!-- or: Express 4, FastAPI 0.111, etc. -->
- **UI**: Tailwind CSS 3.4 + shadcn/ui
- **Database**: PostgreSQL 16 via Prisma 5
- **Auth**: NextAuth.js v5
- **Testing**: Vitest + Playwright
- **Package manager**: pnpm 9
- **CI**: GitHub Actions

---

## Architecture
<!--
  Tell agents where things live so they don't create files in the wrong place
  or duplicate existing modules. Keep this updated as the codebase evolves.
-->

```
src/
  app/           # Next.js App Router pages and layouts
  components/    # Shared React components
  lib/           # Utilities, helpers, shared logic
  server/        # Server actions, API routes, DB queries
  hooks/         # Custom React hooks
  types/         # Shared TypeScript types / Zod schemas

prisma/          # Database schema and migrations
public/          # Static assets
tests/           # Integration and E2E tests (Playwright)
```

**Key patterns:**
- Server components by default; use `"use client"` only when necessary
- All DB access goes through `src/server/db/` — never query from components
- Shared types live in `src/types/` — don't redefine inline
- Environment variables are validated in `src/lib/env.ts` (Zod) — add new ones there

---

## Conventions
<!--
  The rules agents must follow when writing or editing code.
  Be specific — vague rules get ignored or misinterpreted.
-->

### Naming
- Files: `kebab-case.ts` (e.g., `user-profile.ts`)
- Components: `PascalCase.tsx` (e.g., `UserProfile.tsx`)
- Functions/variables: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE`

### Code Style
- No `any` — use `unknown` and narrow, or define proper types
- Prefer `const` over `let`; never use `var`
- Async/await over `.then()` chains
- Early returns over deep nesting
- Max function length: ~40 lines. If longer, split it.

### Imports
- Absolute imports from `@/` (maps to `src/`)
- Group: 1) Node built-ins, 2) external packages, 3) internal `@/` imports
- No circular imports

### Error Handling
- Server actions must return `{ data, error }` — never throw to the client
- Log errors with context: `console.error("[module] message", { context })`

### Testing
- Unit tests co-located: `foo.ts` → `foo.test.ts`
- E2E tests in `tests/e2e/`
- Test names: `"should <do something> when <condition>"`

---

## Anti-Patterns
<!--
  This section is critical. Agents need explicit "never do this" rules
  to avoid subtle bugs, security issues, or architectural drift.
  Be blunt — diplomatic wording gets ignored.
-->

### Never Do This

- ❌ **Never** import server-only modules (`prisma`, `bcrypt`, secret env vars) in client components
- ❌ **Never** use `@ts-ignore` or `as any` — fix the type instead
- ❌ **Never** commit `.env` or any file containing secrets
- ❌ **Never** add a new `npm` / `pip` dependency without explicit instruction — check existing deps first
- ❌ **Never** write raw SQL — use Prisma's query API
- ❌ **Never** put business logic in React components — extract to `lib/` or server actions
- ❌ **Never** create a new utility that already exists in `src/lib/`
- ❌ **Never** disable ESLint rules inline (`// eslint-disable-next-line`) without a comment explaining why
- ❌ **Never** use `useEffect` to fetch data — use server components or React Query

---

## Commands
<!--
  The exact commands to build, test, lint, and run the project.
  Agents use these to verify their changes. Be precise.
-->

```bash
# Install dependencies
pnpm install

# Start dev server
pnpm dev

# Run unit tests (watch mode)
pnpm test

# Run unit tests (CI / one-shot)
pnpm test:run

# Run E2E tests
pnpm test:e2e

# Type check
pnpm typecheck

# Lint
pnpm lint

# Format
pnpm format

# Build for production
pnpm build

# Database: apply migrations
pnpm db:migrate

# Database: open Prisma Studio
pnpm db:studio
```

---

## PR & Git Workflow
<!--
  Agents that can open PRs need to know your branching and commit conventions.
  Without this, they'll create branches named "fix" and write "updated stuff".
-->

### Branches
- `main` — production. Never push directly.
- `dev` — integration branch. PRs merge here first.
- Feature branches: `feat/<short-description>`
- Bug branches: `fix/<short-description>`
- Chore branches: `chore/<short-description>`

### Commits (Conventional Commits)
```
feat: add user profile page
fix: correct token refresh race condition
chore: update dependencies
docs: add API endpoint documentation
refactor: extract auth logic to useAuth hook
test: add integration tests for checkout flow
```

### PR Rules
- Title must follow Conventional Commits format
- Must include: what changed, why, how to test
- All CI checks must pass before merge
- One logical change per PR — don't bundle unrelated fixes
- Reference the issue: `Closes #123`

---

## Multi-Agent Rules
<!--
  When multiple agents (or agent + human) work in parallel, scope discipline
  prevents conflicts and makes PRs reviewable.
-->

### Scope Constraints
- Work only in files relevant to the assigned task
- If a change requires touching >5 files, pause and ask for confirmation
- Never refactor files you weren't asked to change — separate PR

### File Size
- Max ~300 lines per new file. If a file grows beyond this, split it.
- Max ~100 lines per function/component

### Dependencies
- Do **not** add new packages without explicit instruction
- If you believe a new dep is needed, state which one and why, then wait for approval
- Prefer the existing dep that already does the job

### Migrations
- Do **not** run `prisma migrate dev` automatically — create the migration file, then ask
- Never modify an existing migration file

### Coordination
- If your task depends on another agent's work, state the dependency clearly in the PR description
- Resolve all TypeScript errors in your changed files before opening a PR

---

## Response Style
<!--
  How agents should communicate — in code comments, PR descriptions, and chat.
  Agents with no style guidance default to verbose, hedging corporate-speak.
-->

- **No preamble.** Don't restate the task. Just do it.
- **No sycophancy.** No "Great question!", "Certainly!", or "I'd be happy to help!"
- **No unnecessary summaries.** Don't explain what you just did after doing it.
- **Minimal comments.** Comment code only when the logic is non-obvious. Don't narrate the obvious.
- **Direct and concise.** If a change is small and clear, make it without asking for permission.
- **Surface blockers fast.** If something is ambiguous or blocked, say so immediately — don't spin wheels.
