from pathlib import Path

from diaas_ops.configure.helpers import BaseConfiguration, from_env
from diaas_ops.secret import SecretStore
from slugify import slugify


class Configuration(BaseConfiguration):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        default_project_id = self.if_env(prd="diaas-prd", otherwise="diaas-stg")
        project_id = from_env("CLOUDSDK_CORE_PROJECT", default=default_project_id)
        self.secrets = SecretStore(project_id=project_id)
        self.commit_config()
        self.deployment_config()
        self.app_config()
        self.monitoring_config()
        self.tracker_config()
        self.login_config()

    def _secret(self, name):
        secret = self.secrets.secret_from_name(name).value
        if secret is None:
            raise ValueError(f"Missing required secret {name} in {self.secrets}")
        else:
            return secret

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
                deployment_url = "https://crvl.app"
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

    def _db_config(self, install_dir):
        self._set_all(
            DIAAS_BEDB_PGDATABASE="postgres",
            DIAAS_BEDB_PGHOST="127.0.0.1",
            DIAAS_BEDB_PGPASSWORD="KFvZLY65Mv0GahRMBL",
            DIAAS_BEDB_PGPORT="5432",
            DIAAS_BEDB_PGUSER="postgres",
        )
        self._set(
            "DIAAS_BEDB_MIGRATIONS_DIR",
            default=install_dir / "be/migrations",
            type=Path,
        )

    def _flask_config(self):
        self._set_all(
            DIAAS_INTERNAL_API_TOKEN=self._secret("app/internal-api-token"),
            DIAAS_SESSION_SECRET_KEY=self._secret("app/session-secret-key"),
        )

        self._set_all(
            DIAAS_SESSION_COOKIE_IS_SECURE=not self.is_lcl,
            FLASK_DEBUG=self.if_env(prd=None, otherwise="1"),
            FLASK_ENV=self.if_env(prd="production", otherwise="development"),
        )

    def app_config(self):
        if self.with_be:
            self._flask_config()
            install_dir = from_env(
                "DIAAS_INSTALL_DIR", default=Path(".").resolve(), type=Path
            )
            self._set("DIAAS_INSTALL_DIR", install_dir)
            self._db_config(install_dir)
            self._set_all(
                DIAAS_DS_STORE=install_dir / "tmp/lcl-ds-store",
                DIAAS_WORKBENCH_STORE=install_dir / "tmp/lcl-workbench-store",
                DIAAS_BE_BIN_DIR=install_dir / "be/bin",
                DIAAS_LIBDS_DIR=install_dir / "libds",
                DIAAS_BEDB_MIGRATIONS_DIR=install_dir / "be/migrations",
            )
            pg_hashids_salt = self.secrets.secret_from_name("app/pg_hashids-salt").value
            self._set("DIAAS_PG_HASHIDS_SALT", value=pg_hashids_salt)

            self._set("DIAAS_BE_BIN_DIR", default=install_dir / "be/bin")

    def monitoring_config(self):
        dsn = self.if_env(
            prd="https://f3551f0329dd4a9cbe4030f5f5507be5@o469059.ingest.sentry.io/5497805",
            otherwise="https://7e144b9b33bb467ba432cacd5ef608ab@o469059.ingest.sentry.io/5497814",
        )

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

    def login_config(self):
        self._set(
            "DIAAS_AUTH_METHOD", default=self.if_env(lcl="TRUST", otherwise="VERIFY")
        )
        self._set(
            "DIAAS_AUTH_GOOGLE_CLIENT_ID", self._secret("app/google-oauth/client-id")
        )
        if self.with_be:
            self._set(
                "DIAAS_AUTH_GOOGLE_CLIENT_SECRET",
                self._secret("app/google-oauth/client-secret"),
            )
