# Project: MyApp

## Stack
- Next.js 16, TypeScript strict, Tailwind CSS, Prisma + PostgreSQL
- pnpm for package management
- Vitest for unit tests, Playwright for E2E

## Conventions
- Components: PascalCase, co-located tests (Component.test.tsx)
- API routes: zod validation on all inputs, never trust req.body
- Database: always use transactions for multi-table writes
- Commits: conventional commits (feat/fix/chore/docs)

## Commands
- `pnpm dev` -- start dev server
- `pnpm test` -- run unit tests
- `pnpm test:e2e` -- run Playwright suite
- `pnpm build` -- production build (MUST pass before PR)

## Rules
- Never modify migration files once committed
- All API responses use { data, error } shape
- No `any` types -- use `unknown` + type narrowing
