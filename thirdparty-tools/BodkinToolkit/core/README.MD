# core

Shared infrastructure library used by every tool. **Not a CLI tool** - it has
no entry point and no verbs; it holds only generic, game-agnostic helpers so
tools don't duplicate them.

## Modules

| Module | Provides |
|---|---|
| `args` | `build_parser`, `add_verb`, `parse_or_help`, `print_help_summary`, `resolve_out_target` - standard `?` help, `--out`, `--yes`. |
| `prompt` | `select_one/many`, `text`, `confirm`, `confirm_destructive`, `Cancelled` - interactive prompts with non-TTY fallback. |
| `io` | `atomic_write_text` (tmp -> validate -> replace), `read_text_safe`, `ensure_dir`. |
| `out` | `emit` / `error` + `--out` file sink. All human output routes through here. |
| `proc` | `run_tool` / `run_entry` - invoke another tool/pipeline by its front (absolute path), the single cross-tool calling mechanism. |
| `paths` | project-internal locations: `V3_ROOT`, `WORLD_DIR`, `JSON_DIR`, `YAML_DIR`, `BACKUPS_DIR`, `RESEARCH_DIR`, `WORK_DIR`, `DEFAULT_BUNDLE`, `GAME_ROOT_FILE`, `tool_root()`. All under `/v3/`. |

`core` knows nothing about tables, fields, schema, or the game. It holds no
mutable global state. Tools import it; it imports no tool.
