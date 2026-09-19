"""
Development seed script — a small, realistic dataset for local testing.
Not real people's data: names/emails are Faker-generated.

Run inside the backend container (or locally with DATABASE_URL pointed at
your dev Postgres): python seed.py
"""
import random
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from faker import Faker

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.department import Department
from app.models.employee import AvailabilityStatus, Employee, EmploymentStatus
from app.models.attendance import Attendance
from app.models.employee_project import EmployeeProject
from app.models.employee_skill import EmployeeSkill, ProficiencyLevel
from app.models.job_role import JobRole
from app.models.project import Project, ProjectStatus
from app.models.skill import Skill
from app.models.user import User, UserRole
from app.models.hr import LeaveType, LeaveBalance, LeaveRequest, SalaryProfile, PayrollRun, PayrollRecord, AuditLog

fake = Faker()
random.seed(42)
Faker.seed(42)

DEPARTMENTS = ["Engineering", "Human Resources", "Sales", "Marketing", "Finance"]
JOB_ROLES = [
    "Backend Developer", "Frontend Developer", "DevOps Engineer", "Data Analyst",
    "Product Manager", "HR Specialist", "Sales Executive", "Marketing Associate",
    "QA Engineer", "UI/UX Designer",
]

INDIAN_NAMES = [
    "Aarav Sharma", "Vivaan Verma", "Aditya Singh", "Arjun Negi", "Rohan Joshi",
    "Kabir Mehta", "Ishaan Kapoor", "Rahul Rawat", "Kunal Bisht", "Ankit Chauhan",
    "Yash Thakur", "Mohit Rana", "Siddharth Tiwari", "Nikhil Gupta", "Varun Bhatia",
    "Akash Pandey", "Harsh Vashisht", "Manish Kumar", "Abhishek Yadav", "Saurabh Mishra",
    "Ananya Sharma", "Aditi Verma", "Priya Singh", "Isha Negi", "Kavya Joshi",
    "Riya Mehta", "Sneha Kapoor", "Neha Rawat", "Pooja Bisht", "Simran Chauhan",
    "Shreya Thakur", "Nandini Rana", "Sakshi Tiwari", "Muskan Gupta", "Tanya Bhatia",
    "Meera Pandey", "Radhika Vashisht", "Divya Kumar", "Anjali Yadav", "Ishita Mishra",
    "Ritvik Sharma", "Dev Verma", "Ayush Singh", "Aman Negi", "Varun Joshi",
    "Dhruv Mehta", "Manav Kapoor", "Rishabh Rawat", "Gaurav Bisht", "Vikas Chauhan",
]

SKILLS = [
    ("Python", "Programming"), ("JavaScript", "Programming"), ("TypeScript", "Programming"),
    ("React", "Frontend"), ("FastAPI", "Backend"), ("SQL", "Database"), ("PostgreSQL", "Database"),
    ("Docker", "DevOps"), ("Kubernetes", "DevOps"), ("AWS", "Cloud"), ("GCP", "Cloud"),
    ("NLP", "AI/ML"), ("Machine Learning", "AI/ML"), ("Data Analysis", "Data"),
    ("Project Management", "Management"), ("Communication", "Soft Skill"), ("Leadership", "Soft Skill"),
    ("Sales Strategy", "Sales"), ("SEO", "Marketing"), ("Content Writing", "Marketing"),
    ("Figma", "Design"), ("UI Design", "Design"), ("Excel", "Office"), ("Tableau", "Data"),
    ("Java", "Programming"), ("Go", "Programming"), ("Linux", "DevOps"), ("CI/CD", "DevOps"),
    ("Testing", "QA"), ("Selenium", "QA"), ("Negotiation", "Soft Skill"),
]


def run() -> None:
    db = SessionLocal()
    try:
        if db.query(Department).count() > 0:
            # Existing core dataset: only backfill newly introduced enterprise HR tables.
            employees_existing = db.query(Employee).all()
            if db.query(LeaveType).count() == 0 and employees_existing:
                leave_types = [LeaveType(name="Annual Leave", annual_days=18), LeaveType(name="Sick Leave", annual_days=10), LeaveType(name="Casual Leave", annual_days=7), LeaveType(name="Unpaid Leave", annual_days=0)]
                db.add_all(leave_types); db.flush()
                for e in employees_existing:
                    for lt in leave_types[:3]: db.add(LeaveBalance(employee_id=e.id, leave_type_id=lt.id, year=date.today().year, allocated_days=lt.annual_days, used_days=Decimal("0")))
            if db.query(SalaryProfile).count() == 0 and employees_existing:
                for e in employees_existing:
                    basic=Decimal(str(random.randint(45000,180000))); db.add(SalaryProfile(employee_id=e.id,basic_salary=basic,housing_allowance=basic*Decimal("0.20"),transport_allowance=Decimal("5000"),other_allowance=Decimal("2500"),effective_from=e.joining_date))
            db.flush()
            if db.query(PayrollRun).count() == 0 and employees_existing:
                run=PayrollRun(period=date.today().strftime("%Y-%m"),status="PROCESSED",processed_at=datetime.now(timezone.utc)); db.add(run); db.flush()
                for e in employees_existing:
                    sp=db.query(SalaryProfile).filter(SalaryProfile.employee_id==e.id).first()
                    allowances=sp.housing_allowance+sp.transport_allowance+sp.other_allowance; gross=sp.basic_salary+allowances; deductions=(gross*Decimal("0.10")).quantize(Decimal("0.01"))
                    db.add(PayrollRecord(payroll_run_id=run.id,employee_id=e.id,basic_salary=sp.basic_salary,allowances=allowances,bonus=Decimal("0"),deductions=deductions,gross_salary=gross,net_salary=gross-deductions,status="PROCESSED"))
            if db.query(LeaveRequest).count() == 0 and employees_existing:
                lt=db.query(LeaveType).filter(LeaveType.name=="Annual Leave").first()
                if lt:
                    for e in employees_existing[:8]:
                        start=date.today()+timedelta(days=random.randint(1,20)); db.add(LeaveRequest(employee_id=e.id,leave_type_id=lt.id,start_date=start,end_date=start+timedelta(days=1),days=2,reason=random.choice(["Family event","Personal work","Travel plans"]),status=random.choice(["PENDING","PENDING","APPROVED"])))

            # --- Backfill a realistic attendance history for existing databases ---
            # Idempotent: only missing employee/date records are inserted. Includes today
            # so the dashboard and Attendance command center have useful demo data.
            existing_attendance = {
                (row.employee_id, row.attendance_date)
                for row in db.query(Attendance.employee_id, Attendance.attendance_date).all()
            }
            active_employees = sorted(
                [e for e in employees_existing if e.employment_status.value == "ACTIVE"],
                key=lambda e: e.employee_code,
            )
            attendance_added = 0
            today = date.today()
            for employee_index, employee in enumerate(active_employees):
                for days_ago in range(0, 31):
                    day = today - timedelta(days=days_ago)
                    if day.weekday() >= 5 or (employee.id, day) in existing_attendance:
                        continue

                    # Stable distribution so rerunning the seed produces the same demo data.
                    roll = (employee_index * 17 + days_ago * 13) % 100
                    if roll < 6:
                        status_value = "ABSENT"
                    elif roll < 14:
                        status_value = "WORK_FROM_HOME"
                    elif roll < 23:
                        status_value = "LATE"
                    else:
                        status_value = "PRESENT"

                    check_in = check_out = None
                    work_hours = None
                    notes = None
                    if status_value != "ABSENT":
                        if status_value == "LATE":
                            minute = 32 + ((employee_index * 7 + days_ago * 3) % 42)
                            check_in = datetime.combine(day, datetime.min.time()).replace(
                                hour=9 + minute // 60, minute=minute % 60, tzinfo=timezone.utc
                            )
                            notes = "Late arrival"
                        elif status_value == "WORK_FROM_HOME":
                            minute = 5 + ((employee_index * 5 + days_ago * 2) % 26)
                            check_in = datetime.combine(day, datetime.min.time()).replace(
                                hour=9, minute=minute, tzinfo=timezone.utc
                            )
                            notes = "Remote work"
                        else:
                            minute = 2 + ((employee_index * 3 + days_ago * 5) % 28)
                            check_in = datetime.combine(day, datetime.min.time()).replace(
                                hour=9, minute=minute, tzinfo=timezone.utc
                            )

                        duration_minutes = 480 + ((employee_index * 11 + days_ago * 7) % 76)
                        check_out = check_in + timedelta(minutes=duration_minutes)
                        work_hours = round(duration_minutes / 60, 2)

                    db.add(Attendance(
                        employee_id=employee.id,
                        attendance_date=day,
                        check_in=check_in,
                        check_out=check_out,
                        status=status_value,
                        work_hours=work_hours,
                        notes=notes,
                    ))
                    attendance_added += 1

            db.commit()
            print(f"Core seed data already present — HR domain backfilled. Attendance records added: {attendance_added}.")
            return

        departments = [Department(name=name) for name in DEPARTMENTS]
        db.add_all(departments)
        db.flush()

        job_roles = [JobRole(title=title) for title in JOB_ROLES]
        db.add_all(job_roles)
        db.flush()

        skills = [Skill(name=name, category=category) for name, category in SKILLS]
        db.add_all(skills)
        db.flush()

        employees = []
        for i in range(100):
            employee = Employee(
                employee_code=f"EMP-{i + 1:05d}",
                full_name=INDIAN_NAMES[i % len(INDIAN_NAMES)] if i < len(INDIAN_NAMES) else f"Employee {i + 1}",
                email=fake.unique.email(),
                phone=fake.phone_number()[:30],
                location=fake.city(),
                department_id=random.choice(departments).id,
                job_role_id=random.choice(job_roles).id,
                joining_date=fake.date_between(start_date="-5y", end_date="today"),
                employment_status=random.choices(
                    list(EmploymentStatus), weights=[85, 10, 5]
                )[0],
                availability_status=random.choices(
                    list(AvailabilityStatus), weights=[60, 25, 15]
                )[0],
            )
            employees.append(employee)
        db.add_all(employees)
        db.flush()

        for employee in employees:
            for skill in random.sample(skills, k=random.randint(2, 6)):
                db.add(
                    EmployeeSkill(
                        employee_id=employee.id,
                        skill_id=skill.id,
                        proficiency_level=random.choice(list(ProficiencyLevel)),
                        years_of_experience=round(random.uniform(0.5, 12), 1),
                    )
                )

        projects = []
        for i in range(20):
            start = fake.date_between(start_date="-2y", end_date="today")
            status_ = random.choice(list(ProjectStatus))
            project = Project(
                project_code=f"PRJ-{i + 1:05d}",
                project_name=f"{fake.bs().title()} Initiative",
                description=fake.paragraph(nb_sentences=3),
                department_id=random.choice(departments).id,
                status=status_,
                start_date=start,
                end_date=start + timedelta(days=random.randint(60, 400)) if status_ == ProjectStatus.COMPLETED else None,
            )
            projects.append(project)
        db.add_all(projects)
        db.flush()

        for project in projects:
            for employee in random.sample(employees, k=random.randint(3, 8)):
                db.add(
                    EmployeeProject(
                        employee_id=employee.id,
                        project_id=project.id,
                        project_role=random.choice(["Contributor", "Tech Lead", "Reviewer", "Coordinator"]),
                        start_date=project.start_date,
                        end_date=project.end_date,
                    )
                )

        # --- Realistic attendance history for dashboard/profile testing ---
        # Includes today plus the previous 30 calendar days (weekends skipped).
        # The deterministic distribution gives the UI meaningful PRESENT, LATE,
        # WORK_FROM_HOME and ABSENT records without relying on live punch-ins.
        today = date.today()
        active_employees = [e for e in employees if e.employment_status.value == "ACTIVE"]
        for employee_index, employee in enumerate(active_employees):
            for days_ago in range(0, 31):
                day = today - timedelta(days=days_ago)
                if day.weekday() >= 5:
                    continue
                roll = (employee_index * 17 + days_ago * 13) % 100
                if roll < 6:
                    status_value = "ABSENT"
                elif roll < 14:
                    status_value = "WORK_FROM_HOME"
                elif roll < 23:
                    status_value = "LATE"
                else:
                    status_value = "PRESENT"

                check_in = check_out = None
                work_hours = None
                notes = None
                if status_value != "ABSENT":
                    if status_value == "LATE":
                        minute = 32 + ((employee_index * 7 + days_ago * 3) % 42)
                        check_in = datetime.combine(day, datetime.min.time()).replace(
                            hour=9 + minute // 60, minute=minute % 60, tzinfo=timezone.utc
                        )
                        notes = "Late arrival"
                    elif status_value == "WORK_FROM_HOME":
                        minute = 5 + ((employee_index * 5 + days_ago * 2) % 26)
                        check_in = datetime.combine(day, datetime.min.time()).replace(
                            hour=9, minute=minute, tzinfo=timezone.utc
                        )
                        notes = "Remote work"
                    else:
                        minute = 2 + ((employee_index * 3 + days_ago * 5) % 28)
                        check_in = datetime.combine(day, datetime.min.time()).replace(
                            hour=9, minute=minute, tzinfo=timezone.utc
                        )

                    duration_minutes = 480 + ((employee_index * 11 + days_ago * 7) % 76)
                    check_out = check_in + timedelta(minutes=duration_minutes)
                    work_hours = round(duration_minutes / 60, 2)

                db.add(Attendance(
                    employee_id=employee.id, attendance_date=day, check_in=check_in, check_out=check_out,
                    status=status_value, work_hours=work_hours, notes=notes
                ))

        # --- Demo login accounts (one per role) ---
        demo_users = [
            User(email="admin@acmecorp.example", hashed_password=hash_password("Admin@123"), user_role=UserRole.ADMIN),
            User(email="hr@acmecorp.example", hashed_password=hash_password("Hr@12345"), user_role=UserRole.HR),
            User(
                email="manager@acmecorp.example",
                hashed_password=hash_password("Manager@123"),
                user_role=UserRole.MANAGER,
                employee_id=employees[0].id,
            ),
            User(
                email="employee@acmecorp.example",
                hashed_password=hash_password("Employee@123"),
                user_role=UserRole.EMPLOYEE,
                employee_id=employees[1].id,
            ),
        ]
        db.add_all(demo_users)

        # --- Enterprise HR domain seed ---
        leave_types = [LeaveType(name="Annual Leave", annual_days=18), LeaveType(name="Sick Leave", annual_days=10), LeaveType(name="Casual Leave", annual_days=7), LeaveType(name="Unpaid Leave", annual_days=0)]
        db.add_all(leave_types)
        db.flush()
        for employee in employees:
            for lt in leave_types[:3]:
                db.add(LeaveBalance(employee_id=employee.id, leave_type_id=lt.id, year=today.year, allocated_days=lt.annual_days, used_days=Decimal("0")))
            if employee in employees[:8]:
                start=today+timedelta(days=random.randint(1,20)); db.add(LeaveRequest(employee_id=employee.id,leave_type_id=leave_types[0].id,start_date=start,end_date=start+timedelta(days=1),days=2,reason=random.choice(["Family event","Personal work","Travel plans"]),status="PENDING"))
            basic = Decimal(str(random.randint(45000, 180000)))
            db.add(SalaryProfile(employee_id=employee.id, basic_salary=basic, housing_allowance=basic*Decimal("0.20"), transport_allowance=Decimal("5000"), other_allowance=Decimal("2500"), effective_from=employee.joining_date))
        db.flush()
        period=today.strftime("%Y-%m")
        run=PayrollRun(period=period,status="PROCESSED",processed_at=datetime.now(timezone.utc))
        db.add(run); db.flush()
        for employee in employees:
            sp=db.query(SalaryProfile).filter(SalaryProfile.employee_id==employee.id).first()
            allowances=sp.housing_allowance+sp.transport_allowance+sp.other_allowance
            gross=sp.basic_salary+allowances
            deductions=(gross*Decimal("0.10")).quantize(Decimal("0.01"))
            db.add(PayrollRecord(payroll_run_id=run.id,employee_id=employee.id,basic_salary=sp.basic_salary,allowances=allowances,bonus=Decimal("0"),deductions=deductions,gross_salary=gross,net_salary=gross-deductions,status="PROCESSED"))
        db.add(AuditLog(actor_user_id=demo_users[0].id, action="SEED", entity_type="SYSTEM", details="Enterprise HR seed initialized"))

        db.commit()
        print("Seed complete: 5 departments, 10 job roles, 30 skills, 100 employees, 20 projects.")
        print("Demo logins: admin@acmecorp.example / Admin@123, hr@acmecorp.example / Hr@12345, "
              "manager@acmecorp.example / Manager@123, employee@acmecorp.example / Employee@123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
