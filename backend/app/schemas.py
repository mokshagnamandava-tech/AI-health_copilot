from pydantic import BaseModel, Field

class RecordCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    type: str = Field(default="Other medical record", max_length=80)
    date: str = Field(default="", max_length=30)
    language: str = Field(default="Unknown", max_length=40)
    text: str = Field(default="", max_length=100000)
    summary: str = Field(default="", max_length=20000)
