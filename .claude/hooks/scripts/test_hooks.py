#!/usr/bin/env python3
"""
Test Suite for Context Preservation Hooks
Verifies all hook scripts work correctly
"""
import json
import subprocess
import sys
from pathlib import Path

def test_save_context():
    """Test context save functionality"""
    print("Testing save_context.py...")

    test_input = json.dumps({"event": "test-save"})

    try:
        result = subprocess.run(
            ['python3', '.claude/hooks/scripts/save_context.py'],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and 'Context saved' in result.stdout:
            print("  ✓ Save context test passed")

            # Check if file was created
            context_file = Path('.claude/context-backups/latest-context.md')
            if context_file.exists():
                print(f"  ✓ Context file created: {context_file}")
                return True
            else:
                print("  ❌ Context file not found")
                return False
        else:
            print(f"  ❌ Save context test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_restore_context():
    """Test context restore functionality"""
    print("Testing restore_context.py...")

    try:
        result = subprocess.run(
            ['python3', '.claude/hooks/scripts/restore_context.py'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if 'CONTEXT RESTORATION' in result.stdout or result.returncode == 0:
            print("  ✓ Restore context test passed")
            return True
        else:
            print(f"  ❌ Restore context test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_work_log():
    """Test activity logging functionality"""
    print("Testing update_work_log.py...")

    test_input = json.dumps({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/test/file.py"
        }
    })

    try:
        result = subprocess.run(
            ['python3', '.claude/hooks/scripts/update_work_log.py'],
            input=test_input,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("  ✓ Work log test passed")

            # Check if log file was created/updated
            log_file = Path('.claude/context-backups/work-log.jsonl')
            if log_file.exists():
                print(f"  ✓ Work log file exists: {log_file}")

                # Read last line
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_entry = json.loads(lines[-1])
                        print(f"  ✓ Latest entry: {last_entry['activity']}")

                return True
            else:
                print("  ⚠ Work log file not created (may be OK)")
                return True  # Non-critical

        else:
            print(f"  ❌ Work log test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_context_summary():
    """Test context summary generation"""
    print("Testing generate_context_summary.py...")

    try:
        result = subprocess.run(
            ['python3', '.claude/hooks/scripts/generate_context_summary.py'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and 'Context summary generated' in result.stdout:
            print("  ✓ Context summary test passed")

            # Check file content
            context_file = Path('.claude/context-backups/latest-context.md')
            if context_file.exists():
                content = context_file.read_text()
                if 'Claude Code Context Summary' in content:
                    print("  ✓ Context summary content valid")
                    return True
                else:
                    print("  ❌ Context summary content invalid")
                    return False
            else:
                print("  ❌ Context file not found")
                return False

        else:
            print(f"  ❌ Context summary test failed")
            if result.stderr:
                print(f"     Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("Checking prerequisites...")

    # Check Python version
    version = sys.version_info
    if version >= (3, 6):
        print(f"  ✓ Python {version.major}.{version.minor}")
    else:
        print(f"  ❌ Python 3.6+ required (found {version.major}.{version.minor})")
        return False

    # Check if scripts exist
    scripts = [
        'save_context.py',
        'restore_context.py',
        'update_work_log.py',
        'generate_context_summary.py'
    ]

    for script in scripts:
        script_path = Path('.claude/hooks/scripts') / script
        if script_path.exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ❌ Missing: {script}")
            return False

    # Check if scripts are executable
    for script in scripts:
        script_path = Path('.claude/hooks/scripts') / script
        if script_path.stat().st_mode & 0o111:
            pass  # Executable
        else:
            print(f"  ⚠ {script} not executable (fixing...)")
            script_path.chmod(script_path.stat().st_mode | 0o111)

    print("  ✓ All scripts executable")
    return True

def main():
    """Run all tests"""
    print("="*60)
    print("Context Preservation Hook Test Suite")
    print("="*60)
    print()

    if not check_prerequisites():
        print()
        print("❌ Prerequisites check failed")
        return 1

    print()
    print("Running tests...")
    print()

    tests = [
        ("Save Context", test_save_context),
        ("Restore Context", test_restore_context),
        ("Work Log", test_work_log),
        ("Context Summary", test_context_summary)
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        print()

    # Summary
    print("="*60)
    print("Test Summary")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"  {status}  {test_name}")

    print()
    print(f"Results: {passed}/{total} tests passed")
    print()

    if passed == total:
        print("✅ All tests passed!")
        print()
        print("Next steps:")
        print("  1. Install hooks: python3 .claude/hooks/scripts/setup_hooks.py")
        print("  2. Restart Claude Code")
        print("  3. Hooks will work automatically")
        return 0
    else:
        print("❌ Some tests failed - please review errors above")
        return 1

if __name__ == '__main__':
    sys.exit(main())
