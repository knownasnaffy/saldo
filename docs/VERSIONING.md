# Versioning and Release Guide

## Versioning Strategy

Saldo follows [Semantic Versioning (SemVer)](https://semver.org/) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality in a backward compatible manner
- **PATCH**: Backward compatible bug fixes

## Release Process

### Automated Release (Recommended)

Use the release script for a streamlined process:

```bash
# Patch release (0.1.0 -> 0.1.1)
./scripts/release.sh patch

# Minor release (0.1.0 -> 0.2.0)
./scripts/release.sh minor

# Major release (0.1.0 -> 1.0.0)
./scripts/release.sh major
```

### Manual Release

If you prefer manual control:

1. **Bump version**:

   ```bash
   python scripts/bump_version.py patch
   ```

2. **Commit and tag**:

   ```bash
   git add saldo/__init__.py
   git commit -m "Bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

3. **GitHub Actions handles the rest automatically**

## What Happens During Release

When you push a version tag (e.g., `v1.0.0`), GitHub Actions automatically:

1. **Runs full test suite** across Python 3.7-3.12
2. **Builds distribution packages** (wheel and source)
3. **Creates GitHub release** with auto-generated changelog
4. **Uploads packages** as release assets

## Version Management

### Single Source of Truth

Version is defined in `saldo/__init__.py`:

```python
__version__ = "0.1.0"
```

`setup.py` imports this version to avoid duplication.

### Pre-release Versions

For pre-releases, use suffixes:

- `1.0.0-alpha.1` - Alpha release
- `1.0.0-beta.1` - Beta release
- `1.0.0-rc.1` - Release candidate

GitHub Actions automatically marks these as pre-releases.

## Development Workflow

### Feature Development

1. Create feature branch from `main`
2. Develop and test changes
3. Create pull request to `main`
4. Tests run automatically on PR
5. Merge to `main` after review

### Release Preparation

1. Update `CHANGELOG.md` with new features/fixes
2. Ensure all tests pass
3. Run release script
4. Verify GitHub release was created successfully

## Troubleshooting

### Failed Release

If a release fails:

1. Check GitHub Actions logs
2. Fix any issues
3. Delete the tag: `git tag -d vX.Y.Z && git push origin :refs/tags/vX.Y.Z`
4. Re-run the release process

### Version Conflicts

If you need to fix the version:

1. Edit `saldo/__init__.py` manually
2. Commit the change
3. Create new tag with corrected version

## Best Practices

- Always test before releasing
- Keep `CHANGELOG.md` updated
- Use descriptive commit messages
- Release frequently with small changes
- Tag releases immediately after merging to main
