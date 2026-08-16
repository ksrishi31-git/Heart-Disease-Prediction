from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd139f0ad1ad2'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('model_metadata',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('model_name', sa.String(length=64), nullable=False),
    sa.Column('model_version', sa.String(length=64), nullable=False),
    sa.Column('algorithm', sa.String(length=64), nullable=False),
    sa.Column('training_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('accuracy', sa.Float(), nullable=False),
    sa.Column('precision', sa.Float(), nullable=False),
    sa.Column('recall', sa.Float(), nullable=False),
    sa.Column('f1_score', sa.Float(), nullable=False),
    sa.Column('roc_auc', sa.Float(), nullable=False),
    sa.Column('encrypted_model_path', sa.String(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_metadata_model_name'), 'model_metadata', ['model_name'], unique=False)
    op.create_index(op.f('ix_model_metadata_model_version'), 'model_metadata', ['model_version'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sqlite_autoincrement=True
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=False),
    sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ip_hash', sa.String(length=64), nullable=True),
    sa.Column('success', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_table('predictions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', sa.String(length=36), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('encrypted_input_data', sa.Text(), nullable=False),
    sa.Column('encrypted_result', sa.Text(), nullable=False),
    sa.Column('model_version', sa.String(length=64), nullable=False),
    sa.Column('consensus', sa.String(length=16), nullable=False),
    sa.Column('best_model', sa.String(length=64), nullable=False),
    sa.Column('best_model_name', sa.String(length=64), nullable=False),
    sa.Column('probability', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_predictions_created_at'), 'predictions', ['created_at'], unique=False)
    op.create_index(op.f('ix_predictions_model_version'), 'predictions', ['model_version'], unique=False)
    op.create_index(op.f('ix_predictions_user_id'), 'predictions', ['user_id'], unique=False)
    op.create_index(op.f('ix_predictions_uuid'), 'predictions', ['uuid'], unique=True)
    op.create_table('refresh_tokens',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('token_hash', sa.String(length=64), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('ip_hash', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_refresh_tokens_token_hash'), 'refresh_tokens', ['token_hash'], unique=True)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_token_hash'), table_name='refresh_tokens')
    op.drop_table('refresh_tokens')
    op.drop_index(op.f('ix_predictions_uuid'), table_name='predictions')
    op.drop_index(op.f('ix_predictions_user_id'), table_name='predictions')
    op.drop_index(op.f('ix_predictions_model_version'), table_name='predictions')
    op.drop_index(op.f('ix_predictions_created_at'), table_name='predictions')
    op.drop_table('predictions')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_model_metadata_model_version'), table_name='model_metadata')
    op.drop_index(op.f('ix_model_metadata_model_name'), table_name='model_metadata')
    op.drop_table('model_metadata')
