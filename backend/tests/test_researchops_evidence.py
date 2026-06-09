from deerflow.researchops.evidence.verifier import extract_claims, verify_claims
from deerflow.researchops.schemas import EvidenceRef


def test_extract_claims_ignores_headings_and_keeps_report_bullets():
    markdown = """
# Weekly Report

## 进展
- 完成 intent classifier [note:weekly.md#L1-L2]
- 完成 memory store

## Evidence
- `note:weekly.md#L1-L2` (source): 完成 intent classifier
"""

    claims = extract_claims(markdown)

    assert [claim.text for claim in claims] == ["完成 intent classifier", "完成 memory store"]
    assert claims[0].evidence_refs == ["note:weekly.md#L1-L2"]


def test_verify_claims_marks_supported_and_unsupported_claims():
    claims = extract_claims("- 完成 intent classifier [note:weekly.md#L1-L2]\n- 完成 multi-agent")
    evidence = [
        EvidenceRef(
            source_ref="note:weekly.md#L1-L2",
            kind="source",
            snippet="完成 intent classifier 和 HITL checkpoint",
        )
    ]

    verified = verify_claims(claims=claims, evidence_table=evidence)

    assert verified[0].support_status == "supported"
    assert verified[0].matched_evidence_refs == ["note:weekly.md#L1-L2"]
    assert verified[1].support_status == "unsupported"
