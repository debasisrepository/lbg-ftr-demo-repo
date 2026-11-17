import ast
import os
from pathlib import Path


def test_import_boundaries():
    """
    Verify API routers respect architectural boundaries (HLD B-2).
    
    API layer (app/api/**/*.py) must NOT import from:
    - app.adapters (data adapter layer)
    - app.agents (AI orchestration layer, including llm_gateway and orchestrator)
    - app.tools (tool execution layer)
    
    This ensures AI/adapter outages never block read operations or Case creation.
    """
    backend_root = Path(__file__).resolve().parents[2]
    violations = []

    api_files = list((backend_root / "app" / "api").rglob("*.py"))
    
    # Prohibited import prefixes for API routers
    forbidden_modules = ["adapters", "agents", "tools"]
    
    for file_path in api_files:
        if file_path.name.startswith("__"):
            continue
        source = file_path.read_text()
        tree = ast.parse(source, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = getattr(node, "module", None)
                if module:
                    # Check if module imports from any forbidden namespace
                    for forbidden in forbidden_modules:
                        # Match "adapters", "agents", "tools", "app.adapters", "app.agents", etc.
                        if module == forbidden or module.startswith(f"{forbidden}.") or \
                           module == f"app.{forbidden}" or module.startswith(f"app.{forbidden}."):
                            violations.append(
                                f"{file_path.relative_to(backend_root)}: imports {module} "
                                f"(violates boundary - API must not import {forbidden})"
                            )
                            break

    assert not violations, f"Import boundary violations:\n" + "\n".join(violations)
