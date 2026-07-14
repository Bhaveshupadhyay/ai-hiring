import logging
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

logger = logging.getLogger(__name__)

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
    def __init__(self, model_name: str = "gemini-3.5-flash"):
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
            "summary, responsibilities (list of strings), requirements (list of strings), nice_to_have (list of strings), "
            "experience_required (string), and education (string). "
            "Return valid JSON only matching the schema. No markdown."
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
        logger.info(f"Gemini generate_job_description response: {text}")
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
        logger.info(f"Gemini parse_resume response: {text}")
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
        logger.info(f"Gemini match_resume response: {text}")
        return CandidateMatchingLLMResponse.model_validate_json(text)


class GroqLLmProvider(LLmProvider):
    def __init__(self, model_name: str = "openai/gpt-oss-20b"):
        api_key = config.GROQ_API_KEY or None
        self.client = AsyncGroq(api_key=api_key)
        self.model_name = model_name

    async def generate_job_description(self, title: str) -> JobDescriptionLLMResponse:
        prompt = f"Generate a comprehensive, professional job description for the job title: '{title}'."
        
        system_instruction = (
            "You are a professional HR assistant. Generate a hiring post structured as JSON containing: "
            "summary, responsibilities (list of strings), requirements (list of strings), nice_to_have (list of strings), "
            "experience_required (string), and education (string). "
            "Return valid JSON only matching the schema. No markdown."
        )

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ]

        chat_completion = await self.client.chat.completions.create(
            messages=cast(Any, messages),
            model=self.model_name,
            response_format=cast(Any, {"type": "json_object"}),
            temperature=0.7
        )

        text = chat_completion.choices[0].message.content or ""
        logger.info(f"Groq generate_job_description response: {text}")
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

        text = chat_completion.choices[0].message.content or ""
        logger.info(f"Groq parse_resume response: {text}")
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

        text = chat_completion.choices[0].message.content or ""
        logger.info(f"Groq match_resume response: {text}")
        return CandidateMatchingLLMResponse.model_validate_json(text)