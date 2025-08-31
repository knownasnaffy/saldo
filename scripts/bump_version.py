#!/usr/bin/env python3
"""
Version bumping utility for Saldo.

Usage:
    python scripts/bump_version.py patch    # 0.1.0 -> 0.1.1
    python scripts/bump_version.py minor    # 0.1.0 -> 0.2.0
    python scripts/bump_version.py major    # 0.1.0 -> 1.0.0
"""

import re
import sys
import os
from pathlib import Path

def get_current_version():
    """Read current version from __init__.py"""
    init_file = Path("saldo/__init__.py")
    content = init_file.read_text()
    match = re.search(r'__version__ = "([^"]+)"', content)
    if not match:
        raise ValueError("Could not find version in __init__.py")
    return match.group(1)

def parse_version(version_str):
    """Parse version string into major, minor, patch"""
    parts = version_str.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version_str}")
    return [int(p) for p in parts]

def bump_version(current_version, bump_type):
    """Bump version based on type"""
    major, minor, patch = parse_version(current_version)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    return f"{major}.{minor}.{patch}"

def update_version_file(new_version):
    """Update version in __init__.py"""
    init_file = Path("saldo/__init__.py")
    content = init_file.read_text()
    
    # Replace version
    new_content = re.sub(
        r'__version__ = "[^"]+"',
        f'__version__ = "{new_version}"',
        content
    )
    
    init_file.write_text(new_content)
    print(f"Updated saldo/__init__.py with version {new_version}")

def main():
    if len(sys.argv) != 2 or sys.argv[1] in ["-h", "--help"]:
        print("Usage: python scripts/bump_version.py [major|minor|patch]")
        print("\nBump types:")
        print("  patch  - Bug fixes (0.1.0 -> 0.1.1)")
        print("  minor  - New features (0.1.0 -> 0.2.0)")
        print("  major  - Breaking changes (0.1.0 -> 1.0.0)")
        sys.exit(0 if len(sys.argv) == 2 and sys.argv[1] in ["-h", "--help"] else 1)
    
    bump_type = sys.argv[1].lower()
    if bump_type not in ["major", "minor", "patch"]:
        print("Error: bump type must be 'major', 'minor', or 'patch'")
        print("Run with --help for usage information")
        sys.exit(1)
    
    try:
        current_version = get_current_version()
        new_version = bump_version(current_version, bump_type)
        
        print(f"Bumping version from {current_version} to {new_version}")
        update_version_file(new_version)
        
        print(f"\nNext steps:")
        print(f"1. git add saldo/__init__.py")
        print(f"2. git commit -m 'Bump version to {new_version}'")
        print(f"3. git tag v{new_version}")
        print(f"4. git push origin main --tags")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()