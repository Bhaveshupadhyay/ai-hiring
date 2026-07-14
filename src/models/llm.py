from pydantic import BaseModel, Field, AliasChoices

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
    experience: int = Field(
        default=0, 
        description="Total years of professional experience (as integer)",
        validation_alias=AliasChoices("experience", "total_experience", "years_of_experience")
    )
    education: str = Field(default="", description="Education history or degrees details")
    projects: list[str] = Field(default_factory=list, description="Brief summaries of projects or key accomplishments")
    summary: str = Field(
        default="", 
        description="A short summary of the candidate's profile",
        validation_alias=AliasChoices("summary", "professional_summary", "profile_summary")
    )

class CandidateMatchingLLMResponse(BaseModel):
    score: int = Field(
        description="Match percentage/score between 0 and 100",
        validation_alias=AliasChoices("score", "match_score", "match_percentage")
    )
    decision: str = Field(
        description="Recommended decision: 'shortlisted' or 'rejected'",
        validation_alias=AliasChoices("decision", "recommended_decision", "recommendation")
    )
    strengths: list[str] = Field(
        description="Key strengths of the candidate matching the job description",
        validation_alias=AliasChoices("strengths", "key_strengths")
    )
    weaknesses: list[str] = Field(
        description="Gaps or weaknesses identified in the candidate profile relative to the job description",
        validation_alias=AliasChoices("weaknesses", "gaps", "key_weaknesses")
    )
    reason: str = Field(
        description="Detailed reason for the recommendation",
        validation_alias=AliasChoices("reason", "detailed_reason", "rationale")
    )