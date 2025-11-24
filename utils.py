"""Utilities for PDF parsing, model setup, and LLM-powered analysis."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from PyPDF2 import PdfReader

import prompts


class Publication(BaseModel):
    """Key publication details."""

    title: str = Field(default="N/A")
    journal: str = Field(default="N/A")
    year: Optional[int] = Field(default=None)


class Grant(BaseModel):
    """Grant or funding record."""

    title: str = Field(default="N/A")
    amount: Optional[str] = Field(default=None)
    year: Optional[int] = Field(default=None)
    sponsor: Optional[str] = Field(default=None)


class CVProfile(BaseModel):
    """Structured representation of a parsed CV."""

    name: str = Field(default="Unknown")
    current_institution: str = Field(default="N/A")
    estimated_ranking: str = Field(default="N/A")
    h_index: Optional[str] = Field(default=None)
    research_focus_keywords: List[str] = Field(default_factory=list)
    key_publications: List[Publication] = Field(default_factory=list)
    grants: List[Grant] = Field(default_factory=list)
    notes: str = Field(default="")


@dataclass
class ModelConfig:
    provider: str
    model: str
    api_key: str


def demo_profile() -> CVProfile:
    """Return a pre-filled profile for quick UI demo without uploading a PDF."""

    return CVProfile(
        name="Dr. Ada Zhang",
        current_institution="Tsinghua University",
        estimated_ranking="Top 20 globally",
        h_index="42",
        research_focus_keywords=["Immunology", "T cell", "Tumor microenvironment", "Single-cell"],
        key_publications=[
            Publication(title="Checkpoint modulation in solid tumors", journal="Nature", year=2023),
            Publication(title="Single-cell atlas of immune niches", journal="Science", year=2022),
        ],
        grants=[
            Grant(title="NSFC Excellent Young Scientist", amount="$500K", year=2021, sponsor="NSFC"),
            Grant(title="Translational immunotherapy consortium", amount="$1.2M", year=2023, sponsor="Industry"),
        ],
        notes="示例数据：可直接用于体验匹配与邮件生成。",
    )


def load_pdf_text(file) -> str:
    """Extract raw text from an uploaded PDF file-like object."""

    try:
        reader = PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except Exception as exc:  # pragma: no cover - defensive UI surface
        raise ValueError(f"Failed to parse PDF: {exc}")


def heuristic_extract(text: str) -> CVProfile:
    """Lightweight heuristic extraction without LLM calls."""

    h_index_match = re.search(r"H-?Index[:\s]+(\d+)", text, flags=re.IGNORECASE)
    keywords = list({word.strip() for word in re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", text)})[:10]
    publications = []
    for journal in ["Nature", "Science", "Cell", "Lancet"]:
        if re.search(journal, text, re.IGNORECASE):
            publications.append(Publication(title=f"Highlight from {journal}", journal=journal))

    return CVProfile(
        h_index=h_index_match.group(1) if h_index_match else None,
        research_focus_keywords=keywords,
        key_publications=publications,
        notes="Heuristic extraction; refine with LLM for richer details.",
    )


def get_llm(config: ModelConfig):
    """Instantiate a chat model based on provider selection."""

    if config.provider == "openai":
        return ChatOpenAI(api_key=config.api_key, model=config.model, temperature=0.2)
    if config.provider == "anthropic":
        return ChatAnthropic(api_key=config.api_key, model=config.model, temperature=0.2)
    raise ValueError("Unsupported provider. Choose 'openai' or 'anthropic'.")


def llm_structured_parse(text: str, config: ModelConfig) -> CVProfile:
    """Use the LLM to create a structured CV profile."""

    llm = get_llm(config)
    messages = [
        SystemMessage(content=prompts.parsing_prompt()),
        HumanMessage(content=text[:12000]),
    ]
    response = llm.invoke(messages)
    try:
        parsed = json.loads(response.content)
        return CVProfile(**parsed)
    except Exception:
        # fall back to heuristic merge
        base = heuristic_extract(text)
        base.notes += " | LLM parsing failed to return valid JSON."
        return base


def build_candidate_table(profiles: Dict[str, CVProfile]) -> pd.DataFrame:
    """Convert candidate profiles into a DataFrame for UI display."""

    rows = []
    for name, profile in profiles.items():
        rows.append(
            {
                "Name": name,
                "Institution": profile.current_institution,
                "H-Index": profile.h_index,
                "Focus": ", ".join(profile.research_focus_keywords),
                "Publications": ", ".join(pub.journal for pub in profile.key_publications),
            }
        )
    return pd.DataFrame(rows)


def generate_match_report(profile: CVProfile, target: str, config: ModelConfig) -> Dict:
    """Produce a suitability analysis JSON using the LLM."""

    llm = get_llm(config)
    cv_summary = profile.json(indent=2)
    prompt = prompts.matching_prompt(cv_summary=cv_summary, target_direction=target)
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    try:
        return json.loads(response.content)
    except Exception:
        return {
            "suitability_score": "N/A",
            "reasoning": response.content,
            "strengths": [],
            "gaps": [],
            "recommended_projects": [],
        }


def generate_outreach(profile: CVProfile, institute_value: str, language: str, config: ModelConfig) -> str:
    """Craft a personalized outreach email."""

    llm = get_llm(config)
    candidate_profile = profile.json(indent=2)
    prompt = prompts.outreach_prompt(candidate_profile=candidate_profile, institute_value=institute_value, language=language)
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content
