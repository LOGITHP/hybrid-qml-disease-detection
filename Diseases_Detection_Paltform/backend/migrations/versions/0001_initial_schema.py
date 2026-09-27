"""Initial database schema with complete multi-domain models.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-27 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # 2. artifacts table
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('artifact_type', sa.String(length=100), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_artifacts_id'), 'artifacts', ['id'], unique=False)
    op.create_index(op.f('ix_artifacts_user_id'), 'artifacts', ['user_id'], unique=False)

    # 3. datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_datasets_id'), 'datasets', ['id'], unique=False)
    op.create_index(op.f('ix_datasets_name'), 'datasets', ['name'], unique=False)
    op.create_index(op.f('ix_datasets_user_id'), 'datasets', ['user_id'], unique=False)

    # 4. dataset_versions table
    op.create_table(
        'dataset_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('file_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('column_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('dataset_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dataset_versions_dataset_id'), 'dataset_versions', ['dataset_id'], unique=False)
    op.create_index(op.f('ix_dataset_versions_id'), 'dataset_versions', ['id'], unique=False)
    op.create_index(op.f('ix_dataset_versions_user_id'), 'dataset_versions', ['user_id'], unique=False)

    # 5. preprocessing_configs table
    op.create_table(
        'preprocessing_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='auto'),
        sa.Column('configuration', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_preprocessing_configs_id'), 'preprocessing_configs', ['id'], unique=False)
    op.create_index(op.f('ix_preprocessing_configs_user_id'), 'preprocessing_configs', ['user_id'], unique=False)

    # 6. preprocessing_runs table
    op.create_table(
        'preprocessing_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('preprocessing_config_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('approval_status', sa.String(length=50), nullable=False, server_default='not_required'),
        sa.Column('plan', sa.JSON(), nullable=True),
        sa.Column('report_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('processed_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['preprocessing_config_id'], ['preprocessing_configs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['processed_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['report_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_preprocessing_runs_dataset_version_id'), 'preprocessing_runs', ['dataset_version_id'], unique=False)
    op.create_index(op.f('ix_preprocessing_runs_id'), 'preprocessing_runs', ['id'], unique=False)
    op.create_index(op.f('ix_preprocessing_runs_user_id'), 'preprocessing_runs', ['user_id'], unique=False)

    # 7. feature_selection_runs table (SINGLE SOURCE OF TRUTH FOR FEATURES)
    op.create_table(
        'feature_selection_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('preprocessing_run_id', sa.String(length=36), nullable=True),
        sa.Column('ranking_method', sa.String(length=100), nullable=False),
        sa.Column('feature_count', sa.Integer(), nullable=False),
        sa.Column('selected_features', sa.JSON(), nullable=False),
        sa.Column('ranking_scores', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['preprocessing_run_id'], ['preprocessing_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_feature_selection_runs_dataset_version_id'), 'feature_selection_runs', ['dataset_version_id'], unique=False)
    op.create_index(op.f('ix_feature_selection_runs_id'), 'feature_selection_runs', ['id'], unique=False)
    op.create_index(op.f('ix_feature_selection_runs_user_id'), 'feature_selection_runs', ['user_id'], unique=False)

    # 8. models table
    op.create_table(
        'models',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('model_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_models_id'), 'models', ['id'], unique=False)
    op.create_index(op.f('ix_models_name'), 'models', ['name'], unique=False)
    op.create_index(op.f('ix_models_user_id'), 'models', ['user_id'], unique=False)

    # 9. model_configs table
    op.create_table(
        'model_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('model_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('hyperparameters', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_model_configs_id'), 'model_configs', ['id'], unique=False)

    # 10. model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('model_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('version_tag', sa.String(length=50), nullable=False),
        sa.Column('artifact_id', sa.String(length=36), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_model_versions_id'), 'model_versions', ['id'], unique=False)
    op.create_index(op.f('ix_model_versions_model_id'), 'model_versions', ['model_id'], unique=False)
    op.create_index(op.f('ix_model_versions_user_id'), 'model_versions', ['user_id'], unique=False)

    # 11. training_configs table
    op.create_table(
        'training_configs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('epochs', sa.Integer(), nullable=True),
        sa.Column('batch_size', sa.Integer(), nullable=True),
        sa.Column('learning_rate', sa.Float(), nullable=True),
        sa.Column('optimizer', sa.String(length=50), nullable=True),
        sa.Column('random_seed', sa.Integer(), nullable=False, server_default='42'),
        sa.Column('early_stopping', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('extra_config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_training_configs_id'), 'training_configs', ['id'], unique=False)

    # 12. training_runs table
    op.create_table(
        'training_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('model_id', sa.String(length=36), nullable=False),
        sa.Column('model_version_id', sa.String(length=36), nullable=True),
        sa.Column('dataset_version_id', sa.String(length=36), nullable=False),
        sa.Column('preprocessing_run_id', sa.String(length=36), nullable=True),
        sa.Column('feature_selection_run_id', sa.String(length=36), nullable=False),
        sa.Column('training_config_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('artifact_id', sa.String(length=36), nullable=True),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['feature_selection_run_id'], ['feature_selection_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['preprocessing_run_id'], ['preprocessing_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['training_config_id'], ['training_configs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_training_runs_feature_selection_run_id'), 'training_runs', ['feature_selection_run_id'], unique=False)
    op.create_index(op.f('ix_training_runs_id'), 'training_runs', ['id'], unique=False)

    # 13. quantum_providers table
    op.create_table(
        'quantum_providers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )

    # 14. quantum_devices table
    op.create_table(
        'quantum_devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('provider_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('device_type', sa.String(length=50), nullable=False),
        sa.Column('num_qubits', sa.Integer(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['provider_id'], ['quantum_providers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 15. quantum_jobs table
    op.create_table(
        'quantum_jobs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('training_run_id', sa.String(length=36), nullable=True),
        sa.Column('external_job_id', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('shots', sa.Integer(), nullable=False, server_default='1000'),
        sa.Column('circuit_data', sa.JSON(), nullable=False),
        sa.Column('results', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['quantum_devices.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['training_run_id'], ['training_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 16. prediction_runs table
    op.create_table(
        'prediction_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('model_version_id', sa.String(length=36), nullable=False),
        sa.Column('preprocessing_run_id', sa.String(length=36), nullable=True),
        sa.Column('feature_selection_run_id', sa.String(length=36), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='queued'),
        sa.Column('input_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('output_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('predictions_summary', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['feature_selection_run_id'], ['feature_selection_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['input_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['output_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['preprocessing_run_id'], ['preprocessing_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 17. evaluation_runs table
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('model_version_id', sa.String(length=36), nullable=False),
        sa.Column('dataset_version_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('metrics', sa.JSON(), nullable=False),
        sa.Column('report_artifact_id', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['dataset_version_id'], ['dataset_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['report_artifact_id'], ['artifacts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 18. experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 19. audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('experiments')
    op.drop_table('evaluation_runs')
    op.drop_table('prediction_runs')
    op.drop_table('quantum_jobs')
    op.drop_table('quantum_devices')
    op.drop_table('quantum_providers')
    op.drop_table('training_runs')
    op.drop_table('training_configs')
    op.drop_table('model_versions')
    op.drop_table('model_configs')
    op.drop_table('models')
    op.drop_table('feature_selection_runs')
    op.drop_table('preprocessing_runs')
    op.drop_table('preprocessing_configs')
    op.drop_table('dataset_versions')
    op.drop_table('datasets')
    op.drop_table('artifacts')
    op.drop_table('users')
