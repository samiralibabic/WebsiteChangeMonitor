"""safe add notification email to user

Revision ID: [alembic will generate]
Revises: [your_previous_revision]
Create Date: [timestamp]

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # 1. Add notification_email as nullable
    op.add_column('user', sa.Column('notification_email', sa.String(length=120), nullable=True))
    
    # 2. Add notifications_enabled with a default value
    op.add_column('user', sa.Column('notifications_enabled', sa.Boolean(), server_default='0', nullable=False))

def downgrade():
    # Remove in reverse order
    op.drop_column('user', 'notifications_enabled')
    op.drop_column('user', 'notification_email') 