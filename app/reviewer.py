import re
from dataclasses import dataclass
from typing import Iterable

@dataclass
class FindingResult:
    category: str
    severity: str
    title: str
    description: str
    recommendation: str
    line_number: int | None = None

LANG_ALIASES = {
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript",
    "typescript": "javascript", "ts": "javascript",
    "java": "java", "c": "c", "cpp": "cpp", "c++": "cpp",
    "go": "go", "golang": "go", "sql": "sql",
}

def normalize_language(language: str) -> str:
    return LANG_ALIASES.get(language.lower().strip(), language.lower().strip())

def line_of(source: str, match: re.Match) -> int:
    return source.count("\n", 0, match.start()) + 1

def add(results, category, severity, title, description, recommendation, line=None):
    results.append(FindingResult(category, severity, title, description, recommendation, line))

def analyze(source: str, language: str, historical: Iterable[dict] = ()) -> list[FindingResult]:
    lang = normalize_language(language)
    findings = []
    lines = source.splitlines()

    # Universal readability / maintainability
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            add(findings, "readability", "medium", "Long line reduces readability",
                "This line is over 120 characters and is harder to review and maintain.",
                "Break the statement into smaller expressions or helper functions.", i)
        if re.search(r"\b(for|while)\b.*\b(for|while)\b", line):
            add(findings, "performance", "medium", "Nested loop detected",
                "Nested iteration can become expensive as input size grows.",
                "Consider indexing data with a set/dictionary or reducing the algorithmic complexity.", i)

    # Language-specific checks
    if lang == "python":
        for i, line in enumerate(lines, 1):
            if re.match(r"\s*def\s+\w+\([^)]*=\s*(\[\]|\{\})", line):
                add(findings, "bug", "high", "Mutable default argument",
                    "A list or dictionary default is shared between function calls.",
                    "Use None as the default and initialize the mutable object inside the function.", i)
            if re.search(r"\bexcept\s*:\s*$", line):
                add(findings, "maintainability", "medium", "Bare exception handler",
                    "Bare except catches system-exiting exceptions and hides the real failure.",
                    "Catch the specific exception types you expect and log useful context.", i)
            if re.search(r"(^|[\s,(])([a-zA-Z])\s*=", line):
                add(findings, "readability", "low", "Single-character variable name",
                    "A short variable name provides little semantic information.",
                    "Prefer descriptive names such as customer_count or retry_limit.", i)

    if lang == "javascript":
        for i, line in enumerate(lines, 1):
            if re.search(r"(^|[^=])==([^=]|$)|(^|[^!])!=([^=]|$)", line):
                add(findings, "bug", "medium", "Loose equality",
                    "Loose equality performs implicit type conversion and can produce surprising results.",
                    "Prefer === or !== unless coercion is explicitly intended.", i)
            if re.search(r"\beval\s*\(", line):
                add(findings, "security", "critical", "Dynamic eval detected",
                    "Executing dynamic strings can allow code injection when data is user-controlled.",
                    "Remove eval and use explicit parsing or a safe dispatch table.", i)

    if lang in {"java", "c", "cpp", "go"}:
        sql_pat = re.compile(r'["\'].*\b(SELECT|INSERT|UPDATE|DELETE)\b.*["\']\s*\+')
        for m in sql_pat.finditer(source, re.I):
            add(findings, "security", "critical", "Potential SQL injection",
                "SQL appears to be constructed with string concatenation.",
                "Use parameterized queries/prepared statements and bind user values as parameters.",
                line_of(source, m))

    # Universal security checks
    for pattern, title, desc, rec, sev in [
        (r"(?i)(password|secret|api[_-]?key)\s*=\s*['\"][^'\"]+['\"]",
         "Hard-coded secret", "A credential-like value is embedded in source code.",
         "Move secrets to environment variables or a managed secret store.", "critical"),
        (r"(?i)\b(os\.system|subprocess\.call|subprocess\.Popen)\s*\(",
         "Shell command execution", "Process execution can become command injection when input is not trusted.",
         "Use fixed command arguments, avoid shell=True, and validate all external input.", "high"),
    ]:
        m = re.search(pattern, source)
        if m:
            add(findings, "security", sev, title, desc, rec, line_of(source, m))

    # Historical rules: keyword similarity
    src_words = set(re.findall(r"[a-zA-Z]{4,}", source.lower()))
    for rule in historical:
        words = set(re.findall(r"[a-zA-Z]{4,}", rule["description"].lower()))
        overlap = len(src_words & words)
        if overlap >= 2:
            category = rule["type"]
            add(findings, category if category in {"security","performance","readability","architecture","bug"} else "historical",
                "low", "Historical review insight",
                f"Past review data highlights: {rule['description']}.",
                "Consider this historical pattern when refining the current implementation.")

    # Architecture guidance from broad patterns
    if source.count("def ") + source.count("function ") + source.count("public static") > 12:
        add(findings, "architecture", "medium", "Large review surface",
            "The submission contains many functions/methods in one unit, which can make ownership and testing harder.",
            "Separate cohesive responsibilities into modules/services with clear interfaces.")

    if not findings:
        add(findings, "quality", "low", "No obvious issues found",
            "The deterministic review checks did not identify a high-confidence problem.",
            "Add automated tests, linting, dependency scanning, and peer review before production release.")

    return findings

def quality_score(findings: list[FindingResult]) -> float:
    penalties = {"critical": 3.0, "high": 2.0, "medium": 1.0, "low": 0.25}
    score = 10.0 - sum(penalties.get(f.severity, 0.5) for f in findings)
    # Avoid a misleadingly low score from many historical informational findings.
    score = max(1.0, min(10.0, score))
    return round(score, 1)

def summarize(findings: list[FindingResult], score: float) -> str:
    critical = sum(f.severity == "critical" for f in findings)
    high = sum(f.severity == "high" for f in findings)
    if score >= 9:
        tone = "Excellent"
    elif score >= 7:
        tone = "Good"
    elif score >= 5:
        tone = "Needs improvement"
    else:
        tone = "High-priority remediation recommended"
    return f"{tone}. Quality score: {score}/10. {critical} critical and {high} high-severity findings were detected."
