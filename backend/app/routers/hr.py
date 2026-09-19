import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.deps import get_current_user, get_db, require_roles
from app.models.employee import Employee
from app.models.department import Department
from app.models.hr import LeaveType, LeaveBalance, LeaveRequest, SalaryProfile, PayrollRun, PayrollRecord, AuditLog
from app.models.user import User, UserRole

router=APIRouter(prefix='/api/v1',tags=['hr'])

def money(v): return float(v or 0)
def visible_employee_ids(db,user):
    if user.user_role in (UserRole.ADMIN,UserRole.HR): return None
    if user.employee_id: return [user.employee_id]
    return []

@router.get('/analytics/overview')
def overview(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    ids=visible_employee_ids(db,user); eq=[] if ids is None else [Employee.id.in_(ids)]
    total=db.scalar(select(func.count(Employee.id)).where(*eq)) or 0
    active=db.scalar(select(func.count(Employee.id)).where(Employee.employment_status=='ACTIVE',*eq)) or 0
    today=date.today()
    from app.models.attendance import Attendance
    present=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==today,Attendance.status.in_(['PRESENT','WORK_FROM_HOME','HALF_DAY']), *( [Attendance.employee_id.in_(ids)] if ids is not None else []))) or 0
    late=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==today,Attendance.status=='LATE', *( [Attendance.employee_id.in_(ids)] if ids is not None else []))) or 0
    onleave=db.scalar(select(func.count(LeaveRequest.id)).where(LeaveRequest.status=='APPROVED',LeaveRequest.start_date<=today,LeaveRequest.end_date>=today, *( [LeaveRequest.employee_id.in_(ids)] if ids is not None else []))) or 0
    pending=db.scalar(select(func.count(LeaveRequest.id)).where(LeaveRequest.status=='PENDING', *( [LeaveRequest.employee_id.in_(ids)] if ids is not None else []))) or 0
    dept_rows=db.execute(select(Employee.department_id,func.count(Employee.id)).where(*eq).group_by(Employee.department_id).order_by(func.count(Employee.id).desc()).limit(6)).all()
    return {'total_employees':total,'active_employees':active,'present_today':present,'absent_today':max(active-present-onleave,0),'late_today':late,'on_leave':onleave,'pending_leave':pending,'department_headcount':[{'department_id':str(d),'count':c} for d,c in dept_rows]}

@router.get('/analytics/trend')
def attendance_trend(days:int=14,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.models.attendance import Attendance
    days=max(7,min(days,31))
    ids=visible_employee_ids(db,user)
    scope=[Attendance.employee_id.in_(ids)] if ids is not None else []
    active_scope=[Employee.id.in_(ids)] if ids is not None else []
    rows=[]
    start=date.today()-__import__('datetime').timedelta(days=days-1)
    for offset in range(days):
        day=start+__import__('datetime').timedelta(days=offset)
        total=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==day,*scope)) or 0
        present=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==day,Attendance.status.in_(['PRESENT','HALF_DAY']),*scope)) or 0
        wfh=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==day,Attendance.status=='WORK_FROM_HOME',*scope)) or 0
        late=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==day,Attendance.status=='LATE',*scope)) or 0
        absent=db.scalar(select(func.count(Attendance.id)).where(Attendance.attendance_date==day,Attendance.status=='ABSENT',*scope)) or 0
        rows.append({'date':day.isoformat(),'total':total,'present':present,'wfh':wfh,'late':late,'absent':absent})
    return rows

@router.get('/analytics/departments')
def department_attendance(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.models.attendance import Attendance
    ids=visible_employee_ids(db,user)
    employee_scope=[Employee.id.in_(ids)] if ids is not None else []
    today=date.today()
    departments=db.execute(select(Department.id,Department.name).order_by(Department.name)).all()
    result=[]
    for did,name in departments:
        if ids is not None and not db.scalar(select(func.count(Employee.id)).where(Employee.department_id==did,*employee_scope)):
            continue
        total=db.scalar(select(func.count(Employee.id)).where(Employee.department_id==did,Employee.employment_status=='ACTIVE',*employee_scope)) or 0
        present=db.scalar(select(func.count(Attendance.id)).join(Employee,Employee.id==Attendance.employee_id).where(Attendance.attendance_date==today,Employee.department_id==did,Attendance.status.in_(['PRESENT','HALF_DAY','WORK_FROM_HOME']),*employee_scope)) or 0
        late=db.scalar(select(func.count(Attendance.id)).join(Employee,Employee.id==Attendance.employee_id).where(Attendance.attendance_date==today,Employee.department_id==did,Attendance.status=='LATE',*employee_scope)) or 0
        absent=max(total-present-late,0)
        result.append({'department_id':str(did),'department':name,'total':total,'present':present,'late':late,'absent':absent,'attendance_rate':round((present/total)*100,1) if total else 0})
    return result

@router.get('/attendance/today')
def attendance_today(date_:date|None=Query(None,alias='date'),department_id:uuid.UUID|None=None,status:str|None=None,search:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.models.attendance import Attendance
    q=select(Attendance,Employee).join(Employee,Employee.id==Attendance.employee_id).where(Attendance.attendance_date==(date_ or date.today()))
    if user.user_role==UserRole.EMPLOYEE:
        q=q.where(Employee.id==user.employee_id)
    if user.user_role==UserRole.MANAGER and user.employee_id: q=q.where(Employee.department_id==select(Employee.department_id).where(Employee.id==user.employee_id).scalar_subquery())
    if department_id: q=q.where(Employee.department_id==department_id)
    if status: q=q.where(Attendance.status==status.upper())
    if search: q=q.where((Employee.full_name.ilike(f'%{search}%'))|(Employee.employee_code.ilike(f'%{search}%')))
    rows=db.execute(q.order_by(Employee.full_name)).all()
    return [{'id':str(a.id),'employee_id':str(e.id),'employee_name':e.full_name,'employee_code':e.employee_code,'department_id':str(e.department_id),'date':a.attendance_date.isoformat(),'check_in':a.check_in,'check_out':a.check_out,'hours':money(a.work_hours),'status':a.status} for a,e in rows]

@router.get('/leave/requests')
def leave_requests(status:str|None=None,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    q=select(LeaveRequest,Employee,LeaveType).join(Employee,Employee.id==LeaveRequest.employee_id).join(LeaveType,LeaveType.id==LeaveRequest.leave_type_id)
    if user.user_role==UserRole.EMPLOYEE: q=q.where(LeaveRequest.employee_id==user.employee_id)
    if status: q=q.where(LeaveRequest.status==status.upper())
    rows=db.execute(q.order_by(LeaveRequest.created_at.desc())).all()
    return [{'id':str(r.id),'employee_id':str(e.id),'employee_name':e.full_name,'type':lt.name,'start_date':r.start_date.isoformat(),'end_date':r.end_date.isoformat(),'days':money(r.days),'reason':r.reason,'status':r.status} for r,e,lt in rows]

@router.post('/leave/requests')
def create_leave(payload:dict,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    eid=user.employee_id if user.user_role==UserRole.EMPLOYEE else uuid.UUID(payload['employee_id'])
    start=date.fromisoformat(payload['start_date']); end=date.fromisoformat(payload['end_date'])
    if end<start: raise HTTPException(400,'End date must be on or after start date')
    days=(end-start).days+1
    lt=db.get(LeaveType,uuid.UUID(payload['leave_type_id']))
    if not lt: raise HTTPException(404,'Leave type not found')
    r=LeaveRequest(employee_id=eid,leave_type_id=lt.id,start_date=start,end_date=end,days=days,reason=payload.get('reason'))
    db.add(r); db.add(AuditLog(actor_user_id=user.id,action='CREATE',entity_type='LEAVE_REQUEST',entity_id=str(r.id),details='Leave request submitted')); db.commit(); db.refresh(r)
    return {'id':str(r.id),'status':r.status}

@router.post('/leave/requests/{request_id}/decision')
def decide_leave(request_id:uuid.UUID,decision:dict,db:Session=Depends(get_db),user:User=Depends(require_roles(UserRole.ADMIN,UserRole.HR,UserRole.MANAGER))):
    r=db.get(LeaveRequest,request_id)
    if not r: raise HTTPException(404,'Leave request not found')
    value=decision.get('status','').upper()
    if value not in ('APPROVED','REJECTED'): raise HTTPException(400,'Decision must be APPROVED or REJECTED')
    r.status=value; r.reviewer_id=user.id; r.reviewed_at=datetime.now(timezone.utc)
    if value=='APPROVED':
        bal=db.scalar(select(LeaveBalance).where(LeaveBalance.employee_id==r.employee_id,LeaveBalance.leave_type_id==r.leave_type_id,LeaveBalance.year==r.start_date.year))
        if bal: bal.used_days=Decimal(str(bal.used_days or 0))+Decimal(str(r.days))
    db.add(AuditLog(actor_user_id=user.id,action=value,entity_type='LEAVE_REQUEST',entity_id=str(r.id),details=f'Leave request {value.lower()}')); db.commit()
    return {'status':r.status}

@router.get('/leave/types')
def leave_types(db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return [{'id':str(x.id),'name':x.name,'annual_days':money(x.annual_days)} for x in db.scalars(select(LeaveType).where(LeaveType.is_active==True).order_by(LeaveType.name))]

@router.get('/payroll/overview')
def payroll_overview(period:str|None=None,db:Session=Depends(get_db),_:User=Depends(require_roles(UserRole.ADMIN,UserRole.HR))):
    run=db.scalar(select(PayrollRun).order_by(PayrollRun.period.desc())) if not period else db.scalar(select(PayrollRun).where(PayrollRun.period==period))
    if not run: return {'period':period,'status':'NOT_CREATED','gross':0,'deductions':0,'net':0,'employees':0,'processed':0}
    rows=list(db.scalars(select(PayrollRecord).where(PayrollRecord.payroll_run_id==run.id)))
    return {'period':run.period,'status':run.status,'gross':sum(money(x.gross_salary) for x in rows),'deductions':sum(money(x.deductions) for x in rows),'net':sum(money(x.net_salary) for x in rows),'employees':len(rows),'processed':sum(x.status=='PROCESSED' for x in rows)}

@router.get('/payroll/records')
def payroll_records(period:str|None=None,db:Session=Depends(get_db),_:User=Depends(require_roles(UserRole.ADMIN,UserRole.HR))):
    run=db.scalar(select(PayrollRun).order_by(PayrollRun.period.desc())) if not period else db.scalar(select(PayrollRun).where(PayrollRun.period==period))
    if not run:return []
    rows=db.execute(select(PayrollRecord,Employee).join(Employee,Employee.id==PayrollRecord.employee_id).where(PayrollRecord.payroll_run_id==run.id).order_by(Employee.full_name)).all()
    return [{'id':str(r.id),'employee_id':str(e.id),'employee_name':e.full_name,'period':run.period,'basic':money(r.basic_salary),'allowances':money(r.allowances),'bonus':money(r.bonus),'deductions':money(r.deductions),'gross':money(r.gross_salary),'net':money(r.net_salary),'status':r.status} for r,e in rows]

@router.post('/payroll/runs')
def create_payroll(payload:dict,db:Session=Depends(get_db),user:User=Depends(require_roles(UserRole.ADMIN,UserRole.HR))):
    period=payload['period']; existing=db.scalar(select(PayrollRun).where(PayrollRun.period==period))
    if existing: raise HTTPException(409,'Payroll run already exists for this period')
    run=PayrollRun(period=period,status='PROCESSED',processed_at=datetime.now(timezone.utc)); db.add(run); db.flush()
    for e in db.scalars(select(Employee).where(Employee.employment_status=='ACTIVE')):
        sp=db.scalar(select(SalaryProfile).where(SalaryProfile.employee_id==e.id))
        basic=Decimal(str(sp.basic_salary if sp else 50000)); allowances=Decimal(str((sp.housing_allowance+sp.transport_allowance+sp.other_allowance) if sp else 10000)); bonus=Decimal('0'); deductions=(basic+allowances)*Decimal('0.10'); gross=basic+allowances+bonus; net=gross-deductions
        db.add(PayrollRecord(payroll_run_id=run.id,employee_id=e.id,basic_salary=basic,allowances=allowances,bonus=bonus,deductions=deductions,gross_salary=gross,net_salary=net,status='PROCESSED'))
    db.add(AuditLog(actor_user_id=user.id,action='CREATE',entity_type='PAYROLL_RUN',entity_id=str(run.id),details=f'Payroll processed for {period}')); db.commit(); return {'id':str(run.id),'period':period,'status':run.status}


@router.get('/payroll/my')
def my_payroll(db:Session=Depends(get_db),user:User=Depends(require_roles(UserRole.EMPLOYEE))):
    if not user.employee_id: return []
    rows=db.execute(select(PayrollRecord,PayrollRun).join(PayrollRun,PayrollRun.id==PayrollRecord.payroll_run_id).where(PayrollRecord.employee_id==user.employee_id).order_by(PayrollRun.period.desc())).all()
    return [{'period':run.period,'basic':money(r.basic_salary),'allowances':money(r.allowances),'bonus':money(r.bonus),'deductions':money(r.deductions),'gross':money(r.gross_salary),'net':money(r.net_salary),'status':r.status} for r,run in rows]

@router.get('/audit-logs')
def audit_logs(db:Session=Depends(get_db),_:User=Depends(require_roles(UserRole.ADMIN,UserRole.HR))):
    rows=db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)).all()
    return [{'id':str(x.id),'action':x.action,'entity_type':x.entity_type,'entity_id':x.entity_id,'details':x.details,'created_at':x.created_at} for x in rows]
