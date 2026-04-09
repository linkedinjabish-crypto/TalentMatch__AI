import re

# 👔 PRO-RECRUITER SENIORITY LADDER
SENIORITY_LADDER = ["junior", "associate", "senior", "lead", "staff", "principal", "architect", "director", "manager", "head", "vp", "c-level"]

# 🏗️ ARCHITECTURAL STACK (HIGH-DENSITY WORDS)
ARCH_WORDS = {
    "scalability", "microservices", "system design", "architecture", "distributed systems", "high availability",
    "cloud native", "governance", "stakeholders", "strategy", "roadmap", "lifecycle", "optimization", "infrastructure",
    "mentorship", "leadership", "budget", "p&l", "cross-functional", "consensus", "influence", "vision"
}

def analyze_stability_score(text):
    """Detects tenure and job hopping patterns based on year ranges."""
    if not text: return 50 # Default neutral
    
    # Simple regex to find year ranges like 2019-2022, 2015 - Present, etc.
    years = re.findall(r"(?:19|20)\d{2}\s*(?:-|to)\s*(?:(?:19|20)\d{2}|present|current|now)", text.lower())
    
    if not years: return 60 # Not enough data, assume average
    
    # If many short-lived roles are detected in a small space
    if len(years) > 3 and len(text.split()) < 500:
        return 30 # High "Job Hopper" potential
        
    return 90 # High stability (fewer, longer chunks)

def analyze_career_growth(text):
    """Detects if a candidate's titles are progressing upward."""
    if not text: return 0
    t = text.lower()
    
    progression_score = 0
    # Check for keywords that indicate growth/leadership over time
    growth_keywords = ["promoted", "transitioned to", "tasked with", "leadership", "mentored", "lead", "senior"]
    progression_score = sum(10 for kw in growth_keywords if kw in t)
    
    # Check for title ladder jumps
    found_titles = [title for title in SENIORITY_LADDER if title in t]
    if len(found_titles) > 2: progression_score += 30 # Mentioning multiple levels usually implies growth
    
    return min(100, progression_score)

def analyze_seniority_density(resume_text, jd_text):
    """Compares the vocabulary complexity of the JD vs the Resume."""
    if not resume_text or not jd_text: return 50
    rt = resume_text.lower()
    jt = jd_text.lower()
    
    # 1. Identify JD Seniority "Expectation"
    is_senior_jd = any(word in jt for word in ["senior", "lead", "staff", "principal", "architect", "manager"])
    
    # 2. Identify Resume "Complexity"
    arch_count = sum(1 for word in ARCH_WORDS if word in rt)
    
    if is_senior_jd:
        # Senior JD expects high density of arch words
        if arch_count >= 5: return 100
        if arch_count >= 2: return 70
        return 40 # JD is senior, but resume is task-only
    else:
        # Junior JD
        if arch_count > 3: return 85 # "Overqualified" potential but strong
        return 90 # Perfect "fit" for a junior/task-oriented role

def get_recruiter_insights(resume, jd, final_score):
    """Generates glowing neon badges based on the pro-recruiter analysis."""
    insights = []
    
    stability = analyze_stability_score(resume)
    growth = analyze_career_growth(resume)
    density = analyze_seniority_density(resume, jd)
    
    # Badges based on scores
    if stability > 80: insights.append(("🏆 High Stability", "#10b981"))
    if stability < 40: insights.append(("⚠️ Job Hopper", "#f59e0b"))
    
    if growth > 70: insights.append(("📈 Rapid Growth", "#a855f7"))
    
    if density > 85: insights.append(("🔥 Domain Expert", "#3b82f6"))
    if density < 50: insights.append(("🏢 Mismatched Seniority", "#ef4444"))
    
    # Impact-based (re-use existing logic if possible, or add simple flags)
    if final_score > 90: insights.append(("⭐️ Superstar Hire", "#fbbf24"))
    
    return insights

def rule_based_questions(jd_text):
    """
    Generates a high-fidelity interview question matrix based on JD keywords.
    Categorizes into Technical, Situational, and Behavioral.
    """
    from tech_library import SKILL_LIBRARY
    
    t = jd_text.lower()
    questions = []
    
    # 🧪 Logic: Categorize identified skills and map to question templates
    found_tech = []
    for cat, skills in SKILL_LIBRARY.items():
        if cat in ["Backend Technologies", "Frontend Technologies", "Cloud Platforms", "DevOps & Tools", "Databases", "Machine Learning"]:
            for s in skills:
                if re.search(r'\b' + re.escape(s) + r'\b', t):
                    found_tech.append(s.title())

    # Map discovered tech to standard tech questions
    if found_tech:
        questions.append("### 💻 Technical Deep-Dive")
        for skill in list(set(found_tech))[:5]:
            questions.append(f"- **{skill}**: Can you walk us through a complex implementation using {skill}? What were the scaling challenges?")
            questions.append(f"- **{skill} Architecture**: How do you stay updated with the latest in the {skill} ecosystem, and how would you apply it to our current stack?")

    # 👔 Leadership / Architecture (Seniority check)
    is_senior = any(word in t for word in ["senior", "lead", "architect", "manager", "principal", "staff"])
    if is_senior:
        questions.append("### 🏗️ Architecture & Strategy")
        questions.append("- **System Design**: Describe a time you had to design a system for high availability. What tradeoffs did you make?")
        questions.append("- **Mentorship**: How do you approach code reviews and growing the technical skills of junior developers on your team?")
        questions.append("- **Vision**: Where do you see the technical roadmap of a platform like ours evolving in the next 18-24 months?")

    # 🤝 Behavioral / Soft Skills
    questions.append("### 🤝 Behavioral & Leadership")
    questions.append("- **Conflict**: Describe a situation where you had a technical disagreement with a peer. How did you resolve it?")
    questions.append("- **Impact**: What is the most significant technical project you've delivered, and what was the quantifiable business impact?")
    questions.append("- **Ambiguity**: How do you handle shifting priorities and tight deadlines in a fast-paced environment?")

    # Form as a unified HTML-ready string for Streamlit-markdown integration
    matrix_html = "<div style='background: rgba(12, 8, 30, 0.4); border: 1px solid rgba(16, 185, 129, 0.2); border-radius: 16px; padding: 30px; backdrop-filter: blur(12px); border-left: 4px solid #10b981;'>"
    matrix_html += "<h2 style='color: #10b981; margin-top: 0;'>Interview Matrix</h2>"
    
    # Simple list to HTML
    for q in questions:
        if q.startswith("###"):
            matrix_html += f"<h4 style='color: #e2e8f0; margin-top: 20px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;'>{q.strip('# ')}</h4>"
        else:
            matrix_html += f"<p style='color: #94a3b8; font-size: 15px; margin-left: 10px;'>{q}</p>"
            
    matrix_html += "</div>"
    return matrix_html
