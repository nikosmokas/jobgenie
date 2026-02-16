from pydantic import BaseModel, EmailStr
from typing import List, Optional

class CVProfile(BaseModel):
    name: Optional[str]
    email: Optional[EmailStr]
    location: Optional[str]
    skills: List[str] = []
    experience_years: Optional[int]
    education: List[str] = []
