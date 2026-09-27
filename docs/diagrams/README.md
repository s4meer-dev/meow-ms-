# Downloadable Mermaid Diagrams

This folder contains the Mermaid source files used by the README and project report.

How to use them:

1. Open any `.mmd` file.
2. Copy it into Mermaid Live Editor, VS Code Mermaid Preview, or Mermaid CLI.
3. Export as SVG, PNG, or PDF for resumes, project reports, LinkedIn posts, or interview presentations.

Recommended export command with Mermaid CLI:

```bash
npx @mermaid-js/mermaid-cli -i docs/diagrams/01_high_level_architecture.mmd -o architecture.svg
```

## Files

| File | Purpose |
|---|---|
| `01_high_level_architecture.mmd` | End-to-end system architecture |
| `02_complete_request_flow.mmd` | Ticket-to-draft sequence flow |
| `03_code_flow.mmd` | Code/module responsibility flow |
| `04_ai_draft_generation_pipeline.mmd` | AI draft generation pipeline |
| `05_knowledge_base_ingestion.mmd` | RAG ingestion flow |
| `06_data_model.mmd` | SQLite data model |
| `07_memory_and_tool_calling.mmd` | Memory and tool-calling flow |
| `08_production_architecture.mmd` | Production-ready target architecture |
| `09_deployment_flow.mmd` | Docker Compose deployment flow |
| `10_accuracy_metrics.mmd` | System accuracy evaluation map |
