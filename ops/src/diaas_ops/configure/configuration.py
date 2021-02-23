from pathlib import Path

from diaas_ops.configure.helpers import BaseConfiguration, from_env
from diaas_ops.secret import SecretStore
from slugify import slugify


class Configuration(BaseConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.secrets = SecretStore(
            project_id=self.if_env(prd="diaas-prd", otherwise="diaas-stg")
        )
        self.commit_config()
        self.deployment_config()
        self.app_config()
        self.monitoring_config()
        self.tracker_config()

    def commit_config(self):
        if from_env("CI"):
            ref_name = from_env("CI_COMMIT_REF_NAME")
            sha = from_env("CI_COMMIT_SHA")
            title = from_env("CI_COMMIT_TITLE")
        else:
            if self.is_prd:
                ref_name = sha = title = f"HOTFIX-{self.timestamp}"
            else:
                ref_name = sha = title = f"HEAD-{self.timestamp}"

        self._set_all(
            DIAAS_DEPLOYMENT_COMMIT_REF_NAME=ref_name,
            DIAAS_DEPLOYMENT_COMMIT_SHA=sha,
            DIAAS_DEPLOYMENT_COMMIT_TITLE=title,
        )

    def deployment_config(self):
        if not self.with_be:
            return

        self._set_all(
            DIAAS_DEPLOYMENT_BRANCH=self.branch,
        )

        ci_environment_url = from_env("CI_ENVIRONMENT_URL")
        if ci_environment_url is not None:
            deployment_url = ci_environment_url
        else:
            if self.is_prd:
                deployment_url = "https://app.crvl.io"
            elif self.is_lcl:
                deployment_url = "http://127.0.0.1:8080/"
            else:
                branch = slugify(text=self.branch, max_length=48)
                deployment_url = f"https://{branch}.app.crvl.dev"
        self._set_all(
            DIAAS_DEPLOYMENT_NAME=slugify(
                self.environment + "-" + self.branch, max_length=60
            ),
            DIAAS_DEPLOYMENT_URL=deployment_url,
        )

    def _db_config(self):
        self._set_all(
            DIAAS_BEDB_PGDATABASE="postgres",
            DIAAS_BEDB_PGHOST="127.0.0.1",
            DIAAS_BEDB_PGPASSWORD="KFvZLY65Mv0GahRMBL",
            DIAAS_BEDB_PGPORT="5432",
            DIAAS_BEDB_PGUSER="postgres",
        )

    def _flask_config(self):
        self._set_all(
            DIAAS_INTERNAL_API_TOKEN=self.secrets.secret_from_name(
                "app/internal-api-token"
            ).value,
            DIAAS_SESSION_SECRET_KEY=self.secrets.secret_from_name(
                "app/session-secret-key"
            ).value,
        )

        self._set_all(
            DIAAS_SESSION_COOKIE_IS_SECURE=not self.is_lcl,
            FLASK_DEBUG=self.if_env(prd=None, otherwise="1"),
            FLASK_ENV=self.if_env(prd="production", otherwise="development"),
        )

    def app_config(self):
        if self.with_fe:
            self._set(
                "DIAAS_API_BASEURL",
                default=self.if_env(prd="/", lcl="http://127.0.0.1:8080"),
            )

        if self.with_be:
            self._flask_config()
            self._db_config()
            install_dir = from_env("DIAAS_INSTALL_DIR", default=Path(".").resolve(), type=Path)
            self._set("DIAAS_INSTALL_DIR", install_dir)
            if self.is_lcl:
                self._set_all(
                    DIAAS_DS_STORE=install_dir / "tmp/lcl-ds-store",
                    DIAAS_WORKBENCH_STORE=install_dir / "tmp/lcl-workbench-store",
                )
            else:
                self._set_all(
                    DIAAS_DS_STORE=Path("/opt/store/ds"),
                    DIAAS_WORKBENCH_STORE=Path("/opt/store/wb"),
                )
            pg_hashids_salt = self.secrets.secret_from_name("app/pg_hashids-salt").value
            self._set("DIAAS_PG_HASHIDS_SALT", value=pg_hashids_salt)

    def monitoring_config(self):
        dsn = self.if_env(
            prd="https://f3551f0329dd4a9cbe4030f5f5507be5@o469059.ingest.sentry.io/5497805",
            otherwise="https://7e144b9b33bb467ba432cacd5ef608ab@o469059.ingest.sentry.io/5497814",
        )

        if self.with_be:
            diaas_enable_sentry = self._set(
                "DIAAS_ENABLE_SENTRY", default=self.is_prd, type=bool
            )
            if diaas_enable_sentry:
                self._set_all(
                    DIAAS_SENTRY_DSN=dsn,
                    DIAAS_SENTRY_ENVIRONMENT=self.environment,
                    DIAAS_SENTRY_RELEASE="diaas@"
                    + self.values["DIAAS_DEPLOYMENT_COMMIT_SHA"],
                )

        if self.with_fe:
            self._set("DIAAS_ENABLE_WEB_VITALS", default=self.is_prd, type=bool)

    def tracker_config(self):
        if not self.with_fe:
            return

        enable_trackers = self._set(
            "DIAAS_ENABLE_TRACKERS", default=self.is_prd, type=bool
        )
        if enable_trackers:
            self._set_all(
                DIAAS_GTM_CONTAINER_ID="GTM-1234567890",
            )
