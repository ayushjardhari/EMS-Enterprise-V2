"""enterprise HR domains: leave payroll audit
Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg
revision='0003'; down_revision='0002'; branch_labels=None; depends_on=None

def upgrade():
    uuid=pg.UUID(as_uuid=True)
    op.create_table('leave_types', sa.Column('id',uuid,primary_key=True), sa.Column('name',sa.String(80),nullable=False,unique=True), sa.Column('annual_days',sa.Numeric(5,1),nullable=False,server_default='12'), sa.Column('is_active',sa.Boolean(),nullable=False,server_default=sa.true()))
    op.create_table('leave_balances', sa.Column('id',uuid,primary_key=True), sa.Column('employee_id',uuid,sa.ForeignKey('employees.id',ondelete='CASCADE'),nullable=False), sa.Column('leave_type_id',uuid,sa.ForeignKey('leave_types.id',ondelete='CASCADE'),nullable=False), sa.Column('year',sa.Integer(),nullable=False), sa.Column('allocated_days',sa.Numeric(5,1),nullable=False), sa.Column('used_days',sa.Numeric(5,1),nullable=False,server_default='0'), sa.UniqueConstraint('employee_id','leave_type_id','year',name='uq_leave_balance'))
    op.create_index('ix_leave_balances_employee_id','leave_balances',['employee_id'])
    op.create_table('leave_requests', sa.Column('id',uuid,primary_key=True), sa.Column('employee_id',uuid,sa.ForeignKey('employees.id',ondelete='CASCADE'),nullable=False), sa.Column('leave_type_id',uuid,sa.ForeignKey('leave_types.id'),nullable=False), sa.Column('start_date',sa.Date(),nullable=False), sa.Column('end_date',sa.Date(),nullable=False), sa.Column('days',sa.Numeric(5,1),nullable=False), sa.Column('reason',sa.Text()), sa.Column('status',sa.String(20),nullable=False,server_default='PENDING'), sa.Column('reviewer_id',uuid,sa.ForeignKey('users.id',ondelete='SET NULL')), sa.Column('reviewed_at',sa.DateTime(timezone=True)), sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index('ix_leave_requests_employee_id','leave_requests',['employee_id']); op.create_index('ix_leave_requests_status','leave_requests',['status'])
    op.create_table('salary_profiles', sa.Column('id',uuid,primary_key=True), sa.Column('employee_id',uuid,sa.ForeignKey('employees.id',ondelete='CASCADE'),nullable=False,unique=True), sa.Column('basic_salary',sa.Numeric(12,2),nullable=False), sa.Column('housing_allowance',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('transport_allowance',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('other_allowance',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('effective_from',sa.Date(),nullable=False))
    op.create_table('payroll_runs', sa.Column('id',uuid,primary_key=True), sa.Column('period',sa.String(7),nullable=False,unique=True), sa.Column('status',sa.String(20),nullable=False,server_default='DRAFT'), sa.Column('processed_at',sa.DateTime(timezone=True)), sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index('ix_payroll_runs_period','payroll_runs',['period'])
    op.create_table('payroll_records', sa.Column('id',uuid,primary_key=True), sa.Column('payroll_run_id',uuid,sa.ForeignKey('payroll_runs.id',ondelete='CASCADE'),nullable=False), sa.Column('employee_id',uuid,sa.ForeignKey('employees.id',ondelete='CASCADE'),nullable=False), sa.Column('basic_salary',sa.Numeric(12,2),nullable=False), sa.Column('allowances',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('bonus',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('deductions',sa.Numeric(12,2),nullable=False,server_default='0'), sa.Column('gross_salary',sa.Numeric(12,2),nullable=False), sa.Column('net_salary',sa.Numeric(12,2),nullable=False), sa.Column('status',sa.String(20),nullable=False,server_default='PENDING'), sa.UniqueConstraint('payroll_run_id','employee_id',name='uq_payroll_employee_run'))
    op.create_index('ix_payroll_records_employee_id','payroll_records',['employee_id'])
    op.create_table('audit_logs', sa.Column('id',uuid,primary_key=True), sa.Column('actor_user_id',uuid,sa.ForeignKey('users.id',ondelete='SET NULL')), sa.Column('action',sa.String(100),nullable=False), sa.Column('entity_type',sa.String(80),nullable=False), sa.Column('entity_id',sa.String(100)), sa.Column('details',sa.Text()), sa.Column('created_at',sa.DateTime(timezone=True),server_default=sa.func.now()))
    op.create_index('ix_audit_logs_actor_user_id','audit_logs',['actor_user_id']); op.create_index('ix_audit_logs_action','audit_logs',['action']); op.create_index('ix_audit_logs_created_at','audit_logs',['created_at'])

def downgrade():
    for t in ['audit_logs','payroll_records','payroll_runs','salary_profiles','leave_requests','leave_balances','leave_types']:
        op.drop_table(t)
