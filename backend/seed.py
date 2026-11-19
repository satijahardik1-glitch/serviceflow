"""Populate ServiceFlow with sample data. Run after `alembic upgrade head`.

    python seed.py          # seed (skips if data already exists)
    python seed.py --reset  # wipe all rows first, then seed
"""
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from app.core.config import settings
from app.core.crypto import encrypt
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal
from app.models import (
    Booking, DiagnosisRule, Review, SavedTechnician, ServiceCategory, TechnicianProfile, User,
    technician_categories,
)
from app.services.ratings import recompute_rating

CATEGORIES = [
    ("Electrical", "electrical", "Wiring, switches, fans, lighting and power faults", "⚡"),
    ("Plumbing", "plumbing", "Leaks, blockages, taps, toilets and water heaters", "🔧"),
    ("AC Repair", "ac-repair", "Air-conditioner cooling, servicing and gas refill", "❄️"),
    ("Carpentry", "carpentry", "Doors, furniture, cabinets and woodwork repair", "🪚"),
]

# (category slug, symptom chip, keywords, diagnosis, min ₹, max ₹, minutes, priority, is_default)
RULES = [
    ("electrical", "Tripping breaker / power cut", "trip,tripping,breaker,mcb,fuse,power cut,no power,blackout,overload", "Overloaded circuit or faulty MCB/breaker", 400, 1200, 60, 3, False),
    ("electrical", "Flickering lights", "flicker,flickering,dim,blinking,loose bulb,holder", "Loose wiring or failing light fixture", 300, 900, 45, 1, False),
    ("electrical", "Sparks or burning smell", "spark,sparking,burning smell,burnt,shock,hot socket,smoke", "Damaged socket or overheated wiring (safety-critical)", 500, 1800, 90, 9, False),
    ("electrical", "Fan not working", "fan,ceiling fan,capacitor,slow fan,noisy fan,regulator", "Faulty fan capacitor or motor", 300, 800, 45, 1, False),
    ("electrical", "Switch or socket not working", "switch,socket,plug point,loose switch,board,not working switch", "Worn switch or socket needing replacement", 200, 600, 30, 0, False),
    ("electrical", "Other electrical issue", "", "General electrical fault - needs on-site inspection", 300, 1000, 60, 0, True),
    ("plumbing", "Leaking tap or pipe", "leak,leaking,drip,dripping,tap,pipe burst,seepage,washer", "Worn washer or damaged pipe joint", 300, 1000, 45, 3, False),
    ("plumbing", "Clogged drain", "clog,clogged,blocked,drain,choke,choked,slow drain,overflow,sink", "Drain or pipe blockage", 400, 1500, 60, 2, False),
    ("plumbing", "Low water pressure", "low pressure,weak flow,pressure,trickle,aerator", "Scaling in pipes/aerator or a partly closed valve", 400, 1200, 60, 0, False),
    ("plumbing", "Toilet or flush problem", "toilet,flush,cistern,commode,running toilet,wc", "Faulty flush mechanism or cistern valve", 350, 1100, 45, 1, False),
    ("plumbing", "Geyser not heating", "geyser,water heater,no hot water,not heating,heating element", "Failed heating element or thermostat", 500, 1800, 75, 1, False),
    ("plumbing", "Other plumbing issue", "", "General plumbing fault - needs on-site inspection", 300, 1000, 60, 0, True),
    ("ac-repair", "Not cooling", "not cooling,warm air,no cooling,weak cooling,hot air,cooling", "Low refrigerant or dirty filters/coil", 600, 2500, 90, 2, False),
    ("ac-repair", "Water leaking from indoor unit", "water leak,dripping,drain pipe,leaking ac,water dripping,leaking", "Clogged condensate drain line", 400, 1200, 60, 2, False),
    ("ac-repair", "Strange noise", "noise,noisy,rattling,grinding,vibration,buzzing,loud", "Loose parts or failing fan motor/compressor", 500, 2000, 75, 1, False),
    ("ac-repair", "Not turning on", "not turning on,won't start,wont start,dead,no power,remote,not starting,tripping", "Electrical/PCB or capacitor fault", 500, 2200, 75, 1, False),
    ("ac-repair", "Routine service / gas refill", "gas,refill,service,cleaning,servicing,maintenance,filter", "Routine servicing and gas top-up", 500, 1800, 90, 0, False),
    ("ac-repair", "Other AC issue", "", "General AC fault - needs on-site inspection", 500, 1500, 60, 0, True),
    ("carpentry", "Door won't close / hinge issue", "door,hinge,jammed,stuck,misaligned,won't close,wont close,lock,latch", "Misaligned door or loose hinges", 300, 900, 45, 1, False),
    ("carpentry", "Broken or wobbly furniture", "broken,chair,table,wobbly,wobble,crack,cracked,bed,sofa", "Joint failure or damaged furniture frame", 400, 1500, 75, 1, False),
    ("carpentry", "Cabinet / wardrobe / drawer", "wardrobe,cabinet,drawer,shelf,shelves,kitchen cabinet,channel,hinges", "Faulty drawer channel or cabinet fitting", 400, 1600, 90, 0, False),
    ("carpentry", "Termite or wood damage", "termite,rot,wood damage,swollen,moisture,warped,pest", "Termite or moisture damage to woodwork", 800, 3500, 150, 5, False),
    ("carpentry", "Assembly or installation", "install,assembly,assemble,mount,fit,new,curtain rod", "Furniture assembly or fixture installation", 300, 1200, 60, 0, False),
    ("carpentry", "Other carpentry work", "", "General carpentry work - needs on-site inspection", 300, 1200, 60, 0, True),
]

# name, email, phone, city, categories, base_rate, years, bio, status, available, id_doc
TECHNICIANS = [
    ("Rajesh Kumar", "rajesh@serviceflow.com", "9810000001", "Jalandhar", ["electrical"], 350, 12,
     "Licensed electrician with 12 years of experience in residential wiring, MCB panels and fan repair.", "verified", True, ("Aadhaar", "XXXX-XXXX-1201")),
    ("Amandeep Singh", "amandeep@serviceflow.com", "9810000002", "Jalandhar", ["plumbing"], 300, 8,
     "Plumber specialising in leak detection, bathroom fittings and geyser installation.", "verified", True, ("Aadhaar", "XXXX-XXXX-1202")),
    ("Harpreet Sharma", "harpreet@serviceflow.com", "9810000003", "Ludhiana", ["ac-repair", "electrical"], 500, 10,
     "HVAC technician for split and window ACs. Gas refill, PCB repair and annual maintenance contracts.", "verified", True, ("Driving Licence", "PB10-2014-5521")),
    ("Gurpreet Gill", "gurpreet@serviceflow.com", "9810000004", "Jalandhar", ["carpentry"], 400, 15,
     "Master carpenter - modular wardrobes, door fitting, furniture repair and polishing.", "verified", False, ("Aadhaar", "XXXX-XXXX-1204")),
    ("Manpreet Kaur", "manpreet@serviceflow.com", "9810000005", "Patiala", ["plumbing", "carpentry"], 320, 5,
     "Handy all-rounder for plumbing fixes and light carpentry work.", "verified", True, ("Voter ID", "XYZ1234567")),
    ("Sandeep Verma", "sandeep@serviceflow.com", "9810000006", "Jalandhar", ["ac-repair"], 450, 3,
     "Newly joined AC technician - awaiting verification.", "pending", True, ("Aadhaar", "XXXX-XXXX-1206")),
    ("Vikram Chauhan", "vikram@serviceflow.com", "9810000007", "Chandigarh", ["electrical"], 300, 2,
     "Electrician - ID submission was incomplete.", "rejected", True, ("PAN", "ABCDE1234F")),
]

CUSTOMERS = [
    ("Neha Arora", "neha@example.com", "9820000001", "Jalandhar"),
    ("Arjun Mehta", "arjun@example.com", "9820000002", "Ludhiana"),
]

REVIEWS = {  # technician email -> [(rating, comment)]
    "rajesh@serviceflow.com": [(5, "Fixed the tripping MCB in under an hour. Very professional."), (4, "On time and fair price."), (5, "Explained the fault clearly before starting.")],
    "amandeep@serviceflow.com": [(5, "Found a hidden leak other plumbers missed."), (4, "Neat work, cleaned up afterwards.")],
    "harpreet@serviceflow.com": [(5, "AC cooling like new after the gas refill."), (5, "Honest diagnosis, no unnecessary parts replaced."), (4, "Good service, slightly late.")],
    "gurpreet@serviceflow.com": [(5, "Wardrobe fitting was flawless.")],
}


def main(reset: bool) -> None:
    if settings.is_production:
        sys.exit("Refusing to seed sample data with default passwords in production. Use create_admin.py instead.")
    db = SessionLocal()
    try:
        if reset:
            for model in (SavedTechnician, Review, Booking):
                db.execute(delete(model))
            db.execute(delete(technician_categories))
            for model in (TechnicianProfile, DiagnosisRule, ServiceCategory, User):
                db.execute(delete(model))
            db.commit()
        if db.scalar(select(User.id).limit(1)) is not None:
            print("Database already contains data - run `python seed.py --reset` to start over.")
            return

        cats = {}
        for name, slug, desc, icon in CATEGORIES:
            cats[slug] = ServiceCategory(name=name, slug=slug, description=desc, icon=icon)
            db.add(cats[slug])
        db.flush()
        for slug, symptom, kw, diag, lo, hi, mins, prio, default in RULES:
            db.add(DiagnosisRule(category_id=cats[slug].id, symptom=symptom, keywords=kw, diagnosis=diag,
                                 min_price=lo, max_price=hi, estimated_minutes=mins, priority=prio, is_default=default))

        db.add(User(name="Platform Admin", email="admin@serviceflow.com", hashed_password=hash_password("Admin@123"),
                    role="admin", city="Jalandhar"))
        customers = []
        for name, email, phone, city in CUSTOMERS:
            u = User(name=name, email=email, hashed_password=hash_password("Customer@123"), role="customer", phone=phone, city=city)
            db.add(u)
            customers.append(u)
        techs = {}
        for name, email, phone, city, slugs, rate, years, bio, status, avail, (doc_type, doc_no) in TECHNICIANS:
            u = User(name=name, email=email, hashed_password=hash_password("Tech@1234"), role="technician", phone=phone, city=city)
            db.add(u)
            db.flush()
            p = TechnicianProfile(
                user_id=u.id, bio=bio, city=city, base_rate=rate, experience_years=years, is_available=avail,
                verification_status=status, id_document_type=doc_type, id_document_number=encrypt(doc_no),
                verification_note="ID photo unreadable - please resubmit." if status == "rejected" else None,
                categories=[cats[s] for s in slugs])
            db.add(p)
            techs[email] = p
        db.flush()

        # completed bookings + reviews so ratings are derived from real data
        past = datetime.now(timezone.utc) - timedelta(days=10)
        for email, items in REVIEWS.items():
            tech = techs[email]
            cat = tech.categories[0]
            rule = next(r for r in RULES if r[0] == cat.slug and not r[8])
            for i, (rating, comment) in enumerate(items):
                cust = customers[i % len(customers)]
                booking = Booking(
                    customer_id=cust.id, technician_id=tech.id, category_id=cat.id,
                    problem_description=f"Sample completed job: {rule[1]}", diagnosis=rule[3],
                    estimated_min_price=rule[4], estimated_max_price=rule[5], estimated_minutes=rule[6],
                    address="Model Town, Main Market", city=cust.city or tech.city,
                    scheduled_at=past - timedelta(days=i * 3), status="completed")
                db.add(booking)
                db.flush()
                db.add(Review(booking_id=booking.id, customer_id=cust.id, technician_id=tech.id, rating=rating, comment=comment))
            db.flush()
            recompute_rating(db, tech.id)

        # a pending request and a trusted-list entry for the first customer
        rajesh = techs["rajesh@serviceflow.com"]
        db.add(Booking(
            customer_id=customers[0].id, technician_id=rajesh.id, category_id=cats["electrical"].id,
            problem_description="Breaker keeps tripping when the AC and microwave run together.",
            diagnosis="Overloaded circuit or faulty MCB/breaker", estimated_min_price=400, estimated_max_price=1200,
            estimated_minutes=60, address="House 14, Model Town", city="Jalandhar",
            scheduled_at=datetime.now(timezone.utc) + timedelta(days=2), status="pending"))
        db.add(SavedTechnician(customer_id=customers[0].id, technician_id=rajesh.id))
        db.commit()
        print("Seeded successfully.\n"
              "  Admin:      admin@serviceflow.com / Admin@123\n"
              "  Customers:  neha@example.com, arjun@example.com / Customer@123\n"
              "  Technicians: rajesh@, amandeep@, harpreet@, gurpreet@, manpreet@ (verified), sandeep@ (pending),\n"
              "               vikram@ (rejected) @serviceflow.com / Tech@1234")
    finally:
        db.close()


if __name__ == "__main__":
    main(reset="--reset" in sys.argv)
