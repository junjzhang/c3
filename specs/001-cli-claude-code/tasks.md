# Tasks: Claude Code Configuration Manager CLI

**Input**: Design documents from `/Users/zhangjunjie/c3/specs/001-cli-claude-code/`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory ✓
   → Extract: Python 3.11+, Pydantic, Typer, GitPython, Pixi
   → Structure: Single project (CLI tool)
2. Load optional design documents ✓:
   → data-model.md: 5 entities → 5 model tasks
   → contracts/: 6 CLI commands → 6 contract test tasks  
   → research.md: Technical decisions → setup tasks
3. Generate tasks by category ✓:
   → Setup: Pixi init, dependencies, linting (3 tasks)
   → Tests: contract tests, integration tests (8 tasks)
   → Core: models, libraries, CLI (13 tasks) 
   → Integration: Git, filesystem, CLI wiring (4 tasks)
   → Polish: unit tests, performance, docs (5 tasks)
4. Apply task rules ✓:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
5. Number tasks sequentially T001-T033 ✓
6. Generate dependency graph ✓
7. Create parallel execution examples ✓
8. Validate task completeness ✓:
   → All 6 CLI commands have contract tests ✓
   → All 5 entities have model tasks ✓
   → All tests before implementation ✓
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions  
- **Single project**: `src/`, `tests/` at repository root (per plan.md)
- All paths assume repository root at `/Users/zhangjunjie/c3/`

## Phase 3.1: Setup
- [ ] T001 Create project structure with Pixi environment in pyproject.toml
- [ ] T002 Initialize Python project with Pydantic, Typer, GitPython dependencies
- [ ] T003 [P] Configure linting (ruff, mypy) and formatting (black) tools

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**
- [ ] T004 [P] Contract test `c3cli install` command in tests/contract/test_cli_install.py
- [ ] T005 [P] Contract test `c3cli apply` command in tests/contract/test_cli_apply.py
- [ ] T006 [P] Contract test `c3cli list` command in tests/contract/test_cli_list.py
- [ ] T007 [P] Contract test `c3cli sync` command in tests/contract/test_cli_sync.py
- [ ] T008 [P] Contract test `c3cli status` command in tests/contract/test_cli_status.py
- [ ] T009 [P] Contract test `c3cli config` command in tests/contract/test_cli_config.py
- [ ] T010 [P] Integration test Git repository operations in tests/integration/test_git_operations.py
- [ ] T011 [P] Integration test filesystem operations (symlinks, copies) in tests/integration/test_filesystem_operations.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)
- [ ] T012 [P] Template Pydantic model in src/models/template.py
- [x] T013 Removed — superseded by CLIConfig + GitOperations (no implementation needed)
- [ ] T014 [P] DotfileLink Pydantic model in src/models/dotfile_link.py
- [ ] T015 [P] ProjectFile Pydantic model in src/models/project_file.py
- [ ] T016 [P] CLIConfig Pydantic model in src/models/cli_config.py
- [ ] T017 [P] Dotfiles library for symlink management in src/lib/dotfiles.py
- [ ] T018 [P] Templates library for file copying in src/lib/templates.py
- [ ] T019 [P] Git operations library in src/lib/git_ops.py
- [ ] T020 CLI install command implementation in src/cli/install_command.py
- [ ] T021 CLI apply command implementation in src/cli/apply_command.py
- [ ] T022 CLI list command implementation in src/cli/list_command.py
- [ ] T023 CLI sync command implementation in src/cli/sync_command.py
- [ ] T024 CLI status command implementation in src/cli/status_command.py

## Phase 3.4: Integration
- [ ] T025 Main CLI application with Typer in src/main.py
- [ ] T026 Configuration management and persistence in src/config/manager.py
- [ ] T027 Error handling and structured logging in src/utils/error_handler.py
- [ ] T028 CLI config command implementation in src/cli/config_command.py

## Phase 3.5: Polish
- [ ] T029 [P] Unit tests for Template model validation in tests/unit/test_template_model.py
- [ ] T030 [P] Unit tests for Git operations in tests/unit/test_git_ops.py
- [ ] T031 [P] Unit tests for filesystem operations in tests/unit/test_filesystem.py
- [ ] T032 Performance tests (<1s CLI operations, <5s sync) in tests/performance/test_performance.py
- [ ] T033 [P] Update CLAUDE.md with implementation details and usage examples

## Dependencies
```
Setup (T001-T003) → Tests (T004-T011) → Implementation (T012-T028) → Polish (T029-T033)

Detailed dependencies:
- T001,T002,T003 must complete before any other tasks
- T004-T011 must complete and FAIL before T012-T028
- T012-T016 (models) must complete before T017-T024 (libraries & CLI)
- T017-T019 (libraries) must complete before T020-T024 (CLI commands)
- T025-T028 (integration) requires T020-T024 (CLI commands)
- T029-T033 (polish) requires all implementation complete
```

## Parallel Example
```bash
# Phase 3.2: Launch all contract tests together (T004-T011):
Task: "Contract test c3cli install command in tests/contract/test_cli_install.py" 
Task: "Contract test c3cli apply command in tests/contract/test_cli_apply.py"
Task: "Contract test c3cli list command in tests/contract/test_cli_list.py"
Task: "Contract test c3cli sync command in tests/contract/test_cli_sync.py"
Task: "Contract test c3cli status command in tests/contract/test_cli_status.py"
Task: "Contract test c3cli config command in tests/contract/test_cli_config.py"
Task: "Integration test Git repository operations in tests/integration/test_git_operations.py"
Task: "Integration test filesystem operations in tests/integration/test_filesystem_operations.py"

# Phase 3.3: Launch Pydantic models (T012, T014-T016):
Task: "Template Pydantic model in src/models/template.py"
Task: "DotfileLink Pydantic model in src/models/dotfile_link.py"
Task: "ProjectFile Pydantic model in src/models/project_file.py"
Task: "CLIConfig Pydantic model in src/models/cli_config.py"

# Phase 3.3: Launch all libraries together (T017-T019):
Task: "Dotfiles library for symlink management in src/lib/dotfiles.py"
Task: "Templates library for file copying in src/lib/templates.py"
Task: "Git operations library in src/lib/git_ops.py"
```

## Notes
- [P] tasks = different files, no dependencies between them
- Verify all contract tests fail before implementing (TDD requirement)
- Commit after each task completion
- Use real Git repositories and filesystem operations in tests (no mocks)
- Follow Pydantic v2 patterns with type hints using built-in types (list, dict, not List, Dict)

## Task Generation Rules
*Applied during main() execution*

1. **From Contracts** ✓:
   - 6 CLI commands → 6 contract test tasks [P] (T004-T009)
   - Each command → implementation task (T020-T024, T028)
   
2. **From Data Model** ✓:
   - 5 entities → 5 model creation tasks [P] (T012-T016)
   - 3 libraries identified → 3 library tasks [P] (T017-T019)
   
3. **From User Stories** ✓:
   - Git operations → integration test [P] (T010)
   - Filesystem operations → integration test [P] (T011)
   - Performance requirements → performance tests (T032)

4. **Ordering** ✓:
   - Setup → Tests → Models → Libraries → CLI → Integration → Polish
   - Dependencies properly sequenced

## Validation Checklist
*GATE: Checked by main() before returning*

- [x] All 6 CLI commands have corresponding contract tests (T004-T009)
- [x] All 5 entities have model tasks (T012-T016)
- [x] All tests come before implementation (T004-T011 before T012-T028)
- [x] Parallel tasks truly independent (different files, marked [P])
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task
- [x] TDD enforced: contract tests must fail before implementation
- [x] Constitutional compliance: library-first, real dependencies, structured logging
