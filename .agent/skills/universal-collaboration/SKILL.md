---
name: universal-collaboration
description: Best-practice agent skills for multi-contributor software projects. Use this skill set for onboarding, PR reviews, generating ADRs, and maintaining consistent engineering patterns.
---

# Universal Collaboration Skill

This skill guides consistent, high-quality collaboration across any engineering team. It ensures that every contributor — regardless of experience level — produces work that meets the project's architectural and collaboration standards.

## 🚀 How to Use This Skill

You can invoke this skill or its sub-skills naturally:
- **Project-wide**: *"Use **@universal-collaboration** to review my current changes."*
- **Specific Sub-skills**:
    - *"Generate a PR description using **@universal-collaboration** patterns."*
    - *"Draft an ADR for the new module following **@universal-collaboration** styles."*
    - *"Review the code structure using **@universal-collaboration** checks."*

## 🔄 Collaboration vs. Technical Implementation

To prevent confusion, use this table to choose the right skill for your task:

| Feature | **@universal-collaboration** | **@precision-bio-mcp** |
| :--- | :--- | :--- |
| **Primary Focus** | Team workflow and PR hygiene. | Technical server implementation. |
| **When to Use** | Onboarding, PRs, ADRs, Test scaffolding. | Creating/Refactoring MCP servers. |
| **Server Pattern** | Defines *where* things go (Paths/Naming). | Defines *how* things work (`uv`, `mcp` SDK). |
| **Compliance** | Workflow triggers (Checks & Notes). | Technical data validation logic. |
| **Testing** | General coverage and scenario patterns. | Specific `pytest` setups and bio-mocking. |

---

## Sub-Skill 1: Code Review & Quality
**Purpose**: Enforce consistent patterns across contributed code before human review.
**When to trigger**: Any new PR or significant code modification.

**What to check**:
- **Design Patterns**: Ensure code follows the project's established patterns (e.g., MCP tool registration, standardized decorators).
- **Naming**: Consistent variable, function, and file naming across the codebase.
- **Reliability**: Proper error handling, input validation, and logging.
- **Cleanliness**: No dead code, commented-out blocks, or unresolved TODOs.

---

## Sub-Skill 2: Architecture Decision Records (ADR)
**Purpose**: Capture the *why* behind significant technical decisions to preserve context.
**When to trigger**: Any time a non-obvious technical choice is made regarding dependencies or infrastructure.

**Storage convention**: Place ADRs in `docs/reference/architecture/decisions/` numbered sequentially (e.g., `ADR-0001-chose-mcp-over-rest.md`).

**Standard Structure**:
- **Status**: [Proposed | Accepted | Deprecated | Superseded]
- **Context**: What problem or situation prompted this decision?
- **Decision**: What was decided? State it clearly.
- **Alternatives**: What other options were considered and why were they rejected?
- **Consequences**: What becomes easier? What technical debt is introduced?

---

## Sub-Skill 3: Test Generation & Coverage
**Purpose**: Reduce friction for contributors by scaffolding consistent tests.
**When to trigger**: When adding new functions or classes.

**Style Rules**:
- **Naming**: Match the naming convention of existing tests exactly.
- **Isolation**: Each test should be independently runnable with no shared mutable state.
- **Scenarios**: Include happy path, edge cases (empty inputs, bounds), and failure paths.

---

## Sub-Skill 4: Onboarding & Summarization
**Purpose**: Help new contributors reach productivity faster via synthesized guides.
**When to trigger**: When a team member joins or moves to an unfamiliar module.

**Output**: A concise "Getting Started" summary that links to primary entry points (`INDEX.md`, `README.md`) rather than duplicating them.

---

## Sub-Skill 5: PR Description & Commit Quality
**Purpose**: Ensure git history and PR records serve as a reliable audit trail.

**PR Structure**:
- **What Changed**: Concise summary of additions/modifications.
- **Why**: The problem being solved or feature being added.
- **How to Test**: Step-by-step instructions for the reviewer.
- **Checklist**: Tests added, docs updated, no hardcoded secrets.

**Commit Messages**:
- Use imperative mood: "Add module" not "Added module".
- First line ≤ 72 characters.

---

## Sub-Skill 6: Scaffolding New MCP Servers
**Purpose**: Ensure every new tool or service follows the project's containerized architecture.
**When to trigger**: When a contributor is tasked with adding a new data source, model, or utility as an MCP server.

**Implementation Guide**:
For the authoritative technical specification of the server structure, dependency management (`uv`), and deployment patterns, always follow the **@precision-bio-mcp** skill.

**Core Patterns to Enforce**:
- **Separation**: Logic should be in `src/mcp_[name]/`, not the root.
- **Naming**: Folder: `mcp-[dashed-name]`,- Package: `mcp_[underscored_name]`
- Tool names: `verb_noun` (e.g., `predict_perturbation`).

---

## Sub-Skill 7: Skill Testing & Validation
**Purpose**: Verify that a new skill's instructions result in the correct AI behavior and output quality.
**When to trigger**: After creating or significantly modifying a `SKILL.md` file.

**"Skill Unit Test" Pattern**:
To test a skill, provide the AI with a "Test Scenario" consisting of:
1. **Context**: A mock project state or set of files.
2. **Action**: A prompt invoking the skill (e.g., *"Use @your-skill to..."*).
3. **Assertions**: A list of mandatory qualities the output must possess.

**Validation Checklist**:
- **Discovery**: Is the skill's `name` and `description` in the YAML frontmatter clear enough for the AI to pick it up?
- **Logic**: Are the instructions imperative and unambiguous?
- **Referencing**: Does the skill correctly link to other skills or project paths?
- **Output Quality**: Does the AI's response adhere to the naming, structural, and compliance rules defined in the skill?

**Example Test Case**:
- **Subject**: `@precision-bio-mcp`
- **Prompt**: "Scaffold a new server for RNA-seq analysis."
- **Verification**: Does the result contain `deploy.sh`? Is the package named `mcp_rna_seq`? Does it reference `shared/common/logging.py`?
