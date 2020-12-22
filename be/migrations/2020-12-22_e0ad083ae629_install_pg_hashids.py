"""install pg_hashids

Revision ID: e0ad083ae629
Revises: 3a947eec80a9
Create Date: 2020-12-22 12:36:09.641015

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0ad083ae629'
down_revision = '3a947eec80a9'
branch_labels = ()
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION pg_hashids;")


def downgrade():
    op.execute("DROP EXTENSION pg_hashids")
