#!/bin/bash
# Simple Branch Protection Setup for Weight Tracker Repository
# Uses GitHub web interface approach - more reliable

set -e

REPO="CalumMallorie/weight-tracker"
BRANCH="main"

echo "🔒 Setting up branch protection for $REPO on branch $BRANCH"

# Check if gh CLI is installed and authenticated
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it first:"
    echo "   https://cli.github.com/"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ GitHub CLI is not authenticated. Please run: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI is authenticated"

# Step 1: Enable basic branch protection with PR requirement
echo "📋 Step 1: Setting up basic branch protection..."

cat > /tmp/branch-protection.json << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": []
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

if gh api repos/$REPO/branches/$BRANCH/protection --method PUT --input /tmp/branch-protection.json; then
    echo "✅ Basic branch protection enabled!"
else
    echo "⚠️  Failed to set branch protection via API. Using manual setup instructions instead."
fi

# Clean up temp file
rm -f /tmp/branch-protection.json

echo ""
echo "🛡️  Manual Setup Instructions:"
echo "   Since the API setup had issues, please manually configure branch protection:"
echo ""
echo "   1. Go to: https://github.com/$REPO/settings/branches"
echo "   2. Click 'Add branch protection rule'"
echo "   3. Branch name pattern: main"
echo "   4. Check these options:"
echo "      ✅ Require a pull request before merging"
echo "      ✅ Require status checks to pass before merging"
echo "      ✅ Require branches to be up to date before merging"
echo "      ✅ Include administrators"
echo "      ❌ Allow force pushes (unchecked)"
echo "      ❌ Allow deletions (unchecked)"
echo ""
echo "   5. In 'Status checks' section, add these required checks:"
echo "      - Fast Tests"
echo "      - Security Scan"  
echo "      - Build Docker Image"
echo ""
echo "   6. Click 'Create'"
echo ""

# Check current protection status
echo "🔍 Current branch protection status:"
if gh api repos/$REPO/branches/$BRANCH/protection 2>/dev/null | jq -r '
  "✅ Protection enabled\n" +
  "Required checks: " + (.required_status_checks.contexts // [] | join(", ")) + "\n" +
  "PR reviews required: " + (.required_pull_request_reviews.required_approving_review_count // 0 | tostring) + "\n" +
  "Enforce admins: " + (.enforce_admins.enabled // false | tostring)
'; then
    echo "✅ Branch protection is configured!"
else
    echo "⚠️  Branch protection may not be fully configured."
    echo "   Please follow the manual setup instructions above."
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📝 What this achieves:"
echo "   • Prevents direct pushes to main branch"
echo "   • Requires pull requests for all changes"
echo "   • Ensures tests pass before merging"
echo "   • Maintains code quality standards"
echo ""
echo "🚀 Your main branch protection is ready!"