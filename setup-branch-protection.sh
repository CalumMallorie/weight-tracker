#!/bin/bash
# Setup Branch Protection for Weight Tracker Repository
# Requires GitHub CLI (gh) to be installed and authenticated

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

# Create branch protection rule
echo "📋 Creating branch protection rule..."

gh api repos/$REPO/branches/$BRANCH/protection \
  --method PUT \
  --field required_status_checks='{
    "strict": true,
    "contexts": [
      "Fast Tests",
      "Security Scan", 
      "Build Docker Image"
    ]
  }' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "require_last_push_approval": false
  }' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field block_creations=false

echo "✅ Branch protection rule created successfully!"

echo ""
echo "🛡️  Branch Protection Summary:"
echo "   ✅ Require pull request before merging"
echo "   ✅ Require status checks to pass:"
echo "      - Fast Tests (required)"
echo "      - Security Scan (required)" 
echo "      - Build Docker Image (required when code changes)"
echo "   ✅ Require branches to be up to date"
echo "   ✅ Include administrators"
echo "   ❌ Force pushes disabled"
echo "   ❌ Branch deletion disabled"
echo ""

# Verify the protection rule
echo "🔍 Verifying branch protection settings..."
gh api repos/$REPO/branches/$BRANCH/protection --jq '
  "Protection enabled: " + (.enabled | tostring) + "\n" +
  "Required status checks: " + (.required_status_checks.contexts | join(", ")) + "\n" +
  "Enforce admins: " + (.enforce_admins.enabled | tostring) + "\n" +
  "PR reviews required: " + (.required_pull_request_reviews.required_approving_review_count | tostring)
'

echo ""
echo "🎉 Branch protection setup complete!"
echo ""
echo "📝 What this means:"
echo "   • No direct pushes to main branch"
echo "   • All changes must go through pull requests"
echo "   • Tests must pass before merging"
echo "   • Security scans must pass"
echo "   • Docker builds must succeed (when code changes)"
echo "   • Even administrators must follow these rules"
echo ""
echo "🚀 Your main branch is now protected!"