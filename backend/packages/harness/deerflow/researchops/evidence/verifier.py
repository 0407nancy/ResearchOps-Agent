from __future__ import annotations

import re

from deerflow.researchops.schemas import Claim, EvidenceRef, VerifiedClaim


REF_RE = re.compile(r"\[([^\[\]]+#[^\[\]]+)\]")


def extract_claims(markdown: str) -> list[Claim]:
    claims: list[Claim] = []
    in_evidence = False
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("## Evidence"):
            in_evidence = True
            continue
        if line.startswith("#") or in_evidence:
            continue
        if not line.startswith("- "):
            continue
        text = line[2:].strip()
        refs = REF_RE.findall(text)
        cleaned = REF_RE.sub("", text).strip()
        if cleaned:
            claims.append(Claim(text=cleaned, evidence_refs=refs))
    return claims


def verify_claims(*, claims: list[Claim], evidence_table: list[EvidenceRef]) -> list[VerifiedClaim]:
    evidence_by_ref = {evidence.source_ref: evidence for evidence in evidence_table}
    verified: list[VerifiedClaim] = []
    for claim in claims:
        matched_refs = [ref for ref in claim.evidence_refs if ref in evidence_by_ref]
        if matched_refs and _claim_matches_any_evidence(claim.text, [evidence_by_ref[ref] for ref in matched_refs]):
            status = "supported"
        elif matched_refs:
            status = "weakly_supported"
        else:
            status = "unsupported"
        verified.append(
            VerifiedClaim(
                text=claim.text,
                evidence_refs=claim.evidence_refs,
                support_status=status,
                matched_evidence_refs=matched_refs,
            )
        )
    return verified


def _claim_matches_any_evidence(claim_text: str, evidence_items: list[EvidenceRef]) -> bool:
    claim_terms = _terms(claim_text)
    for evidence in evidence_items:
        evidence_terms = _terms(" ".join(part for part in (evidence.title, evidence.snippet) if part))
        if claim_terms and len(claim_terms & evidence_terms) / len(claim_terms) >= 0.5:
            return True
    return False


def _terms(text: str) -> set[str]:
    ascii_terms = re.findall(r"[A-Za-z][A-Za-z0-9_-]+", text.lower())
    cjk_terms = re.findall(r"[\u4e00-\u9fff]{2,}", text)
    return set(ascii_terms + cjk_terms)
