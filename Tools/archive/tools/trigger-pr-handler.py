#!/usr/bin/env python3
"""
GitHub Actions Workflow Dispatcher for PR Handling
Triggers the handle-six-prs.yml workflow to process 6 open PRs
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_command(cmd, capture=True):
    """Execute shell command and return result"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode, result.stdout, result.stderr
        else:
            return subprocess.run(cmd, shell=True).returncode
    except Exception as e:
        return -1, "", str(e)

def check_git_status():
    """Check if we're in a git repo and on the right branch"""
    code, out, err = run_command("git rev-parse --is-inside-work-tree")
    if code != 0:
        print("❌ Not in a git repository")
        return False
    
    code, branch, err = run_command("git branch --show-current")
    print(f"📍 Current branch: {branch.strip()}")
    return True

def trigger_pr_workflow():
    """Trigger the GitHub Actions workflow for PR handling"""
    print("🚀 Triggering GitHub Actions workflow: handle-six-prs.yml")
    print("=" * 60)
    
    # Check if we can use gh CLI
    code, _, _ = run_command("which gh")
    if code == 0:
        print("✅ GitHub CLI available - triggering workflow...")
        
        # Trigger the workflow
        cmd = "gh workflow run handle-six-prs.yml --ref development"
        code, out, err = run_command(cmd)
        
        if code == 0:
            print("✅ Workflow triggered successfully!")
            print(f"📊 Output: {out}")
            
            # Get workflow status
            print("\n🔍 Checking workflow runs...")
            code, runs, _ = run_command("gh run list --workflow=handle-six-prs.yml --limit=1")
            if code == 0:
                print("Latest workflow runs:")
                print(runs)
        else:
            print(f"❌ Failed to trigger workflow: {err}")
    else:
        print("⚠️ GitHub CLI not available")
        print("Manual trigger required:")
        print("")
        print("1. Push this branch to GitHub:")
        print("   git push origin development")
        print("")
        print("2. Go to GitHub Actions tab")
        print("3. Find 'Handle Six Open PRs - Targeted Actions' workflow")
        print("4. Click 'Run workflow' button")
        print("")

def create_pr_tracking_file():
    """Create a tracking file for PR processing"""
    tracking_data = {
        "timestamp": datetime.now().isoformat(),
        "workflow_triggered": True,
        "target_prs": 6,
        "workflow_file": "handle-six-prs.yml",
        "status": "pending",
        "actions": {
            "review_and_merge": ["Low-risk changes"],
            "review_and_approve": ["MQL5 compilation fixes"],
            "review_and_comment": ["Architecture changes"],
            "review_and_close": ["Outdated PRs"],
            "review_and_request_changes": ["Incomplete implementations"]
        }
    }
    
    with open("pr-processing-tracker.json", "w") as f:
        json.dump(tracking_data, f, indent=2)
    
    print("📊 Created PR tracking file: pr-processing-tracker.json")

def main():
    print("🤖 ProjectQuantum PR Handler Dispatcher")
    print("=" * 50)
    print("")
    
    if not check_git_status():
        sys.exit(1)
    
    print("📋 PR Handling Workflows Available:")
    print("1. handle-six-prs.yml - Targeted actions for 6 specific PRs")
    print("2. handle-multiple-prs.yml - Generic batch processor")
    print("")
    
    trigger_pr_workflow()
    create_pr_tracking_file()
    
    print("")
    print("🎯 Next Steps:")
    print("1. Monitor workflow execution in GitHub Actions")
    print("2. Review automated PR decisions")
    print("3. Handle any PRs requiring manual intervention")
    print("4. Check pr-processing-tracker.json for status updates")
    print("")
    print("✅ PR handling system activated!")

if __name__ == "__main__":
    main()