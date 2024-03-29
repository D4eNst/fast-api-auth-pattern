"""Add scope to refresh session and allowed users

Revision ID: ef993acc115e
Revises: 1a7fde94b7ed
Create Date: 2024-02-26 15:29:19.019820

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ef993acc115e'
down_revision = '1a7fde94b7ed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('application_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('application_id', sa.Integer(), nullable=False),
    sa.Column('fullname', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['application_id'], ['application.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('application', 'allowed_users')
    op.add_column('refresh_session', sa.Column('scope', sa.String(length=255), nullable=False))
    op.alter_column('refresh_session', 'ua',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=255),
               existing_nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('refresh_session', 'ua',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
    op.drop_column('refresh_session', 'scope')
    op.add_column('application', sa.Column('allowed_users', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_table('application_user')
    # ### end Alembic commands ###
