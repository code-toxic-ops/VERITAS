from app.engine import analyze

def test_learned_model_is_used_for_message_classification():
    result = analyze("Your account will be closed. Share your OTP immediately to restore access.")
    assert result["model_status"] == "ready"
    assert result["classification"] in {"genuine", "scam", "spam"}
    assert result["risk_band"] in {"low", "moderate", "high", "critical"}
    assert result["risk_label"]

def test_learned_model_assesses_url_without_opening_it():
    result = analyze(url="http://google-login-verify.xyz/signin")
    assert result["model_status"] == "ready"
    assert result["url_assessment"] in {"malicious-pattern", "lower-risk-pattern"}
    assert result["urls"][0]["url"] == "http://google-login-verify.xyz/signin"

def test_interface_payload_uses_categorical_risk_summary():
    result = analyze("Your internship is confirmed. Pay a refundable registration fee today.")
    assert result["risk_band"] in {"low", "moderate", "high", "critical"}
    assert result["risk_summary"]
