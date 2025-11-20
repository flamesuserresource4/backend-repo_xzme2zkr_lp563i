"""
Database Schemas

LearnHub: A digital marketplace for student-made study materials and peer tutoring
Each Pydantic model maps to a MongoDB collection with the lowercase class name.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

# Users can be added later if needed

class Material(BaseModel):
    """
    Student-made academic materials for sale or free download
    Collection: "material"
    """
    title: str = Field(..., description="Material title")
    description: Optional[str] = Field(None, description="Short description")
    course: Literal[
        "Information Technology",
        "Electrical Engineering",
        "Civil Engineering",
        "Business Administration",
        "Education",
        "Nursing",
        "Accountancy",
        "Hospitality Management",
    ] = Field(..., description="Course/Program category")
    subject: str = Field(..., description="Subject name, e.g., Data Structures")
    type: Literal["Reviewer", "Class Notes", "Handout", "Problem Set", "Cheat Sheet"] = Field(
        ..., description="Type of material"
    )
    price: float = Field(0, ge=0, description="Price in PHP; 0 for free")
    author_name: str = Field(..., description="Name of the student author")
    university: str = Field("Pamantasan ng Lungsod ng Valenzuela", description="Institution")
    file_url: Optional[str] = Field(None, description="Link to file storage (placeholder/demo)")
    rating: Optional[float] = Field(4.8, ge=0, le=5, description="Average rating")
    downloads: Optional[int] = Field(0, ge=0, description="Download count")


class Tutor(BaseModel):
    """
    Peer tutors available for one-on-one or group sessions
    Collection: "tutor"
    """
    name: str
    course: Literal[
        "Information Technology",
        "Electrical Engineering",
        "Civil Engineering",
        "Business Administration",
        "Education",
        "Nursing",
        "Accountancy",
        "Hospitality Management",
    ]
    subjects: List[str] = Field(default_factory=list, description="Subjects tutored")
    rate_per_hour: float = Field(..., ge=0, description="Hourly rate in PHP")
    modes: List[Literal["One-on-One", "Group"]] = Field(default_factory=lambda: ["One-on-One"]) 
    bio: Optional[str] = None
    availability: Optional[List[str]] = Field(
        default_factory=list, description="Simple list of available timeslots (e.g., Wed 7-9pm)"
    )
    rating: Optional[float] = Field(4.9, ge=0, le=5)


class Booking(BaseModel):
    """
    Tutoring session bookings
    Collection: "booking"
    """
    tutor_id: str = Field(..., description="Mongo _id of tutor as string")
    student_name: str
    student_email: str
    mode: Literal["One-on-One", "Group"]
    session_datetime: str = Field(..., description="ISO or human-readable for demo")
    duration_hours: float = Field(1.0, gt=0)
    group_size: Optional[int] = Field(None, ge=2, description="If group session")
    notes: Optional[str] = None
    status: Literal["pending", "confirmed", "cancelled"] = Field("pending")
