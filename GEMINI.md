# Gemini CLI Instructions

@AGENTS.md

---

## Gemini CLI-Specific Directives

### Execution Notes

- **SOT validation**: Before running any workflow, execute `python3 env-scanning/scripts/validate_registry.py` and confirm exit code 0.
- **Report validation**: After generating any report, execute `python3 env-scanning/scripts/validate_report.py <report_path> --profile <profile>` and confirm exit code 0.
- Validation profiles: `standard` (WF1/WF2), `naver` (WF3), `multiglobal-news` / `multiglobal-news_en` (WF4), `integrated`, `weekly`.

### File Search

When looking for configuration or data files, refer to the SOT at `env-scanning/config/workflow-registry.yaml` — it defines all paths. Never assume file locations.

### Report Generation

1. Read the appropriate skeleton template (paths listed in AGENTS.md Section 3.4)
2. Fill content into the skeleton structure — do NOT generate free-form
3. Run `validate_report.py` on the generated report
4. On failure: fix issues and re-validate (max 2 retries)

### Language

- Internal analysis and reasoning: English
- All report output and user-facing content: Korean
- STEEPs terminology must be preserved exactly during translation
- **WF4 multilingual pipeline**: WF4 scans 43 global news sites in 11 languages. Source articles are translated to English during Phase 1 collection, then the final report follows the standard English-first → Korean translation pipeline. Use `translation_validator.py` to verify structural integrity after translation.
