"""
Runs a pg_dump backup and prunes anything older than DB_BACKUP_RETENTION_DAYS.
Intended to be scheduled via cron or a task scheduler, e.g.:

    0 2 * * * cd /path/to/backend && .venv/bin/python manage.py backup_database

Requires the `pg_dump` client to be installed on the host running this.
"""
import subprocess
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create a compressed PostgreSQL backup and prune old ones."

    def handle(self, *args, **options):
        backup_dir = Path(settings.DB_BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)

        db = settings.DATABASES["default"]
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        out_file = backup_dir / f"trueblue-{timestamp}.sql.gz"

        self.stdout.write(f"Backing up database to {out_file} ...")
        pg_dump = subprocess.Popen(
            [
                "pg_dump",
                "-h", db["HOST"], "-p", str(db["PORT"]), "-U", db["USER"], db["NAME"],
            ],
            stdout=subprocess.PIPE,
            env={"PGPASSWORD": db["PASSWORD"]},
        )
        gzip_proc = subprocess.Popen(["gzip"], stdin=pg_dump.stdout, stdout=open(out_file, "wb"))
        pg_dump.stdout.close()
        gzip_proc.communicate()

        if gzip_proc.returncode != 0:
            self.stderr.write(self.style.ERROR("Backup failed."))
            return

        self.stdout.write(self.style.SUCCESS(f"Backup complete: {out_file}"))
        self._prune(backup_dir)

    def _prune(self, backup_dir: Path):
        cutoff = time.time() - settings.DB_BACKUP_RETENTION_DAYS * 86400
        for f in backup_dir.glob("trueblue-*.sql.gz"):
            if f.stat().st_mtime < cutoff:
                f.unlink()
                self.stdout.write(f"Pruned old backup {f.name}")
