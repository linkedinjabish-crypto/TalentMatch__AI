import re
from dataclasses import dataclass

# ================================
# CONFIGURATION
# ================================

SENIORITY_LADDER = [
    "junior", "associate", "mid", "senior",
    "lead", "staff", "principal", "architect",
    "manager", "director", "head", "vp", "c-level"
]

ARCH_WORDS = {
    "scalability", "microservices", "system design", "architecture",
    "distributed systems", "high availability", "cloud native",
    "governance", "stakeholders", "strategy", "roadmap",
    "optimization", "infrastructure", "mentorship",
    "leadership", "budget", "cross-functional", "vision"
}

# ================================
# DATA STRUCTURES
# ================================

@dataclass
class AnalysisResult:
    stability: int
    growth: int
    seniority: int
    final_score: float


# ================================
# ANALYZERS
# ================================

class StabilityAnalyzer:
    @staticmethod
    def analyze(text: str) -> int:
        if not text:
            return 50

        years = re.findall(
            r"(?:19|20)\d{2}\s*(?:-|to)\s*(?:(?:19|20)\d{2}|present|current|now)",
            text.lower()
        )

        if not years:
            return 60

        if len(years) > 3 and len(text.split()) < 500:
            return 30

        return 90


class GrowthAnalyzer:
    @staticmethod
    def analyze(text: str) -> int:
        if not text:
            return 0

        t = text.lower()

        growth_keywords = [
            "promoted", "transitioned", "lead",
            "mentored", "ownership", "scaled"
        ]

        score = sum(10 for kw in growth_keywords if kw in t)

        titles = [title for title in SENIORITY_LADDER if title in t]

        if len(titles) >= 3:
            score += 30

        return min(score, 100)


class SeniorityAnalyzer:
    @staticmethod
    def analyze(resume: str, jd: str) -> int:
        if not resume or not jd:
            return 50

        rt = resume.lower()
        jt = jd.lower()

        is_senior_jd = any(word in jt for word in SENIORITY_LADDER)

        arch_count = sum(1 for word in ARCH_WORDS if word in rt)

        if is_senior_jd:
            if arch_count >= 6:
                return 100
            elif arch_count >= 3:
                return 75
            else:
                return 40
        else:
            if arch_count > 3:
                return 85
            return 90


# ================================
# SCORING ENGINE
# ================================

class RecruiterScoringEngine:

    WEIGHTS = {
        "stability": 0.25,
        "growth": 0.25,
        "seniority": 0.50
    }

    @staticmethod
    def evaluate(resume: str, jd: str) -> AnalysisResult:
        stability = StabilityAnalyzer.analyze(resume)
        growth = GrowthAnalyzer.analyze(resume)
        seniority = SeniorityAnalyzer.analyze(resume, jd)

        final_score = (
            stability * RecruiterScoringEngine.WEIGHTS["stability"] +
            growth * RecruiterScoringEngine.WEIGHTS["growth"] +
            seniority * RecruiterScoringEngine.WEIGHTS["seniority"]
        )

        return AnalysisResult(
            stability=stability,
            growth=growth,
            seniority=seniority,
            final_score=round(final_score, 2)
        )


# ================================
# INSIGHTS ENGINE
# ================================

class InsightEngine:

    @staticmethod
    def generate(result: AnalysisResult):
        insights = []

        if result.stability > 80:
            insights.append(("🏆 High Stability", "#10b981"))

        if result.stability < 40:
            insights.append(("⚠️ Job Hopper", "#f59e0b"))

        if result.growth > 70:
            insights.append(("📈 Rapid Growth", "#a855f7"))

        if result.seniority > 85:
            insights.append(("🔥 Domain Expert", "#3b82f6"))

        if result.seniority < 50:
            insights.append(("🏢 Mismatch", "#ef4444"))

        if result.final_score > 90:
            insights.append(("⭐ Superstar Hire", "#fbbf24"))

        return insights


# ================================
# INTERVIEW GENERATOR
# ================================

class InterviewGenerator:

    @staticmethod
    def generate(jd_text: str):
        t = jd_text.lower()
        questions = []

        if "python" in t:
            questions.append("Explain how you optimized a Python-based system.")

        if "aws" in t:
            questions.append("How do you design scalable AWS architectures?")

        if any(word in t for word in ["lead", "manager", "architect"]):
            questions.append("Describe a system you designed end-to-end.")

        questions.append("Describe a major technical challenge you solved.")

        return questions


# ================================
# PUBLIC API FUNCTIONS
# ================================

def analyze_stability_score(resume: str) -> int:
    """Analyze career stability from resume."""
    return StabilityAnalyzer.analyze(resume)


def analyze_career_growth(resume: str) -> int:
    """Analyze career growth from resume."""
    return GrowthAnalyzer.analyze(resume)


def analyze_seniority_density(resume: str, jd: str) -> int:
    """Analyze seniority match with job description."""
    return SeniorityAnalyzer.analyze(resume, jd)


def get_recruiter_insights(resume: str, jd: str, final_score: float):
    """Generate recruiter insights based on analysis."""
    result = RecruiterScoringEngine.evaluate(resume, jd)
    insights = InsightEngine.generate(result)
    return insights