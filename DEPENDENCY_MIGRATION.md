# Python Dependencies Migration Notes

## Migration from requirements.txt to pyproject.toml

This project has been migrated from multiple `requirements.txt` files to a single `pyproject.toml` managed by Poetry.

### Old Structure
- `permit_leads/requirements.txt` - Scraping and ETL dependencies
- `backend/requirements.txt` - FastAPI backend dependencies

### New Structure
- `pyproject.toml` - All dependencies managed by Poetry
- `poetry.lock` - Lock file with exact versions (generated)

### Migration Commands

```bash
# Install Poetry (if not already installed)
pip install poetry

# Install all dependencies
poetry install

# Add new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Generate requirements.txt for deployment (if needed)
poetry export -f requirements.txt --output requirements.txt
```

### Benefits of Poetry
1. **Single source of truth** - All dependencies in one file
2. **Dependency resolution** - Automatic resolution of version conflicts
3. **Lock file** - Reproducible builds with exact versions
4. **Virtual environment management** - Automatic venv handling
5. **Build and publish** - Built-in packaging support

### Backwards Compatibility
The old `requirements.txt` files are still present for reference but should not be used for new installations. They will be removed in a future release.

### CI/CD Updates
All CI workflows have been updated to use Poetry instead of pip for dependency management.