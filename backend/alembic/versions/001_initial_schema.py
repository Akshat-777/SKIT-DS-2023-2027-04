"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-04 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. resumes
    op.create_table(
        'resumes',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='uploaded'),
        sa.Column('ocr_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_given', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('retention_days', sa.Integer(), nullable=False, server_default='365'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('soft_deleted_at', sa.DateTime(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resumes_user_id'), 'resumes', ['user_id'], unique=False)
    op.create_index(op.f('ix_resumes_is_deleted'), 'resumes', ['is_deleted'], unique=False)

    # 3. parsed_entities
    op.create_table(
        'parsed_entities',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('education', sa.JSON(), nullable=True),
        sa.Column('experience', sa.JSON(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('sections', sa.JSON(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('resume_id')
    )
    op.create_index(op.f('ix_parsed_entities_resume_id'), 'parsed_entities', ['resume_id'], unique=True)

    # 4. skills
    op.create_table(
        'skills',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_skills_name'), 'skills', ['name'], unique=True)

    # 5. resume_skills
    op.create_table(
        'resume_skills',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('skill_id', sa.String(length=64), nullable=True),
        sa.Column('skill_name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False, server_default='explicit'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_skills_resume_id'), 'resume_skills', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_skill_id'), 'resume_skills', ['skill_id'], unique=False)
    op.create_index(op.f('ix_resume_skills_skill_name'), 'resume_skills', ['skill_name'], unique=False)

    # 6. job_postings
    op.create_table(
        'job_postings',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('company', sa.String(length=255), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('target_role', sa.String(length=255), nullable=False),
        sa.Column('skills', sa.JSON(), nullable=False),
        sa.Column('experience', sa.String(length=100), nullable=True),
        sa.Column('salary_min', sa.Float(), nullable=True),
        sa.Column('salary_max', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='LPA'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='live_api'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_job_postings_title'), 'job_postings', ['title'], unique=False)
    op.create_index(op.f('ix_job_postings_company'), 'job_postings', ['company'], unique=False)
    op.create_index(op.f('ix_job_postings_target_role'), 'job_postings', ['target_role'], unique=False)
    op.create_index(op.f('ix_job_postings_posted_at'), 'job_postings', ['posted_at'], unique=False)

    # 7. role_taxonomy
    op.create_table(
        'role_taxonomy',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('role_name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('required_skills', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_role_taxonomy_role_name'), 'role_taxonomy', ['role_name'], unique=True)

    # 8. skill_demand
    op.create_table(
        'skill_demand',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=255), nullable=False),
        sa.Column('skill', sa.String(length=255), nullable=False),
        sa.Column('demand_pct', sa.Float(), nullable=False),
        sa.Column('month', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'skill', 'month', name='uix_skill_demand_role_skill_month')
    )
    op.create_index(op.f('ix_skill_demand_role'), 'skill_demand', ['role'], unique=False)
    op.create_index(op.f('ix_skill_demand_skill'), 'skill_demand', ['skill'], unique=False)
    op.create_index(op.f('ix_skill_demand_month'), 'skill_demand', ['month'], unique=False)

    # 9. analyses
    op.create_table(
        'analyses',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('target_role', sa.String(length=255), nullable=False),
        sa.Column('ats_score', sa.Float(), nullable=False),
        sa.Column('breakdown', sa.JSON(), nullable=False),
        sa.Column('skill_gap', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analyses_resume_id'), 'analyses', ['resume_id'], unique=False)
    op.create_index(op.f('ix_analyses_target_role'), 'analyses', ['target_role'], unique=False)

    # 10. market_fit
    op.create_table(
        'market_fit',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('fit_score', sa.Float(), nullable=False),
        sa.Column('salary_min', sa.Float(), nullable=False),
        sa.Column('salary_max', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('unit', sa.String(length=20), nullable=False, server_default='LPA'),
        sa.Column('top_factors', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_market_fit_resume_id'), 'market_fit', ['resume_id'], unique=False)

    # 11. roadmaps
    op.create_table(
        'roadmaps',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('target_role', sa.String(length=255), nullable=False),
        sa.Column('phases', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roadmaps_resume_id'), 'roadmaps', ['resume_id'], unique=False)

    # 12. critiques
    op.create_table(
        'critiques',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('resume_id', sa.String(length=64), nullable=False),
        sa.Column('agents', sa.JSON(), nullable=False),
        sa.Column('merged', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_critiques_resume_id'), 'critiques', ['resume_id'], unique=False)

    # 13. audit_logs
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=100), nullable=False),
        sa.Column('target_id', sa.String(length=64), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)

def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('critiques')
    op.drop_table('roadmaps')
    op.drop_table('market_fit')
    op.drop_table('analyses')
    op.drop_table('skill_demand')
    op.drop_table('role_taxonomy')
    op.drop_table('job_postings')
    op.drop_table('resume_skills')
    op.drop_table('skills')
    op.drop_table('parsed_entities')
    op.drop_table('resumes')
    op.drop_table('users')
