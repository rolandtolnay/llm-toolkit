# AST Tools

## What This Replaces

Nothing directly — Claude Code has no built-in AST tooling. This is inspired by oh-my-pi's `ast_grep` and `ast_edit` tools, which provide syntax-aware code search and transformation.

## Why I Need It

`grep` finds text patterns. AST tools find code structures. The difference matters for:

- **Structural search**: "find all `setState()` calls inside `build()` methods" — impossible with regex, trivial with AST patterns
- **Rename-safe refactoring**: rename a method across files without catching string literals or comments that happen to contain the same text
- **Cross-language consistency**: same pattern syntax works across Dart, TypeScript, Java, Vue, etc.

The underlying tool is [ast-grep](https://ast-grep.github.io/) (`sg` CLI), which uses tree-sitter parsers for 20+ languages.

## How AST Search Differs from Grep and LSP

| Capability | grep/ripgrep | ast-grep | LSP |
|------------|-------------|----------|-----|
| Find text matches | Yes | No | No |
| Find code patterns | Regex only | Structural | Yes |
| Cross-file rename | No | Yes (rewrite rules) | Yes |
| Needs running server | No | No | Yes |
| Language-aware | No | Yes (tree-sitter) | Yes |
| Setup cost | Zero | Install binary | Per-language server |

ast-grep fills the gap between "dumb text search" and "full IDE server" — structural code awareness without persistent infrastructure.

## Pi API Surface

Register two tools via `pi.registerTool()` that wrap the `sg` CLI.

## Implementation: Extension (~50 lines)

```typescript
// ~/.pi/agent/extensions/ast-tools.ts
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { execSync } from "child_process";

export default function (pi: ExtensionAPI) {
  pi.registerTool("ast_search", {
    description: "Search code using structural AST patterns (not regex). Use for finding specific code constructs like function calls, class definitions, or import patterns.",
    parameters: {
      type: "object",
      properties: {
        pattern: { type: "string", description: "ast-grep pattern (use $VAR for wildcards)" },
        lang: { type: "string", description: "Language: dart, typescript, java, vue, etc." },
        path: { type: "string", description: "Directory or file to search (default: current dir)" },
      },
      required: ["pattern", "lang"],
    },
    async execute(input) {
      const path = input.path || ".";
      try {
        const result = execSync(
          `sg --pattern '${input.pattern}' --lang ${input.lang} ${path}`,
          { timeout: 15000, encoding: "utf-8", maxBuffer: 1024 * 1024 }
        );
        return { content: [{ type: "text", text: result || "No matches found." }] };
      } catch (e: any) {
        return { content: [{ type: "text", text: e.stdout || e.stderr || "No matches found." }] };
      }
    },
  });

  pi.registerTool("ast_replace", {
    description: "Replace code using structural AST patterns. Safer than text-based find/replace — only matches actual code structures, not strings or comments.",
    parameters: {
      type: "object",
      properties: {
        pattern: { type: "string", description: "ast-grep pattern to match" },
        rewrite: { type: "string", description: "Replacement pattern (use $VAR to reference captures)" },
        lang: { type: "string", description: "Language: dart, typescript, java, vue, etc." },
        path: { type: "string", description: "Directory or file to transform" },
      },
      required: ["pattern", "rewrite", "lang", "path"],
    },
    async execute(input) {
      try {
        const result = execSync(
          `sg --pattern '${input.pattern}' --rewrite '${input.rewrite}' --lang ${input.lang} ${input.path} --update-all`,
          { timeout: 15000, encoding: "utf-8", maxBuffer: 1024 * 1024 }
        );
        return { content: [{ type: "text", text: result || "Replacement applied." }] };
      } catch (e: any) {
        return { content: [{ type: "text", text: e.stderr || "Replacement failed." }] };
      }
    },
  });
}
```

### Prerequisites

Install ast-grep: `npm i -g @ast-grep/cli` or `cargo install ast-grep`.

### Example patterns

| Task | Pattern | Language |
|------|---------|----------|
| Find all setState calls | `setState($$$)` | dart |
| Find unused imports | `import '$VAR';` | dart |
| Find async functions | `async function $NAME($$$) { $$$ }` | typescript |
| Find React useState hooks | `const [$A, $B] = useState($$$)` | tsx |
| Find try-catch without logging | `try { $$$ } catch ($E) { }` | typescript |

`$VAR` matches a single node, `$$$` matches zero or more nodes.

## Status: Researched — Build in Week 2
