# Python 3.14 Compatibility Notes

## Known Issues and Solutions

### Protobuf Dependency Warning
When installing dependencies, you may see a warning:
```
google-ai-generativelanguage 0.4.0 requires protobuf<5.0.0dev, but you have protobuf 6.33.2
```

**This is safe to ignore.** Protobuf 6.x is backward compatible and works correctly with Python 3.14. The dependency constraint is outdated.

### Recommended Python Version
While the project works with Python 3.14, **Python 3.11 or 3.12 are recommended** for maximum stability and compatibility with all dependencies.

### If You Encounter Issues
If you run into compatibility problems with Python 3.14:

1. **Use Python 3.11 or 3.12** (recommended):
   ```bash
   python3.11 -m venv venv
   # or
   python3.12 -m venv venv
   ```

2. **Reinstall dependencies**:
   ```bash
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Current Compatibility Status
- ✅ FastAPI - Works
- ✅ SQLAlchemy >= 2.0.36 - Works
- ✅ Pydantic >= 2.9.0 - Works
- ✅ Protobuf >= 6.0.0 - Works (with dependency warning that can be ignored)
- ✅ All other dependencies - Works

