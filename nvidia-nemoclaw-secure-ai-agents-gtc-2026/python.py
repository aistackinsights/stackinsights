from nemoclaw import PrivacyRouter

router = PrivacyRouter(
    pii_detection=True,
    redaction_mode="mask",
    credential_patterns=["sk-*", "Bearer *", "AIza*"]
)
