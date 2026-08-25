from app.reviewer import analyze, quality_score

def test_sql_injection_is_detected():
    code = 'query = "SELECT * FROM users WHERE id = " + user_id'
    findings = analyze(code, "python")
    assert any(f.category == "security" for f in findings)

def test_clean_code_has_reasonable_score():
    code = """def add_numbers(first, second):
    return first + second
"""
    score = quality_score(analyze(code, "python"))
    assert score >= 7
