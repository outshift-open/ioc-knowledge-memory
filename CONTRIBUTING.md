- [Please follow this general contribution guide for SRE repos](https://wwwin-github.cisco.com/pages/eti/eti-platform-docs/development/contribution_guide/)
- For pushing git tags/branches to this repo, please reach out to [SRE team](mailto:eti-sre-admins@cisco.com)

## Version Management

This project uses **pyproject.toml as the single source of truth** for versioning.

### How to Release a New Version

**1. Update version in [pyproject.toml](pyproject.toml):**
```toml
[project]
version = "0.1.5"  # Change this line only!
```

**2. Commit and push:**
```bash
git add pyproject.toml
git commit -m "chore: bump version to 0.1.5"
git push
```

**3. CI/CD automatically:**
- ✅ Reads version from pyproject.toml
- ✅ Builds package with correct version
- ✅ Publishes to Artifactory (on `clawbee` branch)
- ✅ Builds Docker image (on `main` branch)

### Version Locations

All version information is **automatically synced** from pyproject.toml:

| Location | How It Works |
|----------|--------------|
| `pyproject.toml` | **Source of truth** - edit here only |
| `setup.py` | Reads from pyproject.toml automatically |
| `src/knowledge_memory/__init__.py` | Uses `importlib.metadata.version()` |
| `.github/workflows/ci.yaml` | Reads dynamically for dev builds |

**No manual sync needed!** Just update pyproject.toml and everything else follows.

### Version Format

We follow [PEP 440](https://peps.python.org/pep-0440/) versioning:
- Release versions: `0.1.4`, `0.2.0`, `1.0.0`
- Dev builds (CI): `0.1.4.dev20260316120000` (adds timestamp)
