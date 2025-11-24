"""Prompt templates for the AI agent."""

from textwrap import dedent


def parsing_prompt() -> str:
    """Prompt guiding the LLM to extract academic CV details."""

    return dedent(
        """
        You are an expert research administrator. Extract the following fields from the provided CV text.
        Return a compact JSON with keys: name, current_institution, estimated_ranking, h_index,
        research_focus_keywords (list), key_publications (list of {title, journal, year}),
        grants (list of {title, amount, year, sponsor}), notes.

        Journals of interest include Nature, Science, Cell, and The Lancet. Use N/A when not found.
        """
    ).strip()


def matching_prompt(cv_summary: str, target_direction: str) -> str:
    """Prompt used to score candidate fit against a research direction."""

    return dedent(
        f"""
        You are assisting a medical research institute to evaluate faculty candidates.
        Consider the following parsed CV data:\n{cv_summary}\n
        Target research direction: {target_direction}

        Provide a JSON with: suitability_score (0-100), reasoning (2-3 sentences),
        strengths (list), gaps (list), recommended_projects (list of short ideas).
        """
    ).strip()


def outreach_prompt(candidate_profile: str, institute_value: str, language: str = "English") -> str:
    """Prompt to produce a personalized outreach email."""

    return dedent(
        f"""
        Write a concise, respectful outreach email to a senior scientist about joining our institute.
        Use an academic tone and reference specific achievements from the profile below.

        Candidate profile:\n{candidate_profile}\n
        Institute value proposition: {institute_value}
        Language: {language}

        Include a specific paper or grant mention to prove personalization.
        """
    ).strip()
