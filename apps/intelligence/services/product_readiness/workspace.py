from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

from apps.intelligence.services.core_model.versioning import get_current_version

EXPECTED_ROOT_FILES = [
    "manage.py",
    "README.md",
    "requirements.txt",
    "docker-compose.yml",
    "Executar_TIP.bat",
]

EXPECTED_DIRS = [
    "ai",
    "analytics",
    "apps",
    "core",
    "dashboard",
    "frontend",
    "integrations",
    "reports",
    "tip_backend",
]

EXPECTED_APPS = [
    "apps.integrations",
    "apps.intelligence",
    "apps.settings",
    "integrations.trello",
    "rest_framework",
]

EXPECTED_INTELLIGENCE_MODULES = [
    "apps/intelligence/services/semantic_layer",
    "apps/intelligence/services/timeline",
    "apps/intelligence/services/risk_engine",
    "apps/intelligence/services/decision_layer",
    "apps/intelligence/services/organizational_learning",
    "apps/intelligence/services/business_value",
    "apps/intelligence/services/pilot",
]

EXPECTED_MODEL_VERSION = "1.1"


@dataclass(frozen=True)
class WorkspaceCheck:
    name: str
    status: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"name": self.name, "status": self.status, "detail": self.detail}


def validate_workspace(root: str | Path | None = None) -> dict[str, Any]:
    base_dir = Path(root or settings.BASE_DIR).resolve()
    checks: list[WorkspaceCheck] = []

    for relative in EXPECTED_ROOT_FILES:
        checks.append(_path_check(base_dir, relative, expected_type="file"))

    for relative in EXPECTED_DIRS + EXPECTED_INTELLIGENCE_MODULES:
        checks.append(_path_check(base_dir, relative, expected_type="dir"))

    installed = set(getattr(settings, "INSTALLED_APPS", []))
    for app in EXPECTED_APPS:
        checks.append(
            WorkspaceCheck(
                name=f"installed_app:{app}",
                status="ok" if app in installed else "fail",
                detail="registered" if app in installed else "missing from INSTALLED_APPS",
            )
        )

    current_version = get_current_version()
    checks.append(
        WorkspaceCheck(
            name="model_version",
            status="ok" if current_version == EXPECTED_MODEL_VERSION else "warn",
            detail=f"current={current_version}; expected={EXPECTED_MODEL_VERSION}",
        )
    )

    failures = [check for check in checks if check.status == "fail"]
    warnings = [check for check in checks if check.status == "warn"]
    status = "ready" if not failures else "blocked"

    return {
        "workspace": "TIP_Trello_Intelligence_Platform",
        "root": str(base_dir),
        "status": status,
        "model_version": current_version,
        "expected_model_version": EXPECTED_MODEL_VERSION,
        "summary": {
            "checks": len(checks),
            "failures": len(failures),
            "warnings": len(warnings),
        },
        "checks": [check.as_dict() for check in checks],
    }


def _path_check(base_dir: Path, relative: str, *, expected_type: str) -> WorkspaceCheck:
    path = base_dir / relative
    exists = path.exists()
    correct_type = path.is_file() if expected_type == "file" else path.is_dir()
    status = "ok" if exists and correct_type else "fail"
    detail = "present" if status == "ok" else f"missing {expected_type}: {relative}"
    return WorkspaceCheck(name=f"{expected_type}:{relative}", status=status, detail=detail)
