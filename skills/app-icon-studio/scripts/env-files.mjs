import { readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const SKILL_NAME = "app-icon-studio";

export const ENV_FILE_PATHS = [
  ...(process.env.HOME ? [path.join(process.env.HOME, ".claude", SKILL_NAME, ".env")] : []),
  path.join(process.cwd(), ".claude", `${SKILL_NAME}.env`),
];

export function loadSkillEnvFiles(paths = ENV_FILE_PATHS) {
  const loaded = [];
  for (const envPath of paths) {
    let text;
    try {
      text = readFileSync(envPath, "utf8");
    } catch (error) {
      if (error?.code === "ENOENT") {
        continue;
      }
      throw error;
    }

    for (const [key, value] of parseEnvText(text)) {
      process.env[key] = value;
    }
    loaded.push(envPath);
  }
  return loaded;
}

export function describeSkillEnvFiles(loadedPaths, paths = ENV_FILE_PATHS) {
  return paths.map((envPath) => `${envPath} (${loadedPaths.includes(envPath) ? "loaded" : "not found"})`);
}

function parseEnvText(text) {
  const entries = [];
  for (const rawLine of text.split(/\r?\n/)) {
    let line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }
    if (line.startsWith("export ")) {
      line = line.slice("export ".length).trim();
    }
    const separator = line.indexOf("=");
    if (separator === -1) {
      continue;
    }

    const key = line.slice(0, separator).trim();
    let value = line.slice(separator + 1).trim();
    if (!key) {
      continue;
    }
    if (value.length >= 2 && value[0] === value[value.length - 1] && ["\"", "'"].includes(value[0])) {
      value = value.slice(1, -1);
    }
    entries.push([key, value]);
  }
  return entries;
}
