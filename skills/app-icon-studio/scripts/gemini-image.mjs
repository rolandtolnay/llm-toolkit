#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { describeSkillEnvFiles, loadSkillEnvFiles } from "./env-files.mjs";

const DEFAULT_MODEL = "gemini-3-pro-image-preview";
const DEFAULT_API_BASE = "https://generativelanguage.googleapis.com/v1beta";
const DEFAULT_OUT_DIR = ".local/generated-images";
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const MAX_RETRIES = 2;
const ASPECT_RATIOS = new Set(["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]);
const IMAGE_SIZES = new Set(["1K", "2K", "4K"]);
const EXT_BY_MIME = {
  "image/png": "png",
  "image/jpeg": "jpg",
  "image/webp": "webp",
};
const MIME_BY_EXT = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
};
const LOADED_ENV_FILES = loadSkillEnvFiles();

const HELP = `
Gemini image CLI (Nano Banana) for app-icon-studio.

Uses GEMINI_API_KEY by default and calls the Gemini generateContent API directly.
The script loads skill-specific env files before reading process env:
  ~/.claude/app-icon-studio/.env
  ./.claude/app-icon-studio.env
The project file loads second and overrides the global file.
The default model is ${DEFAULT_MODEL} (Nano Banana Pro), the latest Gemini image
model documented when this script was added. If the default model returns 404,
run the models command and pick the newest image model:
  node scripts/gemini-image.mjs models
Docs: https://ai.google.dev/gemini-api/docs/image-generation

Usage:
  node scripts/gemini-image.mjs generate --prompt "..." --out icons/myapp/round-1
  node scripts/gemini-image.mjs generate --prompt-file prompt.txt --n 2 --name candidate
  echo "prompt text" | node scripts/gemini-image.mjs generate --stdin
  node scripts/gemini-image.mjs edit --image input.png --prompt "make the mark 30% larger"
  node scripts/gemini-image.mjs config

Commands:
  generate    Generate image(s) from text. This is the default command.
  edit        Edit or combine source images (same API, images attached as input).
  models      List available Gemini image models.
  config      Print env-file/key presence status without revealing secrets.
  help        Print this help.

Required:
  GEMINI_API_KEY must be present in a skill env file, or pass --api-key-env NAME.
  A prompt is required via --prompt, --prompt-file, --stdin, or positional text.
  The edit command also requires at least one --image PATH.

Options:
  --model MODEL              Default: ${DEFAULT_MODEL}
  --prompt TEXT              Text prompt.
  --prompt-file PATH         Read prompt text from a file.
  --stdin                    Read prompt text from standard input.
  --out PATH                 Output file or directory. Default: ${DEFAULT_OUT_DIR}
  --name SLUG                Base filename when --out is a directory.
  --n INT                    Number of images, 1-8 (parallel requests). Default: 1.
  --aspect-ratio VALUE       ${[...ASPECT_RATIOS].join(", ")}. Default: model default (1:1 for icons — set it explicitly).
  --image-size VALUE         1K, 2K, 4K. Supported by ${DEFAULT_MODEL}; older image
                             models reject it — omit for gemini-2.5-flash-image.
  --image PATH               Input image (edit/reference). Repeatable, up to 14.
  --api-base URL             Default: ${DEFAULT_API_BASE}
  --api-key-env NAME         Default: GEMINI_API_KEY
  --timeout-ms INT           Default: ${DEFAULT_TIMEOUT_MS}
  --metadata                 Write sidecar JSON metadata. Default.
  --no-metadata              Skip sidecar metadata.
  --json                     Print machine-readable summary to stdout.
  --quiet                    Only print saved paths unless --json is used.
  --dry-run                  Print request payload without calling the API.
  --help                     Print this help.

Notes:
  1. Nano Banana responds to conversational, art-directed prompts. For app icons,
     structured JSON briefs also work well — see the skill's prompt-recipes reference.
  2. Each request returns one image; --n fans out parallel requests.
  3. Requests can take 20-90s each. Do not lower --timeout-ms below 120000.
  4. Do not print GEMINI_API_KEY or write it into metadata.
`;

class UsageError extends Error {}

async function main(argv) {
  const parsed = parseArgs(argv);
  if (parsed.options.help || parsed.command === "help") {
    console.log(HELP.trimStart());
    return;
  }

  const command = parsed.command ?? "generate";
  if (!["generate", "edit", "models", "config"].includes(command)) {
    throw new UsageError(`Unknown command "${command}". Run with --help.`);
  }

  const options = normalizeOptions(parsed.options);
  if (command === "config") {
    printConfig(options);
    return;
  }
  if (command === "models") {
    const apiKey = readApiKey(options.apiKeyEnv);
    const models = await listModels(options, apiKey);
    printModels(models, options);
    return;
  }

  const prompt = await readPrompt(options, parsed.positionals);
  if (!prompt) {
    throw new UsageError("Prompt is required. Use --prompt, --prompt-file, --stdin, or positional text.");
  }
  validateOptions(command, options);

  const parts = await buildParts(prompt, options.image);
  const request = buildRequestPayload(parts, options);

  if (options.dryRun) {
    printJson({ command, endpoint: endpointFor(options), request: redactInlineData(request) });
    return;
  }

  const apiKey = readApiKey(options.apiKeyEnv);
  const responses = await Promise.all(
    Array.from({ length: options.n }, () => callApiWithRetry(request, options, apiKey)),
  );

  const saved = await saveImages(responses, { command, request, prompt, options });
  printResult(saved, options);
}

function parseArgs(argv) {
  const options = {};
  const positionals = [];
  let command = null;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!command && !arg.startsWith("-") && ["generate", "edit", "models", "config", "help"].includes(arg)) {
      command = arg;
      continue;
    }
    if (arg === "--") {
      positionals.push(...argv.slice(index + 1));
      break;
    }
    if (arg.startsWith("--")) {
      const eq = arg.indexOf("=");
      const key = toCamel(eq === -1 ? arg.slice(2) : arg.slice(2, eq));
      const inlineValue = eq === -1 ? null : arg.slice(eq + 1);
      if (key.startsWith("no") && key.length > 2) {
        const positive = key[2].toLowerCase() + key.slice(3);
        if (!ALLOWED_OPTIONS.has(positive)) {
          throw new UsageError(`Unknown option --${fromCamel(key)}.`);
        }
        options[positive] = false;
        continue;
      }
      if (!ALLOWED_OPTIONS.has(key)) {
        throw new UsageError(`Unknown option --${fromCamel(key)}.`);
      }
      if (BOOLEAN_FLAGS.has(key)) {
        options[key] = inlineValue === null ? true : parseBoolean(inlineValue, key);
        continue;
      }
      const value = inlineValue ?? argv[index + 1];
      if (value === undefined || value.startsWith("--")) {
        throw new UsageError(`Missing value for --${fromCamel(key)}.`);
      }
      index += inlineValue === null ? 1 : 0;
      appendOption(options, key, value);
      continue;
    }
    positionals.push(arg);
  }

  return { command, options, positionals };
}

const BOOLEAN_FLAGS = new Set(["dryRun", "help", "json", "metadata", "quiet", "stdin"]);

const ALLOWED_OPTIONS = new Set([
  ...BOOLEAN_FLAGS,
  "apiBase",
  "apiKeyEnv",
  "aspectRatio",
  "image",
  "imageSize",
  "model",
  "n",
  "name",
  "out",
  "prompt",
  "promptFile",
  "timeoutMs",
]);

function appendOption(options, key, value) {
  if (key === "image") {
    options.image = [...(options.image ?? []), value];
    return;
  }
  options[key] = value;
}

function normalizeOptions(raw) {
  const options = {
    apiBase: DEFAULT_API_BASE,
    apiKeyEnv: "GEMINI_API_KEY",
    aspectRatio: undefined,
    dryRun: false,
    image: [],
    imageSize: undefined,
    metadata: true,
    model: DEFAULT_MODEL,
    n: 1,
    out: DEFAULT_OUT_DIR,
    quiet: false,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    ...raw,
  };

  options.n = toInteger(options.n, "n");
  options.timeoutMs = toInteger(options.timeoutMs, "timeout-ms");
  options.apiBase = String(options.apiBase).replace(/\/+$/, "");
  return options;
}

async function readPrompt(options, positionals) {
  const chunks = [];
  if (options.prompt) {
    chunks.push(String(options.prompt));
  }
  if (options.promptFile) {
    chunks.push(await readFile(options.promptFile, "utf8"));
  }
  if (options.stdin) {
    chunks.push(await readStdin());
  }
  if (positionals.length > 0) {
    chunks.push(positionals.join(" "));
  }
  return chunks.join("\n\n").trim();
}

function validateOptions(command, options) {
  if (options.n < 1 || options.n > 8) {
    throw new UsageError("--n must be between 1 and 8.");
  }
  if (options.timeoutMs < 1000) {
    throw new UsageError("--timeout-ms must be at least 1000.");
  }
  if (options.aspectRatio && !ASPECT_RATIOS.has(options.aspectRatio)) {
    throw new UsageError(`--aspect-ratio must be one of: ${[...ASPECT_RATIOS].join(", ")}.`);
  }
  if (options.imageSize && !IMAGE_SIZES.has(options.imageSize)) {
    throw new UsageError("--image-size must be one of: 1K, 2K, 4K.");
  }
  if (command === "edit" && options.image.length === 0) {
    throw new UsageError("The edit command requires at least one --image PATH.");
  }
  if (options.image.length > 14) {
    throw new UsageError("Gemini requests support up to 14 --image inputs.");
  }
}

async function buildParts(prompt, imagePaths) {
  const parts = [];
  for (const imagePath of imagePaths) {
    const bytes = await readFile(imagePath);
    const mimeType = MIME_BY_EXT[path.extname(imagePath).toLowerCase()] ?? "application/octet-stream";
    parts.push({ inline_data: { mime_type: mimeType, data: bytes.toString("base64") } });
  }
  parts.push({ text: prompt });
  return parts;
}

function buildRequestPayload(parts, options) {
  const imageConfig = compact({
    aspectRatio: options.aspectRatio,
    imageSize: options.imageSize,
  });
  const generationConfig = compact({
    responseModalities: ["TEXT", "IMAGE"],
    imageConfig: Object.keys(imageConfig).length > 0 ? imageConfig : undefined,
  });
  return {
    contents: [{ role: "user", parts }],
    generationConfig,
  };
}

async function callApiWithRetry(request, options, apiKey) {
  let lastError;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt += 1) {
    try {
      return await callApi(request, options, apiKey);
    } catch (error) {
      lastError = error;
      if (!isRetryable(error) || attempt === MAX_RETRIES) {
        throw error;
      }
      const delayMs = 2000 * 2 ** attempt;
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  throw lastError;
}

function isRetryable(error) {
  const status = error?.status;
  return status === 429 || status === 500 || status === 503;
}

async function callApi(request, options, apiKey) {
  const response = await requestWithTimeout(endpointFor(options), {
    method: "POST",
    headers: {
      "x-goog-api-key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  }, options.timeoutMs);

  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Gemini API returned non-JSON response (${response.status}): ${text.slice(0, 500)}`);
  }
  if (!response.ok) {
    const message = data?.error?.message ?? JSON.stringify(data);
    const error = new Error(`Gemini API error ${response.status}: ${message}`);
    error.status = response.status;
    throw error;
  }

  const blockReason = data?.promptFeedback?.blockReason;
  if (blockReason) {
    throw new Error(`Gemini blocked the prompt: ${blockReason}. Rephrase and retry.`);
  }

  const candidate = data?.candidates?.[0];
  const parts = candidate?.content?.parts ?? [];
  const images = parts
    .map((part) => part.inlineData ?? part.inline_data)
    .filter((inline) => inline?.data);
  if (images.length === 0) {
    const textParts = parts.filter((part) => part.text).map((part) => part.text).join("\n");
    const finishReason = candidate?.finishReason ?? "unknown";
    throw new Error(
      `Gemini response contained no image (finishReason: ${finishReason}).`
      + (textParts ? ` Model said: ${textParts.slice(0, 300)}` : ""),
    );
  }

  return {
    images,
    text: parts.filter((part) => part.text).map((part) => part.text).join("\n") || undefined,
    finishReason: candidate?.finishReason,
    usage: data?.usageMetadata,
  };
}

async function requestWithTimeout(url, init, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error(`Timed out after ${timeoutMs}ms`)), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function saveImages(responses, context) {
  const { command, request, prompt, options } = context;
  const flat = [];
  for (const response of responses) {
    for (const image of response.images) {
      flat.push({ image, response });
    }
  }
  if (flat.length === 0) {
    throw new Error("Gemini responses contained no image data.");
  }

  const format = EXT_BY_MIME[flat[0].image.mime_type ?? flat[0].image.mimeType] ?? "png";
  const paths = outputPaths(options.out, options.name, prompt, format, flat.length);
  const saved = [];

  for (let index = 0; index < flat.length; index += 1) {
    const target = paths[index];
    await mkdir(path.dirname(target), { recursive: true });
    await writeFile(target, Buffer.from(flat[index].image.data, "base64"));
    saved.push(path.resolve(target));
  }

  let metadataPath = null;
  if (options.metadata) {
    metadataPath = metadataOutputPath(paths[0]);
    const metadata = {
      generatedAt: new Date().toISOString(),
      command,
      endpoint: endpointFor(options),
      request: redactInlineData(request),
      responses: responses.map((response) => ({
        text: response.text,
        finishReason: response.finishReason,
        usage: response.usage,
      })),
      files: saved,
      docs: "https://ai.google.dev/gemini-api/docs/image-generation",
    };
    await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
  }

  return { files: saved, metadata: metadataPath ? path.resolve(metadataPath) : null };
}

function outputPaths(out, name, prompt, format, count) {
  const parsed = path.parse(out);
  const outLooksLikeFile = parsed.ext.length > 0;
  const baseName = sanitizeSlug(name ?? prompt.slice(0, 72)) || "gemini-image";
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "Z");

  if (outLooksLikeFile) {
    const base = path.join(parsed.dir, parsed.name);
    return Array.from({ length: count }, (_, index) => (
      count === 1 ? out : `${base}-${String(index + 1).padStart(2, "0")}${parsed.ext}`
    ));
  }

  return Array.from({ length: count }, (_, index) => {
    const suffix = count === 1 ? "" : `-${String(index + 1).padStart(2, "0")}`;
    return path.join(out, `${stamp}-${baseName}${suffix}.${format}`);
  });
}

function metadataOutputPath(firstImagePath) {
  const parsed = path.parse(firstImagePath);
  return path.join(parsed.dir, `${parsed.name}.metadata.json`);
}

function redactInlineData(value) {
  if (Array.isArray(value)) {
    return value.map(redactInlineData);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [
      key,
      key === "data" && typeof item === "string" && item.length > 256
        ? `<omitted:${item.length}>`
        : redactInlineData(item),
    ]));
  }
  return value;
}

function endpointFor(options) {
  return `${options.apiBase}/models/${options.model}:generateContent`;
}

function readApiKey(envName) {
  const value = process.env[envName];
  if (!value) {
    throw new UsageError(
      `${envName} is not set. Add it to ~/.claude/app-icon-studio/.env `
      + "or ./.claude/app-icon-studio.env before running this script.",
    );
  }
  return value;
}

async function listModels(options, apiKey) {
  const response = await requestWithTimeout(`${options.apiBase}/models`, {
    headers: { "x-goog-api-key": apiKey },
  }, options.timeoutMs);

  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`Gemini API returned non-JSON response (${response.status}): ${text.slice(0, 500)}`);
  }
  if (!response.ok) {
    const message = data?.error?.message ?? JSON.stringify(data);
    const error = new Error(`Gemini API error ${response.status}: ${message}`);
    error.status = response.status;
    throw error;
  }
  return data?.models ?? [];
}

function printModels(models, options) {
  const imageModels = models.filter((model) => /image/i.test(JSON.stringify(model)));
  if (options.json) {
    printJson({ models: imageModels });
    return;
  }
  for (const model of imageModels) {
    console.log(model.name);
  }
}

function printConfig(options) {
  printJson({
    success: true,
    command: "config",
    api_key_env: options.apiKeyEnv,
    api_key_present: Boolean(process.env[options.apiKeyEnv]),
    env_files: describeSkillEnvFiles(LOADED_ENV_FILES),
  });
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString("utf8");
}

function printResult(saved, options) {
  if (options.json) {
    printJson(saved);
    return;
  }
  for (const file of saved.files) {
    console.log(file);
  }
  if (saved.metadata && !options.quiet) {
    console.log(`metadata: ${saved.metadata}`);
  }
}

function compact(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== undefined && item !== ""));
}

function toInteger(value, label) {
  const integer = Number.parseInt(String(value), 10);
  if (!Number.isFinite(integer) || String(integer) !== String(value)) {
    throw new UsageError(`--${label} must be an integer.`);
  }
  return integer;
}

function parseBoolean(value, key) {
  if (["true", "1", "yes"].includes(String(value).toLowerCase())) {
    return true;
  }
  if (["false", "0", "no"].includes(String(value).toLowerCase())) {
    return false;
  }
  throw new UsageError(`--${fromCamel(key)} must be true or false when a value is provided.`);
}

function toCamel(value) {
  return value.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

function fromCamel(value) {
  return value.replace(/[A-Z]/g, (letter) => `-${letter.toLowerCase()}`);
}

function sanitizeSlug(value) {
  return String(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 72);
}

function printJson(value) {
  console.log(JSON.stringify(value, null, 2));
}

main(process.argv.slice(2)).catch((error) => {
  if (error instanceof UsageError) {
    console.error(`Usage error: ${error.message}`);
    console.error("Run: node scripts/gemini-image.mjs --help");
    process.exit(2);
  }
  console.error(error?.stack ?? error);
  process.exit(1);
});
