#!/bin/bash

# Saldo Release Script
# Usage: ./scripts/release.sh [major|minor|patch]

set -e  # Exit on any error

BUMP_TYPE=${1:-patch}

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Usage: $0 [major|minor|patch]"
    echo "Default: patch"
    exit 1
fi

echo "🚀 Starting release process..."

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "❌ Error: Must be on main branch to release. Currently on: $CURRENT_BRANCH"
    exit 1
fi

# Check if working directory is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "❌ Error: Working directory is not clean. Please commit or stash changes."
    git status --short
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Run tests
echo "🧪 Running tests..."
python -m pytest

# Bump version
echo "📈 Bumping version ($BUMP_TYPE)..."
python scripts/bump_version.py $BUMP_TYPE

# Get the new version
NEW_VERSION=$(python -c "from saldo import __version__; print(__version__)")

# Commit version bump
echo "💾 Committing version bump..."
git add saldo/__init__.py
git commit -m "Bump version to $NEW_VERSION"

# Create and push tag
echo "🏷️  Creating and pushing tag v$NEW_VERSION..."
git tag "v$NEW_VERSION"
git push origin main --tags

echo "✅ Release v$NEW_VERSION initiated!"
echo "📦 GitHub Actions will now:"
echo "   - Run tests"
echo "   - Build packages"
echo "   - Create GitHub release"
echo "   - Upload distribution files"
echo ""
echo "🔗 Check progress at: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions"