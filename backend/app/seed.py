"""
Seed script for SmartCivicAI.

Run with (after `alembic upgrade head`):
    cd backend
    python -m app.seed

Creates:
  - The 4 fixed modules with their spec-defined categories (EN/TE/HI)
  - 2 departments per module (8 total)
  - 3 demo accounts: admin@smartcivicai.gov.in / officer@smartcivicai.gov.in /
    citizen@smartcivicai.gov.in (+ a handful of extra citizens so complaints
    aren't all attributed to one person)
  - ~60 DEMO complaints (is_demo_data=True) spread across every module,
    category, status, priority, language, and a 4-month date range, with
    jittered lat/lng around Hyderabad so the GIS map and dashboards have
    something real to render immediately.

This script is idempotent-ish: it checks for the fixed demo emails and the
module codes before inserting, so re-running it won't create duplicate
admin/officer/citizen accounts or duplicate modules. Demo complaints ARE
appended each run (each gets a fresh complaint_number), so don't run this
against a database you don't want extra demo rows in.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.core.enums import ComplaintStatus, LanguageCode, ModuleCode, PriorityLevel, UserRole
from app.core.security import hash_password
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.misc import Feedback
from app.models.module import Category, Module
from app.models.user import User
from app.ai.pipeline import run_ai_pipeline
from app.services.complaint_service import change_status, generate_complaint_number

random.seed(42)  # reproducible demo data

HYDERABAD_LAT, HYDERABAD_LNG = 17.3850, 78.4867

MODULES_DATA = [
    {
        "code": ModuleCode.GOVERNMENT_SCHOOLS, "name_en": "Government Schools",
        "name_te": "ప్రభుత్వ పాఠశాలలు", "name_hi": "सरकारी स्कूल", "icon": "school",
        "categories": [
            ("School infrastructure", "పాఠశాల మౌలిక సదుపాయాలు", "स्कूल अवसंरचना", "building,roof,wall,infrastructure,construction"),
            ("Drinking water", "తాగునీరు", "पेयजल", "water,drinking water,tap,thirsty"),
            ("Toilets/sanitation", "మరుగుదొడ్లు/పారిశుధ్యం", "शौचालय/स्वच्छता", "toilet,sanitation,restroom,hygiene"),
            ("Electricity", "విద్యుత్", "बिजली", "electricity,power,fan,light,wiring"),
            ("Classroom/furniture", "తరగతి గది/ఫర్నిచర్", "कक्षा/फर्नीचर", "classroom,furniture,desk,bench,chair"),
            ("Teacher-related issues", "ఉపాధ్యాయ సంబంధిత సమస్యలు", "शिक्षक संबंधी समस्याएं", "teacher,absent,staff shortage"),
            ("Student facilities", "విద్యార్థి సౌకర్యాలు", "छात्र सुविधाएं", "student,facility,library,uniform,books"),
            ("Mid-day meal", "మధ్యాహ్న భోజనం", "मध्याह्न भोजन", "mid-day meal,midday meal,food,lunch,quality"),
            ("Safety", "భద్రత", "सुरक्षा", "safety,security,fence,guard,unsafe"),
            ("Other", "ఇతర", "अन्य", ""),
        ],
    },
    {
        "code": ModuleCode.AGRICULTURE, "name_en": "Agriculture",
        "name_te": "వ్యవసాయం", "name_hi": "कृषि", "icon": "wheat",
        "categories": [
            ("Crop disease", "పంట వ్యాధి", "फसल रोग", "crop disease,blight,fungus,infection"),
            ("Pest attack", "పురుగుల దాడి", "कीट हमला", "pest,pest infestation,insects,locust"),
            ("Irrigation", "నీటిపారుదల", "सिंचाई", "irrigation,canal,water supply,borewell"),
            ("Fertilizer", "ఎరువులు", "उर्वरक", "fertilizer,urea,nutrient,manure"),
            ("Seeds", "విత్తనాలు", "बीज", "seeds,seed quality,germination"),
            ("Subsidy", "రాయితీ", "सब्सिडी", "subsidy,scheme,loan,payment delay"),
            ("Weather/crop damage", "వాతావరణం/పంట నష్టం", "मौसम/फसल क्षति", "flooding,drought,hailstorm,crop damage,weather"),
            ("Agricultural equipment", "వ్యవసాయ పరికరాలు", "कृषि उपकरण", "tractor,equipment,machinery,tools"),
            ("Market-related issue", "మార్కెట్ సంబంధిత సమస్య", "बाजार संबंधी समस्या", "market,mandi,price,middleman"),
            ("Other", "ఇతర", "अन्य", ""),
        ],
    },
    {
        "code": ModuleCode.HEALTHCARE, "name_en": "Healthcare",
        "name_te": "ఆరోగ్య సంరక్షణ", "name_hi": "स्वास्थ्य सेवा", "icon": "hospital",
        "categories": [
            ("Hospital infrastructure", "ఆసుపత్రి మౌలిక సదుపాయాలు", "अस्पताल अवसंरचना", "hospital building,infrastructure,ward,beds"),
            ("Medicine availability", "మందుల లభ్యత", "दवा उपलब्धता", "medicine shortage,medicine availability,drugs,pharmacy"),
            ("Doctor/staff availability", "వైద్యుడు/సిబ్బంది లభ్యత", "डॉक्टर/कर्मचारी उपलब्धता", "no doctor,doctor,nurse,staff shortage"),
            ("Cleanliness", "పరిశుభ్రత", "सफाई", "dirty,cleanliness,hygiene,unclean"),
            ("Equipment", "పరికరాలు", "उपकरण", "equipment,machine,ventilator,x-ray"),
            ("Waiting time", "వేచి ఉండే సమయం", "प्रतीक्षा समय", "waiting time,long queue,delay"),
            ("Ambulance/service issue", "అంబులెన్స్/సేవ సమస్య", "एम्बुलेंस/सेवा समस्या", "ambulance,emergency service,108"),
            ("Patient facilities", "రోగి సౌకర్యాలు", "रोगी सुविधाएं", "patient facility,bed,washroom"),
            ("Other", "ఇతర", "अन्य", ""),
        ],
    },
    {
        "code": ModuleCode.TRAFFIC, "name_en": "Traffic",
        "name_te": "ట్రాఫిక్", "name_hi": "यातायात", "icon": "traffic-cone",
        "categories": [
            ("Traffic signal", "ట్రాఫిక్ సిగ్నల్", "यातायात संकेत", "traffic signal,broken signal,light not working"),
            ("Traffic congestion", "ట్రాఫిక్ రద్దీ", "यातायात जाम", "traffic congestion,jam,bottleneck"),
            ("Illegal parking", "అక్రమ పార్కింగ్", "अवैध पार्किंग", "illegal parking,no parking,blocking road"),
            ("Road safety", "రహదారి భద్రత", "सड़क सुरक्षा", "road safety,unsafe road,speeding"),
            ("Damaged road", "దెబ్బతిన్న రహదారి", "क्षतिग्रस्त सड़क", "pothole,damaged road,broken road"),
            ("Accident-prone area", "ప్రమాదకర ప్రాంతం", "दुर्घटना संभावित क्षेत्र", "accident,accident-prone,black spot"),
            ("Traffic violation", "ట్రాఫిక్ ఉల్లంఘన", "यातायात उल्लंघन", "violation,rule breaking,wrong side"),
            ("Street/road lighting", "వీధి/రహదారి లైటింగ్", "सड़क प्रकाश", "street light,dark road,lighting"),
            ("Other", "ఇతర", "अन्य", ""),
        ],
    },
]

DEPARTMENT_NAMES = {
    ModuleCode.GOVERNMENT_SCHOOLS: ["District Education Office", "School Infrastructure Wing"],
    ModuleCode.AGRICULTURE: ["District Agriculture Office", "Irrigation & Extension Wing"],
    ModuleCode.HEALTHCARE: ["District Health Office", "Primary Health Center Administration"],
    ModuleCode.TRAFFIC: ["Traffic Police Division", "Roads & Buildings Department"],
}

# (module, language, category_name_en, text) — kept short but realistic
SAMPLE_COMPLAINTS = [
    (ModuleCode.GOVERNMENT_SCHOOLS, "en", "Drinking water", "There is no clean drinking water available in the school for the past two weeks. Students are bringing water from home."),
    (ModuleCode.GOVERNMENT_SCHOOLS, "en", "Toilets/sanitation", "The girls' toilet block has been closed for repair for over a month, causing serious hygiene issues."),
    (ModuleCode.GOVERNMENT_SCHOOLS, "en", "Mid-day meal", "The mid-day meal served today had poor quality rice with visible insects. This is urgent and needs immediate action."),
    (ModuleCode.GOVERNMENT_SCHOOLS, "en", "Electricity", "Classrooms have no electricity due to a wiring fault, fans are not working in this summer heat."),
    (ModuleCode.GOVERNMENT_SCHOOLS, "hi", "Teacher-related issues", "स्कूल में गणित शिक्षक पिछले तीन महीने से नहीं आ रहे हैं, बच्चों की पढ़ाई का नुकसान हो रहा है।"),
    (ModuleCode.GOVERNMENT_SCHOOLS, "te", "School infrastructure", "పాఠశాల భవనం పైకప్పు కురుస్తోంది, వర్షాకాలంలో తరగతి గదులు నీటితో నిండిపోతున్నాయి. ప్రమాదకరంగా ఉంది."),
    (ModuleCode.AGRICULTURE, "en", "Pest attack", "Our cotton crop has been severely affected by pest infestation this week, we need urgent guidance and pesticide support."),
    (ModuleCode.AGRICULTURE, "en", "Irrigation", "The irrigation canal in our village has been dry for 10 days, crops are wilting without water."),
    (ModuleCode.AGRICULTURE, "en", "Subsidy", "I applied for the fertilizer subsidy scheme two months ago but have not received any update."),
    (ModuleCode.AGRICULTURE, "hi", "Weather/crop damage", "पिछले सप्ताह भारी बारिश और ओलावृष्टि से हमारी पूरी फसल बर्बाद हो गई है। कृपया नुकसान का आकलन करें।"),
    (ModuleCode.AGRICULTURE, "te", "Market-related issue", "మధ్యవర్తుల కారణంగా మా పంటకు మార్కెట్‌లో సరైన ధర లభించడం లేదు. దయచేసి చర్య తీసుకోండి."),
    (ModuleCode.AGRICULTURE, "en", "Seeds", "The seeds distributed under the government scheme have very low germination rate, less than 30%."),
    (ModuleCode.HEALTHCARE, "en", "Medicine availability", "The primary health center has been out of basic medicines like paracetamol and ORS for over a week."),
    (ModuleCode.HEALTHCARE, "en", "Doctor/staff availability", "There is no doctor present at the PHC during evening hours, patients are being turned away."),
    (ModuleCode.HEALTHCARE, "en", "Ambulance/service issue", "We called the ambulance for an emergency and it took over 90 minutes to arrive, this is a life threatening delay."),
    (ModuleCode.HEALTHCARE, "hi", "Cleanliness", "अस्पताल के वार्ड में सफाई की स्थिति बहुत खराब है, कूड़ा कई दिनों से नहीं उठाया गया।"),
    (ModuleCode.HEALTHCARE, "te", "Waiting time", "ఆసుపత్రిలో రోగులు గంటల తరబడి వేచి ఉండాల్సి వస్తోంది, సిబ్బంది సరిపడా లేరు."),
    (ModuleCode.HEALTHCARE, "en", "Hospital infrastructure", "The general ward ceiling is leaking during rains and there aren't enough beds for patients."),
    (ModuleCode.TRAFFIC, "en", "Traffic signal", "The traffic signal at the main junction has been non-functional for three days, causing chaos during peak hours."),
    (ModuleCode.TRAFFIC, "en", "Damaged road", "There is a large pothole on the main road that has caused two accidents already this month."),
    (ModuleCode.TRAFFIC, "en", "Accident-prone area", "This intersection has no proper signage and has seen a fatal accident last week, extremely dangerous."),
    (ModuleCode.TRAFFIC, "hi", "Illegal parking", "मुख्य सड़क के दोनों तरफ अवैध पार्किंग के कारण रोज़ाना भारी ट्रैफिक जाम लग रहा है।"),
    (ModuleCode.TRAFFIC, "te", "Street/road lighting", "ఈ రహదారిపై వీధి దీపాలు పనిచేయడం లేదు, రాత్రిపూట నడవడం చాలా ప్రమాదకరంగా ఉంది."),
    (ModuleCode.TRAFFIC, "en", "Traffic congestion", "Severe traffic congestion every morning near the bus stand, could use a traffic officer or better signal timing."),
]

DEMO_CITIZENS = [
    ("citizen@smartcivicai.gov.in", "Demo Citizen"),
    ("ravi.kumar@example.com", "Ravi Kumar"),
    ("lakshmi.devi@example.com", "Lakshmi Devi"),
    ("mohammed.arif@example.com", "Mohammed Arif"),
    ("priya.sharma@example.com", "Priya Sharma"),
    ("suresh.reddy@example.com", "Suresh Reddy"),
]

DEMO_PASSWORD = "Demo@1234"


def get_or_create_user(db, email, full_name, role, password=DEMO_PASSWORD, department_id=None, language=LanguageCode.EN):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(
        full_name=full_name, email=email, hashed_password=hash_password(password),
        role=role, department_id=department_id, preferred_language=language, is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def seed_modules_and_categories(db) -> dict[ModuleCode, Module]:
    modules_by_code: dict[ModuleCode, Module] = {}
    for mdata in MODULES_DATA:
        module = db.query(Module).filter(Module.code == mdata["code"]).first()
        if module is None:
            module = Module(
                code=mdata["code"], name_en=mdata["name_en"], name_te=mdata["name_te"],
                name_hi=mdata["name_hi"], icon=mdata["icon"],
            )
            db.add(module)
            db.flush()
        modules_by_code[mdata["code"]] = module

        existing_names = {c.name_en for c in module.categories}
        for name_en, name_te, name_hi, keywords in mdata["categories"]:
            if name_en in existing_names:
                continue
            db.add(Category(module_id=module.id, name_en=name_en, name_te=name_te, name_hi=name_hi, keywords=keywords or None))
        db.flush()
    return modules_by_code


def seed_departments(db, modules_by_code: dict[ModuleCode, Module]) -> dict[ModuleCode, list[Department]]:
    departments_by_module: dict[ModuleCode, list[Department]] = {}
    for module_code, names in DEPARTMENT_NAMES.items():
        depts = []
        for name in names:
            dept = db.query(Department).filter(Department.name == name, Department.module == module_code).first()
            if dept is None:
                dept = Department(
                    name=name, module=module_code,
                    description=f"Handles {module_code.value.replace('_', ' ').title()} complaints — {name}",
                    contact_email=f"{name.lower().replace(' ', '.').replace('&', 'and')}@smartcivicai.gov.in",
                )
                db.add(dept)
                db.flush()
            depts.append(dept)
        departments_by_module[module_code] = depts
    return departments_by_module


def seed_accounts(db, departments_by_module: dict[ModuleCode, list[Department]]):
    admin = get_or_create_user(db, "admin@smartcivicai.gov.in", "SmartCivicAI Admin", UserRole.ADMIN)

    first_school_dept = departments_by_module[ModuleCode.GOVERNMENT_SCHOOLS][0]
    officer = get_or_create_user(
        db, "officer@smartcivicai.gov.in", "Demo Department Officer", UserRole.OFFICER,
        department_id=first_school_dept.id,
    )

    # One extra officer per remaining module so every department has *someone* to assign to
    extra_officers = []
    for module_code, depts in departments_by_module.items():
        for dept in depts:
            email = f"officer.{dept.name.lower().replace(' ', '.').replace('&', 'and')}@smartcivicai.gov.in"
            off = get_or_create_user(db, email, f"Officer — {dept.name}", UserRole.OFFICER, department_id=dept.id)
            extra_officers.append(off)

    citizens = [get_or_create_user(db, email, name, UserRole.CITIZEN) for email, name in DEMO_CITIZENS]

    db.flush()
    return admin, officer, extra_officers, citizens


def _random_datetime_within_last_months(months: int = 4) -> datetime:
    now = datetime.now(timezone.utc)
    delta_days = random.randint(0, months * 30)
    return now - timedelta(days=delta_days, hours=random.randint(0, 23), minutes=random.randint(0, 59))


def seed_complaints(db, modules_by_code, departments_by_module, citizens, officer_pool):
    statuses_cycle = [
        ComplaintStatus.NEW, ComplaintStatus.PENDING, ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS,
        ComplaintStatus.RESOLVED, ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED, ComplaintStatus.ESCALATED,
        ComplaintStatus.REQUIRES_ADMIN_REVIEW,
    ]

    created = 0
    for i in range(60):
        module, lang, category_name, text = SAMPLE_COMPLAINTS[i % len(SAMPLE_COMPLAINTS)]
        module_row = modules_by_code[module]
        category = next((c for c in module_row.categories if c.name_en == category_name), None)
        citizen = random.choice(citizens)

        lat = HYDERABAD_LAT + random.uniform(-0.15, 0.15)
        lng = HYDERABAD_LNG + random.uniform(-0.15, 0.15)

        complaint = Complaint(
            complaint_number=generate_complaint_number(db, module.value),
            citizen_id=citizen.id,
            module=module,
            category_id=category.id if category else None,
            original_language=LanguageCode(lang),
            original_text=text,
            latitude=round(lat, 6),
            longitude=round(lng, 6),
            address="Hyderabad, Telangana (demo location)",
            priority=PriorityLevel.MEDIUM,
            status=ComplaintStatus.NEW,
            is_demo_data=True,
        )
        db.add(complaint)
        db.flush()

        # Run the same AI pipeline used in production submissions, so
        # ai_analysis / ai_classification / ai_priority / ai_routing rows
        # exist and the AI Monitoring dashboard has real data too.
        run_ai_pipeline(db, complaint)

        # Force a spread across every status value for meaningful charts
        # (the pipeline itself only ever lands on PENDING or
        # REQUIRES_ADMIN_REVIEW, which wouldn't populate every graph).
        target_status = statuses_cycle[i % len(statuses_cycle)]
        change_status(db, complaint, target_status, changed_by_id=None, note="Demo seed data")

        if target_status in (ComplaintStatus.ASSIGNED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.RESOLVED, ComplaintStatus.ESCALATED):
            depts = departments_by_module[module]
            complaint.department_id = random.choice(depts).id
            eligible_officers = [o for o in officer_pool if o.department_id == complaint.department_id]
            if eligible_officers:
                complaint.assigned_officer_id = random.choice(eligible_officers).id

        if target_status == ComplaintStatus.RESOLVED:
            complaint.officer_remarks = "Issue verified and resolved on-site. (demo data)"
            if random.random() < 0.6:  # not every resolved complaint has feedback, for realism
                db.add(Feedback(
                    complaint_id=complaint.id, citizen_id=citizen.id,
                    rating=random.choice([3, 4, 4, 5, 5, 5]),
                    comment=random.choice(["Resolved quickly, thank you.", "Took a while but got fixed.", None, "Satisfied with the response."]),
                ))

        # Backdate created_at/updated_at to spread complaints across ~4 months
        # so "Complaints Over Time" charts have a real trend to show.
        backdated = _random_datetime_within_last_months(4)
        complaint.created_at = backdated
        complaint.updated_at = backdated + timedelta(hours=random.randint(1, 72))

        created += 1

    db.flush()
    return created


def main():
    Base.metadata.create_all(bind=engine)  # safety net if Alembic hasn't been run yet in a fresh dev DB

    db = SessionLocal()
    try:
        print("Seeding modules and categories...")
        modules_by_code = seed_modules_and_categories(db)
        db.commit()

        print("Seeding departments...")
        departments_by_module = seed_departments(db, modules_by_code)
        db.commit()

        print("Seeding demo accounts...")
        admin, officer, extra_officers, citizens = seed_accounts(db, departments_by_module)
        db.commit()

        print("Seeding demo complaints (this runs the AI pipeline per complaint, may take a few seconds)...")
        count = seed_complaints(db, modules_by_code, departments_by_module, citizens, [officer, *extra_officers])
        db.commit()

        print(f"\nDone. Created/updated:")
        print(f"  - {len(modules_by_code)} modules")
        print(f"  - {sum(len(d) for d in departments_by_module.values())} departments")
        print(f"  - {len(citizens)} citizen accounts, {1 + len(extra_officers)} officer accounts, 1 admin account")
        print(f"  - {count} DEMO complaints (is_demo_data=True)")
        print("\nDemo login credentials (password for all: Demo@1234):")
        print("  ADMIN    : admin@smartcivicai.gov.in")
        print("  OFFICER  : officer@smartcivicai.gov.in")
        print("  CITIZEN  : citizen@smartcivicai.gov.in")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
