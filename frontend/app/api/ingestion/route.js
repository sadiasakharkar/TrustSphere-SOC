import { mkdir, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

import { NextResponse } from "next/server";

const execFileAsync = promisify(execFile);
const ROOT = resolve(process.cwd(), "..");
const PYTHON = "python";

function inferDomain(fileName) {
  const lower = fileName.toLowerCase();
  if (lower.includes("mail") || lower.includes("email") || lower.includes("office")) return "email";
  if (lower.includes("waf") || lower.includes("web") || lower.includes("zeek")) return "network";
  if (lower.includes("sysmon") || lower.includes("windows") || lower.includes("endpoint")) return "endpoint";
  if (lower.includes("azure") || lower.includes("auth") || lower.includes("signin")) return "identity";
  return "network";
}

async function runPipeline(filePath, datasetId, domain, limit = 50) {
  const scriptPath = resolve(ROOT, "scripts", "frontend_live_ingestion.py");
  const { stdout, stderr } = await execFileAsync(
    PYTHON,
    [scriptPath, filePath, datasetId, domain, String(limit)],
    {
      cwd: ROOT,
      timeout: 300000,
      maxBuffer: 10 * 1024 * 1024,
    }
  );
  if (stderr && stderr.trim()) {
    console.warn(stderr);
  }
  return JSON.parse(stdout);
}

export async function GET() {
  try {
    const samplePath = resolve(ROOT, "datasets", "synthetic", "ps1_demo", "ps1_disrupted.json");
    const payload = await runPipeline(samplePath, "frontend_simulation", "network", 50);
    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { error: "Unable to run ingestion simulation." },
      { status: 500 }
    );
  }
}

export async function POST(request) {
  try {
    const formData = await request.formData();
    const file = formData.get("file");

    if (!file || typeof file === "string") {
      return NextResponse.json({ error: "A log file is required." }, { status: 400 });
    }

    const buffer = Buffer.from(await file.arrayBuffer());
    const uploadDir = join(tmpdir(), "trustsphere-ingestion");
    await mkdir(uploadDir, { recursive: true });
    const safeName = `${Date.now()}-${file.name.replace(/[^a-zA-Z0-9._-]/g, "_")}`;
    const targetPath = join(uploadDir, safeName);
    await writeFile(targetPath, buffer);

    const payload = await runPipeline(
      targetPath,
      "frontend_upload",
      inferDomain(file.name),
      50
    );
    return NextResponse.json(payload);
  } catch (error) {
    return NextResponse.json(
      { error: "Unable to process the uploaded log package." },
      { status: 500 }
    );
  }
}
