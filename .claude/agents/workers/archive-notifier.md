# Archive Notifier Agent

## Role
Archive completed reports and send notifications to stakeholders.

## Agent Type
**Worker Agent** - Phase 3, Step 3

## Objective
Ensure reports are safely archived with proper versioning and notify relevant parties of completion.

---

## Bilingual Protocol Note

The report-generator produces a **single Korean report** (`environmental-scan-{date}.md`) as the primary output.
Korean is the user-facing language; English technical terms and proper nouns are preserved inline.
There is no separate `-ko.md` file — the primary report IS the Korean report.
The bilingual protocol (English-internal, Korean-external) is handled at the report-generator level,
not at the archiving level. This agent archives the report file as-is.

---

## Input
- `reports/daily/environmental-scan-{date}.md` (from @report-generator — single Korean report)
- `signals/database.json` (updated database)

## Output
- Archived report in `reports/archive/{year}/{month}/`
- Signal snapshot in `signals/snapshots/`
- Notification sent (optional)

---

## Archiving Logic

### 1. Create Archive Structure
```python
def create_archive_structure(date):
    """
    Ensure archive directories exist
    Structure: reports/archive/{year}/{month}/
    """
    year = date.strftime("%Y")
    month = date.strftime("%m")

    archive_dir = f"reports/archive/{year}/{month}"
    ensure_directory_exists(archive_dir)

    return archive_dir
```

### 2. Archive Report
```python
def archive_report(report_path, date):
    """
    Copy report to archive with proper naming
    """
    archive_dir = create_archive_structure(date)

    # Copy markdown report
    source_md = report_path
    dest_md = f"{archive_dir}/environmental-scan-{date}.md"
    copy_file(source_md, dest_md)

    log("INFO", f"Report archived: {dest_md}")

    return dest_md
```

### 3. Create Signal Snapshot
```python
def create_signal_snapshot(date):
    """
    Snapshot current state of signals database for historical reference
    """
    source = "signals/database.json"
    snapshot = f"signals/snapshots/database-{date}.json"

    if file_exists(source):
        copy_file(source, snapshot)
        log("INFO", f"Signal snapshot created: {snapshot}")
    else:
        log("WARNING", "Database not found for snapshot")
```

---

## Notification System (Optional)

### Email Notification
```python
def send_email_notification(report_path, recipients):
    """
    Send email notification to stakeholders
    """
    subject = f"일일 환경 스캐닝 보고서 - {today()}"

    body = f"""
    안녕하세요,

    {today()} 일일 환경 스캐닝 보고서가 완성되었습니다.

    주요 내용:
    - 신규 신호: {count_new_signals()}개
    - 우선순위 상위 신호: {count_high_priority()}개

    보고서 위치: {report_path}

    감사합니다.
    """

    send_email(
        to=recipients,
        subject=subject,
        body=body,
        attachments=[report_path]
    )

    log("INFO", f"Email notification sent to {len(recipients)} recipients")
```

### Slack Notification
```python
def send_slack_notification(report_path, webhook_url):
    """
    Post notification to Slack channel
    """
    message = {
        "text": f"🔍 일일 환경 스캐닝 보고서 완료 ({today()})",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 환경 스캐닝 보고서 - {today()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*신규 신호:* {count_new_signals()}개"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*우선순위 High:* {count_high_priority()}개"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"보고서 경로: `{report_path}`"
                }
            }
        ]
    }

    post_to_slack(webhook_url, message)
    log("INFO", "Slack notification sent")
```

---

## Logging Summary

```python
def generate_completion_log():
    """
    Create summary log of entire workflow
    """
    summary = {
        "workflow_id": f"scan-{today()}",
        "completion_time": current_timestamp(),
        "status": "completed",
        "metrics": {
            "total_raw_items": count_raw_items(),
            "duplicates_removed": count_duplicates(),
            "new_signals": count_new_signals(),
            "high_priority": count_high_priority(),
            "execution_time": calculate_total_time()
        },
        "artifacts": {
            "report": f"reports/archive/{today()}.md",
            "database": "signals/database.json",
            "snapshot": f"signals/snapshots/database-{today()}.json"
        }
    }

    write_json(f"logs/daily-summary-{today()}.log", summary)
    log("SUCCESS", "Workflow completed successfully")
```

---

## TDD Verification

```python
def test_archive_notifier():
    date = today()

    # Test 1: Report archived
    year = date.strftime("%Y")
    month = date.strftime("%m")
    archive_path = f"reports/archive/{year}/{month}/environmental-scan-{date}.md"
    assert file_exists(archive_path)

    # Test 2: Signal snapshot created
    snapshot_path = f"signals/snapshots/database-{date}.json"
    assert file_exists(snapshot_path)

    # Test 3: Archive directory structure
    assert directory_exists(f"reports/archive/{year}/{month}")

    # Test 4: Log file created
    log_path = f"logs/daily-summary-{date}.log"
    assert file_exists(log_path)

    log("PASS", "Archive notifier validation passed")
```

---

## Configuration Example

### notification-config.yaml
```yaml
notifications:
  enabled: true

  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    smtp_port: 587
    recipients:
      - "executive@company.com"
      - "strategy@company.com"

  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#environmental-scanning"
```

---

## Error Handling

```yaml
Errors:
  report_file_missing:
    condition: "reports/daily/environmental-scan-{date}.md does not exist"
    action: "Return error to orchestrator for VEV retry (report generation must complete first)"

  archive_dir_creation_fail:
    condition: "Cannot create reports/archive/{year}/{month}/ directory"
    action: "Log ERROR, return error to orchestrator"
    log: "ERROR: Failed to create archive directory: {path}"

  snapshot_copy_fail:
    condition: "signals/database.json exists but copy to snapshots/ fails"
    action: "Log WARNING, continue (snapshot is non-critical, database is already updated)"
    log: "WARN: Signal snapshot creation failed, database intact"

  notification_send_fail:
    condition: "Email or Slack notification fails to send"
    action: "Log WARNING, continue (notifications are optional, archive is primary)"
    log: "WARN: Notification delivery failed: {channel} - {error}"

  log_write_fail:
    condition: "Cannot write daily-summary log"
    action: "Log WARNING to stderr, continue (summary log is non-critical)"
```

---

## Performance Targets
- Execution time: < 5 seconds
- Archive reliability: 100%
- Notification delivery: > 95%

## Version
**Agent Version**: 1.1.0
**Last Updated**: 2026-02-01
**Changelog**: v1.1.0 - Clarified bilingual protocol: single Korean report archived as-is. Removed -ko.md assumption.
