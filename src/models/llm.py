from pydantic import BaseModel, Field

class JobDescriptionLLMResponse(BaseModel):
    summary: str = Field(description="High-level summary of the job role")
    responsibilities: list[str] = Field(description="Key responsibilities and duties of the role")
    requirements: list[str] = Field(description="Must-have technical skills, experience, and qualifications")
    nice_to_have: list[str] = Field(description="Good-to-have skills or experiences")
    experience_required: str = Field(description="Minimum and preferred years of experience required")
    education: str = Field(description="Minimum and preferred educational qualifications")

class ResumeParserLLMResponse(BaseModel):
    name: str = Field(default="", description="Full name of the candidate")
    email: str = Field(default="", description="Email address of the candidate")
    phone: str = Field(default="", description="Phone number of the candidate")
    skills: list[str] = Field(default_factory=list, description="Extracted skills and technologies")
    experience: int = Field(default=0, description="Total years of professional experience (as integer)")
    education: str = Field(default="", description="Education history or degrees details")
    projects: list[str] = Field(default_factory=list, description="Brief summaries of projects or key accomplishments")
    summary: str = Field(default="", description="A short summary of the candidate's profile")

class CandidateMatchingLLMResponse(BaseModel):
    score: int = Field(description="Match percentage/score between 0 and 100")
    decision: str = Field(description="Recommended decision: 'shortlisted' or 'rejected'")
    strengths: list[str] = Field(description="Key strengths of the candidate matching the job description")
    weaknesses: list[str] = Field(description="Gaps or weaknesses identified in the candidate profile relative to the job description")
    reason: str = Field(description="Detailed reason for the recommendation")