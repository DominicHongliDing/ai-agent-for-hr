"""Streamlit interface for the academic talent AI agent."""

from __future__ import annotations

import json
import os
from typing import Dict

import pandas as pd
import streamlit as st

from prompts import parsing_prompt
from utils import (
    CVProfile,
    ModelConfig,
    build_candidate_table,
    demo_profile,
    generate_match_report,
    generate_outreach,
    heuristic_extract,
    llm_structured_parse,
    load_pdf_text,
)


st.set_page_config(page_title="Academic Talent AI Agent", layout="wide")
st.title("🏥 Academic Talent Recruitment Assistant")


# --- Sidebar configuration
with st.sidebar:
    st.header("Model Settings")
    provider = st.selectbox("Provider", options=["openai", "anthropic"], index=0)
    model_name = st.text_input(
        "Model name",
        value="gpt-4o-mini" if provider == "openai" else "claude-3-5-sonnet-20240620",
        help="建议使用新版 OpenAI SDK 支持的 gpt-4o-mini，兼具速度与性价比。",
    )
    default_api_key = os.getenv("OPENAI_API_KEY") if provider == "openai" else os.getenv("ANTHROPIC_API_KEY")
    api_key = st.text_input("API Key", type="password", value=default_api_key or "")
    st.markdown(
        """
        Provide your API key to enable LLM-powered parsing, scoring, and outreach.
        Data is processed client-side in this demo. Leave blank to try the built-in demo profile.
        """
    )
    st.markdown(
        """
        **操作小贴士**
        1. 没有 API Key 也能点击「加载示例简历」体验完整流程。
        2. 若模型返回格式异常，系统会自动降级到启发式解析。
        """
    )


def ensure_state():
    if "profiles" not in st.session_state:
        st.session_state["profiles"] = {}
    if "analysis" not in st.session_state:
        st.session_state["analysis"] = {}


def add_profile(name: str, profile: CVProfile):
    st.session_state["profiles"][name] = profile


ensure_state()


# --- Tabs
resume_tab, match_tab, outreach_tab = st.tabs([
    "Resume Analysis",
    "Matching Report",
    "Outreach Writer",
])


with resume_tab:
    st.subheader("Smart Academic CV Parser")
    st.caption("上传 PDF 或直接加载示例简历，帮助你快速上手。")
    uploaded = st.file_uploader("Upload academic CV (PDF)", type=["pdf"])
    candidate_name = st.text_input("Candidate Name (for tracking)")
    use_llm = st.checkbox("Use LLM parsing (requires API key)", value=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Parse CV", type="primary"):
            if not uploaded:
                st.error("Please upload a PDF file first.")
            elif use_llm and not api_key:
                st.error("Provide an API key or disable LLM parsing.")
            else:
                with st.spinner("Extracting CV details..."):
                    raw_text = load_pdf_text(uploaded)
                    profile = heuristic_extract(raw_text)
                    if use_llm and api_key:
                        config = ModelConfig(provider=provider, model=model_name, api_key=api_key)
                        profile = llm_structured_parse(raw_text, config)
                    if candidate_name:
                        profile.name = candidate_name
                    add_profile(profile.name, profile)
                    st.success(f"Parsed profile saved for {profile.name}")
                    st.json(json.loads(profile.json()))
    with col2:
        if st.button("Load demo profile"):
            profile = demo_profile()
            add_profile(profile.name, profile)
            st.success("Demo profile added. You can skip PDF upload and continue to Matching/Outreach.")
            st.json(json.loads(profile.json()))

    if st.session_state["profiles"]:
        st.markdown("### Parsed Candidates")
        st.dataframe(build_candidate_table(st.session_state["profiles"]), use_container_width=True)

with match_tab:
    st.subheader("Talent Matching & Scoring")
    st.caption("选择候选人 + 输入研究方向，一键生成 0-100 评分与理由。")
    if not st.session_state["profiles"]:
        st.info("Upload and parse at least one CV to start matching.")
    else:
        selected = st.selectbox("Select Candidate", options=list(st.session_state["profiles"].keys()))
        target_direction = st.text_area(
            "Target Research Direction / Job Description",
            placeholder="e.g., Immunology with focus on tumor microenvironment",
        )
        if st.button("Generate Analysis", type="primary"):
            if not api_key:
                st.error("API key required for LLM analysis.")
            elif not target_direction.strip():
                st.error("Please enter a target research direction.")
            else:
                with st.spinner("Generating match report..."):
                    config = ModelConfig(provider=provider, model=model_name, api_key=api_key)
                    profile = st.session_state["profiles"][selected]
                    report = generate_match_report(profile, target_direction, config)
                    st.session_state["analysis"][selected] = report
                    st.success("Analysis ready")
                    st.json(report)

with outreach_tab:
    st.subheader("Hyper-Personalized Outreach Generator")
    st.caption("基于匹配结果生成中/英文邀约邮件，突出候选人研究亮点。")
    if not st.session_state["analysis"]:
        st.info("Run a matching analysis first to prepare outreach content.")
    else:
        selected = st.selectbox("Select Candidate for Outreach", options=list(st.session_state["analysis"].keys()))
        institute_value = st.text_area(
            "Institute Value Proposition",
            placeholder="World-class translational medicine platforms, competitive startup packages...",
        )
        language = st.selectbox("Language", options=["English", "Chinese"], index=0)
        if st.button("Generate Outreach Email", type="primary"):
            if not api_key:
                st.error("API key required for outreach generation.")
            else:
                with st.spinner("Drafting personalized outreach..."):
                    config = ModelConfig(provider=provider, model=model_name, api_key=api_key)
                    profile = st.session_state["profiles"].get(selected)
                    if not profile:
                        st.error("Profile missing. Please rerun analysis.")
                    else:
                        email = generate_outreach(profile, institute_value, language, config)
                        st.success("Draft ready")
                        st.code(email, language="markdown")


st.markdown(
    "---\nMade for high-end academic talent recruitment. Upload a CV, score the fit, and reach out with confidence."
)
