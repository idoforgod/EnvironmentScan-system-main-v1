#!/usr/bin/env python3
"""
Comprehensive Context Summary Generator
Creates a detailed summary of current project state for context preservation.
"""
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

def get_project_root():
    """Get the project root directory"""
    return os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

def get_git_status():
    """Get current git status"""
    try:
        project_root = get_project_root()

        # Get branch
        branch = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        ).stdout.strip()

        # Get modified files
        modified = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        ).stdout

        # Get recent commits
        recent_commits = subprocess.run(
            ['git', 'log', '--oneline', '-5'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        ).stdout

        return {
            'branch': branch,
            'modified_files': modified,
            'recent_commits': recent_commits
        }
    except Exception as e:
        return {'error': str(e)}

def get_recent_activities():
    """Read recent work log entries"""
    try:
        project_root = get_project_root()
        log_file = Path(project_root) / '.claude' / 'context-backups' / 'work-log.jsonl'

        if not log_file.exists():
            return []

        activities = []
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Get last 20 activities
            for line in lines[-20:]:
                try:
                    activities.append(json.loads(line))
                except:
                    pass

        return activities
    except Exception:
        return []

def get_project_files_overview():
    """Get overview of project files"""
    try:
        project_root = get_project_root()

        # Count files by extension
        file_counts = {}
        for root, dirs, files in os.walk(project_root):
            # Skip hidden and common ignored directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]

            for file in files:
                if file.startswith('.'):
                    continue
                ext = Path(file).suffix or 'no_extension'
                file_counts[ext] = file_counts.get(ext, 0) + 1

        return file_counts
    except Exception as e:
        return {'error': str(e)}

def generate_summary():
    """Generate comprehensive context summary"""
    project_root = get_project_root()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"""# Claude Code Context Summary
**Project**: {project_root}
**Generated**: {timestamp}

---

## 🎯 Current Project State

### Git Repository Status
"""

    git_status = get_git_status()
    if 'error' not in git_status:
        summary += f"""
**Branch**: `{git_status['branch']}`

**Modified Files**:
```
{git_status['modified_files'] or '(No changes)'}
```

**Recent Commits**:
```
{git_status['recent_commits']}
```
"""
    else:
        summary += f"\n(Git status unavailable: {git_status['error']})\n"

    # Recent activities
    summary += "\n### 📝 Recent Activities\n\n"
    activities = get_recent_activities()
    if activities:
        summary += "| Time | Tool | Activity |\n"
        summary += "|------|------|----------|\n"
        for act in activities[-10:]:  # Last 10
            time = datetime.fromisoformat(act['timestamp']).strftime('%H:%M:%S')
            summary += f"| {time} | {act['tool']} | {act['activity']} |\n"
    else:
        summary += "(No recent activities logged)\n"

    # Project overview
    summary += "\n### 📁 Project Files Overview\n\n"
    file_counts = get_project_files_overview()
    if 'error' not in file_counts:
        summary += "| Extension | Count |\n"
        summary += "|-----------|-------|\n"
        for ext, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            summary += f"| {ext} | {count} |\n"

    # Key directories
    summary += "\n### 📂 Key Directories\n\n"
    key_dirs = [
        'env-scanning',
        '.claude',
        'tests',
        'docs',
        'scripts'
    ]

    for dir_name in key_dirs:
        dir_path = Path(project_root) / dir_name
        if dir_path.exists():
            summary += f"- ✓ `{dir_name}/`\n"
        else:
            summary += f"- ✗ `{dir_name}/` (not found)\n"

    # Critical files
    summary += "\n### 📄 Critical Files\n\n"
    critical_files = [
        'README.md',
        'IMPLEMENTATION_GUIDE.md',
        'env-scanning/FILE_INDEX.md',
        '.claude/agents/env-scan-orchestrator.md'
    ]

    for file_name in critical_files:
        file_path = Path(project_root) / file_name
        if file_path.exists():
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            summary += f"- ✓ `{file_name}` (modified: {mod_time})\n"
        else:
            summary += f"- ✗ `{file_name}` (not found)\n"

    summary += """
---

## 💡 Context Preservation Instructions

**For Claude Code**: When you read this file after a context clear/compression:

1. **Scan Recent Activities** - Review what tools were used and what was modified
2. **Check Git Status** - Understand current working state
3. **Review Modified Files** - Read recent changes to rebuild context
4. **Check Project Overview** - Understand project structure

**Key Principle**: This file is your memory anchor. Use it to rebuild full working context quickly.

---

## 📋 Workflow State Tracking

### Current Phase
<!-- Manually update this section with current workflow phase -->

**Phase**: (Update this during workflow)
**Status**: (Update this during workflow)
**Next Steps**: (Update this during workflow)

### Active Tasks
<!-- List active tasks here -->

### Blockers & Issues
<!-- Note any blockers or issues -->

### Key Decisions Made
<!-- Document important architectural or implementation decisions -->

---

**Auto-generated by**: Claude Code Context Preservation System
**Version**: 1.0.0
"""

    return summary

if __name__ == '__main__':
    try:
        summary = generate_summary()

        # Save to context file
        project_root = get_project_root()
        context_file = Path(project_root) / '.claude' / 'context-backups' / 'latest-context.md'
        context_file.parent.mkdir(parents=True, exist_ok=True)

        with open(context_file, 'w', encoding='utf-8') as f:
            f.write(summary)

        print(f"✓ Context summary generated: {context_file}")

        # Also print to stdout for immediate viewing
        print("\n" + "="*60)
        print(summary)
        print("="*60)

    except Exception as e:
        print(f"❌ Error generating context summary: {e}")
        import traceback
        traceback.print_exc()
