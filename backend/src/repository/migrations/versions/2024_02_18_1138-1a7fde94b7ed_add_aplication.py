"""Add aplication

Revision ID: 1a7fde94b7ed
Revises: 9009013cd889
Create Date: 2024-02-18 11:38:46.429972

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a7fde94b7ed'
down_revision = '9009013cd889'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('application',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=20), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('website', sa.String(length=200), nullable=False),
    sa.Column('redirect_uris', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('allowed_users', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('mode', sa.String(length=3), nullable=False),
    sa.Column('client_id', sa.String(), nullable=False),
    sa.Column('client_secret', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['user'], ['account.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('client_id'),
    sa.UniqueConstraint('client_secret')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('application')
    # ### end Alembic commands ###
