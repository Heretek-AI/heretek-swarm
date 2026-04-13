```markdown
# heretek-swarm Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development patterns and conventions used in the `heretek-swarm` TypeScript codebase. You'll learn how to structure files, write imports/exports, follow commit message conventions, and organize tests. These patterns help maintain consistency and readability across the project.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `userManager.ts`, `swarmController.test.ts`

### Import Style
- Use **relative imports** for modules within the project.
  - Example:
    ```typescript
    import { getUser } from './userManager';
    ```

### Export Style
- Use **named exports** for all modules.
  - Example:
    ```typescript
    // userManager.ts
    export function getUser(id: string) { /* ... */ }
    ```

### Commit Messages
- Follow **Conventional Commits**.
- Use the `feat` prefix for new features.
  - Example:
    ```
    feat: add swarm node discovery logic
    ```

## Workflows

### Feature Development
**Trigger:** When adding a new feature to the codebase  
**Command:** `/feature-dev`

1. Create a new file using camelCase naming.
2. Write code using named exports.
3. Use relative imports for dependencies.
4. Write or update corresponding test files (`*.test.ts`).
5. Commit changes with a conventional commit message:
    ```
    feat: short description of the feature
    ```

### Writing Tests
**Trigger:** When verifying the functionality of modules  
**Command:** `/write-test`

1. Create a test file named after the module, ending with `.test.ts`.
    - Example: `userManager.test.ts`
2. Write tests using the project's preferred (unspecified) testing framework.
3. Use relative imports to bring in the module under test.
    ```typescript
    import { getUser } from './userManager';
    ```
4. Run tests using the project's test runner (see project documentation for details).

## Testing Patterns

- Test files follow the `*.test.ts` naming convention.
- Tests are colocated with the modules they test.
- Import modules under test using relative imports.
- The specific testing framework is not specified; follow project or team guidelines.

## Commands
| Command        | Purpose                                   |
|----------------|-------------------------------------------|
| /feature-dev   | Start a new feature using project patterns |
| /write-test    | Write and organize tests                   |
```
