import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Material, Tutor, Booking

app = FastAPI(title="LearnHub API", description="Marketplace for study materials and peer tutoring (PLV)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"name": "LearnHub", "message": "Backend running", "university": "Pamantasan ng Lungsod ng Valenzuela"}


# Helper: convert Mongo docs to serializable dicts

def serialize_doc(doc):
    if not doc:
        return doc
    d = dict(doc)
    _id = d.get("_id")
    if isinstance(_id, ObjectId):
        d["id"] = str(_id)
        del d["_id"]
    return d


# Seed minimal demo data if collections empty
@app.on_event("startup")
async def seed_demo():
    try:
        if db is None:
            return
        if db["material"].count_documents({}) == 0:
            demo_materials = [
                {
                    "title": "Data Structures Reviewer",
                    "description": "Key concepts + sample problems",
                    "course": "Information Technology",
                    "subject": "Data Structures",
                    "type": "Reviewer",
                    "price": 50,
                    "author_name": "Alex Cruz",
                    "university": "Pamantasan ng Lungsod ng Valenzuela",
                    "file_url": None,
                    "rating": 4.9,
                    "downloads": 120,
                },
                {
                    "title": "Circuit Analysis Handout",
                    "description": "Ohm's law to Thevenin",
                    "course": "Electrical Engineering",
                    "subject": "Circuit Analysis",
                    "type": "Handout",
                    "price": 0,
                    "author_name": "J. Dizon",
                    "university": "Pamantasan ng Lungsod ng Valenzuela",
                    "file_url": None,
                    "rating": 4.7,
                    "downloads": 88,
                },
            ]
            for m in demo_materials:
                db["material"].insert_one(m)
        if db["tutor"].count_documents({}) == 0:
            demo_tutors = [
                {
                    "name": "Maria Santos",
                    "course": "Information Technology",
                    "subjects": ["Programming 1", "Data Structures"],
                    "rate_per_hour": 200,
                    "modes": ["One-on-One", "Group"],
                    "bio": "3rd year IT student, dean's lister",
                    "availability": ["Mon 7-9pm", "Wed 8-10pm"],
                    "rating": 4.9,
                },
                {
                    "name": "Mark Reyes",
                    "course": "Civil Engineering",
                    "subjects": ["Statics", "Strength of Materials"],
                    "rate_per_hour": 250,
                    "modes": ["One-on-One"],
                    "bio": "Board topnotcher reviewee",
                    "availability": ["Sat 2-5pm"],
                    "rating": 4.8,
                },
            ]
            for t in demo_tutors:
                db["tutor"].insert_one(t)
    except Exception:
        # fail silently if DB missing
        pass


# Materials endpoints
@app.get("/api/materials")
def list_materials(course: Optional[str] = None, subject: Optional[str] = None, q: Optional[str] = None):
    flt = {}
    if course:
        flt["course"] = course
    if subject:
        flt["subject"] = subject
    docs = get_documents("material", flt)
    items = [serialize_doc(d) for d in docs]
    if q:
        ql = q.lower()
        items = [i for i in items if ql in i.get("title", "").lower() or ql in (i.get("description") or "").lower()]
    return {"items": items}


class CreateMaterial(BaseModel):
    data: Material


@app.post("/api/materials")
def create_material(payload: CreateMaterial):
    inserted_id = create_document("material", payload.data)
    return {"id": inserted_id}


# Tutors endpoints
@app.get("/api/tutors")
def list_tutors(course: Optional[str] = None, subject: Optional[str] = None):
    flt = {}
    if course:
        flt["course"] = course
    docs = get_documents("tutor", flt)
    items = [serialize_doc(d) for d in docs]
    if subject:
        sl = subject.lower()
        items = [i for i in items if any(sl in s.lower() for s in i.get("subjects", []))]
    return {"items": items}


class CreateTutor(BaseModel):
    data: Tutor


@app.post("/api/tutors")
def create_tutor(payload: CreateTutor):
    inserted_id = create_document("tutor", payload.data)
    return {"id": inserted_id}


# Bookings
class CreateBooking(BaseModel):
    data: Booking


@app.post("/api/bookings")
def create_booking(payload: CreateBooking):
    # basic sanity: ensure tutor exists
    try:
        tid = ObjectId(payload.data.tutor_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid tutor_id")
    tutor = db["tutor"].find_one({"_id": tid}) if db else None
    if not tutor:
        raise HTTPException(status_code=404, detail="Tutor not found")
    inserted_id = create_document("booking", payload.data)
    return {"id": inserted_id, "status": "pending"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from LearnHub backend!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = getattr(db, "name", "✅ Connected")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
