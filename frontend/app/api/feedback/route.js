import { appendFile, mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { NextResponse } from "next/server";

const FEEDBACK_PATH = resolve(process.cwd(), "..", "feedback_loop", "analyst_feedback", "feedback_log.jsonl");

function verdictFromConfidence(confidence) {
  if (confidence >= 70) return "true_positive";
  if (confidence <= 30) return "false_positive";
  return "uncertain";
}

export async function POST(request) {
  try {
    const payload = await request.json();
    const incidentId = String(payload.incidentId || "").trim();
    const analystConfidence = Number(payload.analystConfidence);
    const originalConfidence = Number(payload.originalConfidence);

    if (!incidentId) {
      return NextResponse.json({ error: "incidentId is required." }, { status: 400 });
    }

    if (Number.isNaN(analystConfidence) || analystConfidence < 0 || analystConfidence > 100) {
      return NextResponse.json({ error: "analystConfidence must be between 0 and 100." }, { status: 400 });
    }

    const record = {
      incident_id: incidentId,
      analyst_id: "web_analyst",
      verdict: verdictFromConfidence(analystConfidence),
      playbook_usefulness: "confidence_updated",
      notes: `Analyst updated confidence from ${originalConfidence}% to ${analystConfidence}% for ${payload.title || incidentId}.`,
      created_at: new Date().toISOString(),
      original_model_confidence: originalConfidence,
      updated_confidence: analystConfidence,
      source_file: payload.sourceFile || "",
    };

    await mkdir(dirname(FEEDBACK_PATH), { recursive: true });
    await appendFile(FEEDBACK_PATH, `${JSON.stringify(record)}\n`, "utf8");

    return NextResponse.json({ ok: true, record });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unable to store analyst feedback." },
      { status: 500 }
    );
  }
}
