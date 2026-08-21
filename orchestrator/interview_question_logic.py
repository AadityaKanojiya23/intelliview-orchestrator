"""
Interview Question Logic & Domain Strategy Module.
Enforces domain normalization, category distribution validation,
and question plan generation (40% Technical, 30% Behavioral, 30% Situational).
"""

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)

# Standard Category Distribution default (40% technical, 30% behavioral, 30% situational)
DEFAULT_CATEGORY_DISTRIBUTION = {
    "technical": 0.40,
    "behavioral": 0.30,
    "situational": 0.30,
}

VALID_CATEGORIES = {"technical", "behavioral", "situational"}

# Built-in question bank for domain-specific technical & behavioral/situational questions
DOMAIN_QUESTION_BANK = {
    "python": [
        {
            "question_id": "q_py_01",
            "text": "Explain Python's GIL (Global Interpreter Lock) and how it affects multithreading vs multiprocessing.",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["python", "concurrency", "performance"],
        },
        {
            "question_id": "q_py_02",
            "text": "What are Python decorators, and how do you write a parameterized decorator?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["python", "decorators", "metaprogramming"],
        },
        {
            "question_id": "q_py_03",
            "text": "How do Python generators work, and what are the advantages of yield over returning a list?",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["python", "generators", "memory"],
        },
        {
            "question_id": "q_py_04",
            "text": "Explain memory management and garbage collection mechanism in Python.",
            "category": "technical",
            "difficulty": "hard",
            "tags": ["python", "memory", "gc"],
        },
        {
            "question_id": "q_py_05",
            "text": "What is the difference between shallow copy and deep copy in Python? Give an example.",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["python", "data-structures"],
        },
    ],
    "data_science": [
        {
            "question_id": "q_ds_01",
            "text": "Explain the trade-off between Bias and Variance in machine learning models.",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["data-science", "ml", "theory"],
        },
        {
            "question_id": "q_ds_02",
            "text": "How do you deal with missing or imbalanced data in a binary classification dataset?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["data-science", "preprocessing"],
        },
        {
            "question_id": "q_ds_03",
            "text": "What is Precision vs Recall, and when would you optimize for Precision over Recall?",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["data-science", "metrics"],
        },
        {
            "question_id": "q_ds_04",
            "text": "Explain how Random Forest differs from Gradient Boosting Trees.",
            "category": "technical",
            "difficulty": "hard",
            "tags": ["data-science", "algorithms"],
        },
    ],
    "web_dev": [
        {
            "question_id": "q_web_01",
            "text": "Explain the difference between Server-Side Rendering (SSR) and Client-Side Rendering (CSR).",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["web-dev", "react", "nextjs"],
        },
        {
            "question_id": "q_web_02",
            "text": "How does CORS (Cross-Origin Resource Sharing) work and how do you resolve CORS errors safely?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["web-dev", "http", "security"],
        },
        {
            "question_id": "q_web_03",
            "text": "What are WebSockets and how do they differ from HTTP polling or Server-Sent Events (SSE)?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["web-dev", "networking"],
        },
        {
            "question_id": "q_web_04",
            "text": "Explain RESTful API design principles and the HTTP status codes 200, 201, 400, 401, 403, 404, 500.",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["web-dev", "api"],
        },
    ],
    "prompt_engineering": [
        {
            "question_id": "q_pe_01",
            "text": "What is the difference between zero-shot, one-shot, and few-shot prompting?",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["prompt_engineering", "few_shot"],
        },
        {
            "question_id": "q_pe_02",
            "text": "How would you design a prompt that makes an LLM return a strict JSON response?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "structured_output"],
        },
        {
            "question_id": "q_pe_03",
            "text": "What techniques can be used to reduce hallucinations when designing prompts for an LLM?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "hallucination"],
        },
        {
            "question_id": "q_pe_04",
            "text": "Explain the difference between system, user, and assistant instructions in a conversational LLM.",
            "category": "technical",
            "difficulty": "easy",
            "tags": ["prompt_engineering", "llm"],
        },
        {
            "question_id": "q_pe_05",
            "text": "How would you evaluate two different prompts to determine which one produces better results?",
            "category": "technical",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "evaluation"],
        },
        {
            "question_id": "q_pe_06",
            "text": "What is prompt injection and how can an application reduce the risk of prompt injection?",
            "category": "technical",
            "difficulty": "hard",
            "tags": ["prompt_engineering", "security"],
        },
        {
            "question_id": "q_pe_07",
            "text": "Tell me about a time when you improved a prompt after receiving poor model output.",
            "category": "behavioral",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "behavioral"],
        },
        {
            "question_id": "q_pe_08",
            "text": "Describe a situation where you had to explain an LLM limitation to a non-technical stakeholder.",
            "category": "behavioral",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "communication"],
        },
        {
            "question_id": "q_pe_09",
            "text": "An LLM keeps returning extra text instead of the required JSON format. How would you modify the prompt?",
            "category": "situational",
            "difficulty": "medium",
            "tags": ["prompt_engineering", "structured_output"],
        },
        {
            "question_id": "q_pe_10",
            "text": "A prompt works well for one LLM but poorly for another. What would you investigate and change?",
            "category": "situational",
            "difficulty": "hard",
            "tags": ["prompt_engineering", "optimization"],
        },
    ],
    "general_behavioral": [
        {
            "question_id": "q_beh_01",
            "text": "Describe a situation where you had a disagreement with a team member on a technical design decision. How did you resolve it?",
            "category": "behavioral",
            "difficulty": "medium",
            "tags": ["behavioral", "conflict-resolution", "teamwork"],
        },
        {
            "question_id": "q_beh_02",
            "text": "Tell me about a time you failed to meet a project deadline. What went wrong and what did you learn?",
            "category": "behavioral",
            "difficulty": "medium",
            "tags": ["behavioral", "time-management", "accountability"],
        },
        {
            "question_id": "q_beh_03",
            "text": "Give an example of how you explained a complex technical concept to a non-technical stakeholder.",
            "category": "behavioral",
            "difficulty": "easy",
            "tags": ["behavioral", "communication"],
        },
    ],
    "general_situational": [
        {
            "question_id": "q_sit_01",
            "text": "Imagine a high-severity production outage occurs during your shift. What step-by-step triage process do you follow?",
            "category": "situational",
            "difficulty": "hard",
            "tags": ["situational", "incident-management", "ops"],
        },
        {
            "question_id": "q_sit_02",
            "text": "If product management requests a major new feature 3 days before a scheduled release, how do you handle it?",
            "category": "situational",
            "difficulty": "medium",
            "tags": ["situational", "scope-management"],
        },
        {
            "question_id": "q_sit_03",
            "text": "How would you prioritize fixing tech debt versus delivering new customer features in a tight quarter?",
            "category": "situational",
            "difficulty": "medium",
            "tags": ["situational", "prioritization"],
        },
    ],
}


def normalize_domain(domain: str | None) -> str:
    """Normalize domain strings into canonical domain identifiers."""
    if not domain:
        return "python"
    d = domain.strip().lower().replace("-", "_").replace(" ", "_")
    if "prompt" in d:
        return "prompt_engineering"
    if "py" in d:
        return "python"
    if "data" in d or "ds" in d or "ai" in d or "ml" in d:
        return "data_science"
    if "web" in d or "frontend" in d or "backend" in d or "fullstack" in d:
        return "web_dev"
    return d


def validate_category_distribution(
    distribution: dict[str, float] | None,
) -> dict[str, float]:
    """
    Validates category distribution map.
    Accepts fractions (e.g. 0.40, 0.30, 0.30) or percentages (e.g. 40, 30, 30).
    Ensures total sum equals 1.0 (100%).
    """
    if not distribution:
        return dict(DEFAULT_CATEGORY_DISTRIBUTION)

    normalized: dict[str, float] = {}
    for key, val in distribution.items():
        cat = key.strip().lower()
        if cat not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{key}'. Allowed categories: {sorted(list(VALID_CATEGORIES))}"
            )
        try:
            num = float(val)
        except (ValueError, TypeError):
            raise ValueError(f"Distribution value for '{key}' must be numeric.")
        if num < 0:
            raise ValueError(f"Distribution value for '{key}' cannot be negative.")
        normalized[cat] = num

    # Fill missing categories with 0.0
    for cat in VALID_CATEGORIES:
        if cat not in normalized:
            normalized[cat] = 0.0

    total = sum(normalized.values())
    if total == 0:
        raise ValueError("Category distribution values cannot all be zero.")

    # If user provided percentages (summing close to 100), convert to decimals
    if math.isclose(total, 100.0, abs_tol=1.0):
        normalized = {k: round(v / 100.0, 4) for k, v in normalized.items()}
        total = sum(normalized.values())

    if not math.isclose(total, 1.0, abs_tol=0.01):
        raise ValueError(
            f"Category distribution total must equal 1.0 (or 100%). Current sum is {total:.2f}"
        )

    return normalized


def build_question_plan(
    template: dict[str, Any], domain: str | None = None
) -> dict[str, Any]:
    """
    Builds a question allocation plan based on template parameters.
    Calculates exact counts for technical, behavioral, and situational questions.
    """
    question_count = int(template.get("question_count", 10))
    domain_name = normalize_domain(
        domain or template.get("domain") or template.get("name")
    )
    distribution = validate_category_distribution(template.get("category_distribution"))

    tech_pct = distribution.get("technical", 0.40)
    beh_pct = distribution.get("behavioral", 0.30)
    sit_pct = distribution.get("situational", 0.30)

    tech_count = round(question_count * tech_pct)
    beh_count = round(question_count * beh_pct)
    # Adjust situational count to fit exactly total question count
    sit_count = max(0, question_count - tech_count - beh_count)

    plan = {
        "domain": domain_name,
        "question_count": question_count,
        "category_counts": {
            "technical": tech_count,
            "behavioral": beh_count,
            "situational": sit_count,
        },
        "category_percentages": {
            "technical": tech_pct,
            "behavioral": beh_pct,
            "situational": sit_pct,
        },
    }
    return plan


def get_template_questions(
    domain: str | None, distribution: dict[str, float] | None, question_count: int = 10
) -> list[dict[str, Any]]:
    """
    Generates an ordered question list matching the template's domain and category distribution.
    For Python Dev templates, returns 40% Python technical, 30% behavioral, 30% situational questions.
    """
    dom = normalize_domain(domain)
    dist = validate_category_distribution(distribution)
    plan = build_question_plan(
        {"question_count": question_count, "category_distribution": dist}, domain=dom
    )

    tech_needed = plan["category_counts"]["technical"]
    beh_needed = plan["category_counts"]["behavioral"]
    sit_needed = plan["category_counts"]["situational"]

    selected_questions = []

    # 1. Fetch domain technical questions
    tech_pool = DOMAIN_QUESTION_BANK.get(dom)
    if tech_pool is None:
        raise ValueError(f"No question bank available for domain: {dom}")
    for q in tech_pool[:tech_needed]:
        selected_questions.append(q)

    # If domain technical pool falls short, supplement with general python questions
    if len(selected_questions) < tech_needed:
        for q in DOMAIN_QUESTION_BANK["python"]:
            if q not in selected_questions and len(selected_questions) < tech_needed:
                selected_questions.append(q)

    # 2. Fetch behavioral questions
    beh_pool = DOMAIN_QUESTION_BANK["general_behavioral"]
    for q in beh_pool[:beh_needed]:
        selected_questions.append(q)

    # 3. Fetch situational questions
    sit_pool = DOMAIN_QUESTION_BANK["general_situational"]
    for q in sit_pool[:sit_needed]:
        selected_questions.append(q)

    return selected_questions
