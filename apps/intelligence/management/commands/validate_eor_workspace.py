from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.intelligence.services.product_readiness.workspace import validate_workspace


class Command(BaseCommand):
    help = "Validate that the current workspace is a complete TIP checkout."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Print full JSON payload.")

    def handle(self, *args, **options):
        payload = validate_workspace()
        if options["json"]:
            self.stdout.write(json.dumps(payload, indent=2, default=str))
        else:
            summary = payload["summary"]
            self.stdout.write(
                f"TIP workspace status={payload['status']} checks={summary['checks']} "
                f"failures={summary['failures']} warnings={summary['warnings']}"
            )

        if payload["status"] != "ready":
            raise CommandError("Workspace validation failed. Refusing product hardening operations.")
