from __future__ import annotations

import json

from langchain.tools import tool

from deerflow.researchops.report_writer import write_report
from deerflow.researchops.schemas import ContextPacket


@tool("report_writer", parse_docstring=True)
def report_writer_tool(
    context_packet_json: str,
    output_format: str,
    output_dir: str = "outputs/reports",
    log_summary_json: str = "{}",
) -> str:
    """Generate a Markdown ResearchOps report from a context packet.

    Args:
        context_packet_json: JSON ContextPacket from context_builder.
        output_format: Report format such as daily_report, weekly_report, meeting_prep, or experiment_review.
        output_dir: Directory for generated markdown reports.
        log_summary_json: Optional log summary JSON from log_parser.
    """
    packet = ContextPacket.model_validate_json(context_packet_json)
    log_summary = json.loads(log_summary_json or "{}")
    result = write_report(
        context_packet=packet,
        output_format=output_format,
        output_dir=output_dir,
        log_summary=log_summary,
    )
    return result.model_dump_json(indent=2)
