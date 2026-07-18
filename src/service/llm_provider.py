import json
from abc import ABC, abstractmethod
from typing import Any, cast
from google import genai
from google.genai import types
from core.config import config
from groq import AsyncGroq
from models.llm import (
    JobDescriptionLLMResponse,
    ResumeParserLLMResponse,
    CandidateMatchingLLMResponse
)

class LLmProvider(ABC):
    @abstractmethod
    async def generate_job_description(self, title: str) -> JobDescriptionLLMResponse:
        pass

    @abstractmethod
    async def parse_resume(self, extracted_text: str) -> ResumeParserLLMResponse:
        pass

    @abstractmethod
    async def match_resume(self, job_data: dict, resume_data: dict) -> CandidateMatchingLLMResponse:
        pass


class GeminiLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "gemini-3.1-flash-lite"):
        # Initialize Google GenAI client
        # google-genai client automatically picks up GEMINI_API_KEY from environment,
        # but if we have it in config.GEMINI_API_KEY we can pass it or check.
        api_key = config.GEMINI_API_KEY or None
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = genai.Client()
        self.model_name = model_name

    async def generate_job_description(self, title: str) -> JobDescriptionLLMResponse:
        prompt = f"Generate a comprehensive, professional job description for the job title: '{title}'."
        
        system_instruction = (
            "You are a professional HR assistant. Generate a hiring post structured as JSON containing: "
            "title, summary, responsibilities (list of strings), requirements (list of strings), nice_to_have (list of strings), "
            "experience_required (string), and education (string). "
            "Return valid JSON only matching the schema. No markdown. "
            "The title should be short and concise (e.g., 'SDE 1 Backend') and should not mention all the requirements or details."
        )

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JobDescriptionLLMResponse,
            system_instruction=system_instruction,
            temperature=0.7,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[prompt],
            config=gen_config
        )

        # Parse response using Pydantic
        text = response.text or ""
        return JobDescriptionLLMResponse.model_validate_json(text)

    async def parse_resume(self, extracted_text: str) -> ResumeParserLLMResponse:
        prompt = f"Here is the raw text extracted from a resume PDF:\n\n{extracted_text}"
        
        system_instruction = (
            "You are an expert ATS (Applicant Tracking System) parser. "
            "Extract candidate information: name, email, phone, skills (list of strings), "
            "experience (total years as an integer), education (string), projects (list of strings), "
            "and a professional summary. "
            "Return valid JSON only matching the schema. No markdown."
        )

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResumeParserLLMResponse,
            system_instruction=system_instruction,
            temperature=0.1,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[prompt],
            config=gen_config
        )

        text = response.text or ""
        return ResumeParserLLMResponse.model_validate_json(text)

    async def match_resume(self, job_data: dict, resume_data: dict) -> CandidateMatchingLLMResponse:
        prompt = (
            f"Compare the candidate's resume details against the job description:\n\n"
            f"--- JOB DESCRIPTION ---\n{job_data}\n\n"
            f"--- CANDIDATE RESUME ANALYSIS ---\n{resume_data}\n\n"
            f"Assess the fit of the candidate for this role."
        )

        system_instruction = (
            "You are an expert recruitment matcher. Compare the resume details with the job description. "
            "Return a match score (0-100), recommended decision ('shortlisted' or 'rejected'), "
            "strengths (list of matching skills/experience), weaknesses (list of gaps), and a detailed reason. "
            "Return valid JSON only matching the schema. No markdown."
        )

        gen_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateMatchingLLMResponse,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=[prompt],
            config=gen_config
        )

        text = response.text or ""
        return CandidateMatchingLLMResponse.model_validate_json(text)


class GroqLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        api_key = config.GROQ_API_KEY or None
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = model_name

    async def generate_job_description(self, title: str) -> JobDescriptionLLMResponse:
        prompt = f"Generate a comprehensive, professional job description for the job title: '{title}'."

        # 1. Get the schema
        schema = JobDescriptionLLMResponse.model_json_schema()

        # 2. Inject it into the prompt
        system_instruction = (
            "You are a professional HR assistant. Generate a hiring post structured as JSON containing: "
            "title, summary, responsibilities (list of strings), requirements (list of strings), nice_to_have (list of strings), "
            "experience_required (string), and education (string). "
            "Return valid JSON only. No markdown.\n\n"
            "The title should be short and concise (e.g., 'SDE 1 Backend') and should not mention all the requirements or details.\n\n"
            f"You MUST exactly match this JSON schema:\n{json.dumps(schema, indent=2)}"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        chat_completion = await self.client.chat.completions.create(
            messages=cast(Any, messages),
            model=self.model_name,
            # 3. Use the universally supported json_object
            response_format=cast(Any, {"type": "json_object"}),
            temperature=0.7
        )

        text = chat_completion.choices[0].message.content or "{}"
        return JobDescriptionLLMResponse.model_validate_json(text)

    async def parse_resume(self, extracted_text: str) -> ResumeParserLLMResponse:
        prompt = f"Here is the raw text extracted from a resume PDF:\n\n{extracted_text}"

        schema = ResumeParserLLMResponse.model_json_schema()

        system_instruction = (
            "You are an expert ATS (Applicant Tracking System) parser. "
            "Extract candidate information: name, email, phone, skills (list of strings), "
            "experience (total years as an integer), education (string), projects (list of strings), "
            "and a professional summary. "
            "Return valid JSON only. No markdown.\n\n"
            f"You MUST exactly match this JSON schema:\n{json.dumps(schema, indent=2)}"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        chat_completion = await self.client.chat.completions.create(
            messages=cast(Any, messages),
            model=self.model_name,
            response_format=cast(Any, {"type": "json_object"}),
            temperature=0.1
        )

        text = chat_completion.choices[0].message.content or "{}"
        return ResumeParserLLMResponse.model_validate_json(text)

    async def match_resume(self, job_data: dict, resume_data: dict) -> CandidateMatchingLLMResponse:
        prompt = (
            f"Compare the candidate's resume details against the job description:\n\n"
            f"--- JOB DESCRIPTION ---\n{job_data}\n\n"
            f"--- CANDIDATE RESUME ANALYSIS ---\n{resume_data}\n\n"
            f"Assess the fit of the candidate for this role."
        )

        schema = CandidateMatchingLLMResponse.model_json_schema()

        system_instruction = (
            "You are an expert recruitment matcher. Compare the resume details with the job description. "
            "Return a match score (0-100), recommended decision ('shortlisted' or 'rejected'), "
            "strengths (list of matching skills/experience), weaknesses (list of gaps), and a detailed reason. "
            "Return valid JSON only. No markdown.\n\n"
            f"You MUST exactly match this JSON schema:\n{json.dumps(schema, indent=2)}"
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        chat_completion = await self.client.chat.completions.create(
            messages=cast(Any, messages),
            model=self.model_name,
            response_format=cast(Any, {"type": "json_object"}),
            temperature=0.2
        )

        text = chat_completion.choices[0].message.content or "{}"
        return CandidateMatchingLLMResponse.model_validate_json(text)


class FallbackLLmProvider(LLmProvider):
    def __init__(self, primary: LLmProvider, backup: LLmProvider):
        self.primary = primary
        self.backup = backup

    async def generate_job_description(self, title: str) -> JobDescriptionLLMResponse:
        try:
            return await self.primary.generate_job_description(title)
        except Exception as e:
            return await self.backup.generate_job_description(title)

    async def parse_resume(self, extracted_text: str) -> ResumeParserLLMResponse:
        try:
            return await self.primary.parse_resume(extracted_text)
        except Exception as e:
            return await self.backup.parse_resume(extracted_text)

    async def match_resume(self, job_data: dict, resume_data: dict) -> CandidateMatchingLLMResponse:
        try:
            return await self.primary.match_resume(job_data, resume_data)
        except Exception as e:
            return await self.backup.match_resume(job_data, resume_data)