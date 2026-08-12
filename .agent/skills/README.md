# Project-Specific AI Skills

This directory contains **Agentic Skills** designed specifically for the Precision Medicine MCP project.

## What are Agentic Skills?

Agentic Skills are structured instruction sets (Markdown files) that enhance the capabilities of AI coding assistants (like Antigravity, Claude Code, or Gemini CLI). They allow the AI to:
- Follow project-specific architectural patterns.
- Onboard faster to complex datasets (scRNA-seq, GEARS).
- Maintain consistency across 16+ MCP servers.

## How to Use These Skills

 Once you have downloaded the project and opened it in an environment with an agentic AI assistant (e.g., Cursor, Claude Code, Antigravity):

1.  **Automatic Detection**: The AI automatically reads the `.agent/skills/` directory on startup. You don't need to manually import or reference the files.
2.  **Natural Language Activation**: Simply mention the skill name or the domain you're working on. For example:
    - *"Use the **@universal-collaboration** skill to create a PR description for my genomics changes."*
    - *"I need to build a new server. Follow **@precision-bio-mcp** to set up the boilerplate."*
    - *"We are processing new patient data. Use **@patient-data-ops** to ensure compliance and proper normalization."*
    - *"I'm writing a clinical report. Use **@precision-bio-docs** for the correct persona template."*
3.  **Active Guidance**: During code execution, you can ask, *"Is this compliant with our **@clinical-compliance-doc** skill?"* and the AI will audit your code against the stored standards.

## Orchestration vs. Direct Calling

This library supports two primary modes of interaction:

- **The Orchestrator (`@universal-collaboration`)**: This is the primary entry point for general engineering workflows. It "governs" the project by routing complex tasks to specialized skills. For example, if you ask it to scaffold a server, it enforces the directory pattern from its own list and then pulls technical specs from `@precision-bio-mcp`.
- **Direct Calling**: Experienced developers or researchers can call specialized skills directly for targeted tasks (e.g., using `@patient-data-ops` for specific H5AD normalization).

### Skill Comparison & Roles

To prevent confusion, use this table to choose the right entry point:

| Skill | Primary Role | Stakeholder | Key Sub-Skills |
| :--- | :--- | :--- | :--- |
| **@universal-collaboration** | **Orchestrator** | PR Reviewers / Team | ADRs, PR hygiene, Test scaffolding. |
| **@precision-bio-mcp** | **Tech Specification** | Developers | `uv` packages, Server structure, Docker. |
| **@patient-data-ops** | **Bio-Data Engine** | Bioinformaticians | H5AD loading, GEARS normalization. |
| **@precision-bio-ui** | **Frontend Studio** | UI/UX Engineers | Streamlit, Trace visuals, Providers. |
| **@precision-bio-tests** | **QA / Validation** | QA Engineers | PatientOne scenarios, DRY_RUN logic. |
| **@precision-bio-docs** | **Reporting / Editorial** | Researchers / Ops | Persona-based docs, Mermaid, Registry. |
| **@clinical-compliance-doc** | **Governance / Security** | Compliance Officer | HIPAA, Audit logs, Infrastructure logs. |
| **@precision-compliance-standards** | **Science Guardrails** | Principal Scientist | Gene nomenclature, Bio-validation. |
| **@universal-collaboration** | **Project Onboarding** | New Contributors | Getting Started guides, Context sync. |

---

## What to Expect After Using These Skills

By utilizing these project-specific skills, contributors can expect:

- **Consistency**: All 16+ MCP servers will maintain identical structures, logging, and error-handling patterns, making them easier to debug and scale.
- **Scientific Accuracy**: AI assistants will adhere to the project's specific bioinformatics parameters (e.g., 7000 HVGs, specific normalization steps) without needing constant re-instruction.
- **Audit Readiness**: Documentation and code will automatically align with clinical security standards (HIPAA/PHI safeguards), reducing review time for senior engineers.
- **Faster Onboarding**: New developers can become productive in minutes by relying on the AI to explain and implement the complex "tribal knowledge" codified in these files.

## Skill Directory Structure

- `.agent/skills/README.md`: This file.
- `.agent/skills/[skill-name]/SKILL.md`: The core instruction set for each skill.

## Benefit for Contributors

These skills codify the "tribal knowledge" of the project—standardizing how we handle patient data, how we structure our servers, and how we ensure clinical compliance. They act as automated senior-engineer mentorship for anyone joining the project.
