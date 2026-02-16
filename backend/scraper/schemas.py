from pydantic import BaseModel

class JobListing(BaseModel):
    title: str
    company: str
    location: str | None
    description: str
    url: str
