---
name: precision-bio-ui
description: >
  Expert guide for developing the Precision Medicine Streamlit dashboard and LLM providers.
  Covers provider abstraction, trace visualization, and UI components.
---

# Precision Bio-UI Development

This skill guides the development of the frontend and LLM orchestration layer of the platform.

## 🖼️ Dashboard Architecture

The UI is built with Streamlit and follows a modular provider-based architecture:
- `ui/streamlit-app/app.py`: Main entry point.
- `ui/streamlit-app/providers/`: Abstracted LLM orchestration (Claude, Gemini).
- `ui/streamlit-app/utils/`: Visualization, GCS handling, and trace logic.

## 🤖 Provider Development

When adding or modifying LLM providers:
1.  **Base Class**: Extend `providers/base.py`.
2.  **Streaming**: Implement `generate_response_stream` for a better user experience.
3.  **Trace Extraction**: Use `trace_utils.py` to ensure tool calls are correctly recorded for the orchestration trace.

## 📊 Visualization & Traces

- **Orchestration Trace**: Supports Log, Card, Timeline, and Sequence Diagram (Mermaid) views.
- **Bio-Data Rendering**: Use Streamlit's `st.dataframe` for large genomic tables and `st.image` for GCS-hosted UMAPs/PCA plots.
- **Complexity**: Keep the sidebar clean—use `st.expander` for advanced settings like n_latent or n_hvg.

## ⚙️ Configuration

- Ensure all new features are togglable via `.env` or the sidebar (e.g., `USE_MOCK_MCP`).
- Maintain the 14+ example prompts in `utils/mcp_config.py`.

---

**Use this skill when:**
- Adding a new LLM provider (e.g., DeepSeek, Llama).
- Modifying the orchestration trace visualization.
- Adding new file upload handlers or GCS widgets.
