#!/usr/bin/env node
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const DEFAULT_MODEL = "gpt-image-2";
const DEFAULT_API_BASE = "https://api.openai.com/v1";
const DEFAULT_OUT_DIR = ".local/generated-images";
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const FORMATS = new Set(["png", "jpeg", "webp"]);
const QUALITIES = new Set(["auto", "low", "medium", "high", "standard", "hd"]);
const BACKGROUNDS = new Set(["auto", "opaque", "transparent"]);
const MODERATION = new Set(["auto", "low"]);
const INPUT_FIDELITIES = new Set(["low", "high"]);
const EXT_BY_FORMAT = { png: "png", jpeg: "jpg", webp: "webp" };
const MIME_BY_EXT = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
};

const HELP = `
OpenAI image CLI for Orfea landing-page asset work.

Uses OPENAI_API_KEY by default and calls the current GPT Image API directly.
The default model is ${DEFAULT_MODEL}, the latest GPT Image model documented by OpenAI
when this script was added. Re-check official docs before changing that default:
https://developers.openai.com/api/docs/guides/image-generation

Usage:
  npm run image:generate -- --prompt "warm editorial photo of ..."
  node scripts/openai-image.mjs generate --prompt "..." --out .local/generated-images
  echo "prompt text" | node scripts/openai-image.mjs generate --stdin --size 1536x1024
  node scripts/openai-image.mjs edit --image input.jpg --prompt "make it feel more premium"

Commands:
  generate    Generate image(s) from text. This is the default command.
  edit        Edit or extend one or more source images.
  help        Print this help.

Required:
  OPENAI_API_KEY must be exported in the shell, or pass --api-key-env NAME.
  A prompt is required via --prompt, --prompt-file, --stdin, or positional text.
  The edit command also requires at least one --image PATH.

Generation options:
  --model MODEL              Default: ${DEFAULT_MODEL}
  --prompt TEXT              Text prompt.
  --prompt-file PATH         Read prompt text from a file.
  --stdin                    Read prompt text from standard input.
  --out PATH                 Output file or directory. Default: ${DEFAULT_OUT_DIR}
  --name SLUG                Base filename when --out is a directory.
  --n INT                    Number of images, 1-10. Default: 1.
  --size SIZE                Examples: auto, 1024x1024, 1536x1024, 1024x1536,
                             or custom WIDTHxHEIGHT for gpt-image-2.
  --quality VALUE            auto, low, medium, high. Legacy: standard, hd.
  --format VALUE             png, jpeg, webp. GPT Image models return base64.
  --compression INT          0-100, only for jpeg/webp.
  --background VALUE         auto, opaque, transparent. gpt-image-2 does not
                             support transparent backgrounds.
  --moderation VALUE         auto or low.
  --user VALUE               Stable end-user id for abuse monitoring.
  --stream                   Request image streaming.
  --partial-images INT       0-3 partial images when streaming.
  --save-partials            Save streamed partial images as separate files.
  --style VALUE              Legacy dall-e-3 only: vivid or natural.
  --response-format VALUE    Legacy dall-e-2/dall-e-3 only: url or b64_json.

Edit-only options:
  --image PATH               Source image. Repeat up to 16 times for GPT Image.
  --mask PATH                PNG alpha mask applied to the first source image.
  --input-fidelity VALUE     low or high. Supported by GPT image edit models.

Operational options:
  --api-base URL             Default: ${DEFAULT_API_BASE}
  --api-key-env NAME         Default: OPENAI_API_KEY
  --timeout-ms INT           Default: ${DEFAULT_TIMEOUT_MS}
  --metadata                 Write sidecar JSON metadata. Default.
  --no-metadata              Skip sidecar metadata.
  --json                    Print machine-readable summary to stdout.
  --quiet                   Only print saved paths unless --json is used.
  --dry-run                 Print request payload without calling the API.
  --help                    Print this help.

Agent guidance for landing-page assets:
  1. Read docs/image-generation-cli.md before generating production assets.
  2. Use prompts that read like a creative brief plus photography brief:
     subject, scene, medium, composition, lighting, crop, people/object
     interactions, brand mood, and hard exclusions.
  3. Use --quality low only for API smoke tests or rough style exploration.
     Use --quality medium for real candidates and high for final assets.
  4. Avoid close-up hands/phones/QR cards unless necessary. If visible, specify
     exact hand/object geometry and reject distorted fingers or impossible poses.
  5. For web heroes, start with --size 1536x1024. Use 2048x1152 or 2560x1440
     for widescreen finals after a direction is chosen.
  6. Prefer --format jpeg --compression 85 for photographic web assets.
     Use png only for graphics or when lossless output matters.
  7. Save drafts under .local/generated-images. Move only chosen final assets
     into tracked app asset folders.
  8. Do not print OPENAI_API_KEY or write it into metadata.
`;

class UsageError extends Error {}

async function main(argv) {
  const parsed = parseArgs(argv);
  if (parsed.options.help || parsed.command === "help") {
    console.log(HELP.trimStart());
    return;
  }

  const command = parsed.command ?? "generate";
  if (!["generate", "edit"].includes(command)) {
    throw new UsageError(`Unknown command "${command}". Run with --help.`);
  }

  const options = normalizeOptions(parsed.options);
  const prompt = await readPrompt(options, parsed.positionals);
  if (!prompt) {
    throw new UsageError("Prompt is required. Use --prompt, --prompt-file, --stdin, or positional text.");
  }

  validateSharedOptions(options);
  if (command === "edit") {
    validateEditOptions(options);
  }

  const request = buildRequestPayload(command, options, prompt);
  if (options.dryRun) {
    printJson({ command, endpoint: endpointFor(command, options.apiBase), request });
    return;
  }

  const apiKey = readApiKey(options.apiKeyEnv);
  const result = command === "generate"
    ? await callGenerationApi(request, options, apiKey)
    : await callEditApi(request, options, apiKey);

  const saved = await saveImages(result, { command, request, prompt, options });
  printResult(saved, options);
}

function parseArgs(argv) {
  const options = {};
  const positionals = [];
  let command = null;

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (!command && !arg.startsWith("-") && ["generate", "edit", "help"].includes(arg)) {
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

const BOOLEAN_FLAGS = new Set([
  "dryRun",
  "help",
  "json",
  "metadata",
  "quiet",
  "savePartials",
  "stdin",
  "stream",
]);

const ALLOWED_OPTIONS = new Set([
  ...BOOLEAN_FLAGS,
  "apiBase",
  "apiKeyEnv",
  "background",
  "compression",
  "format",
  "image",
  "inputFidelity",
  "mask",
  "model",
  "moderation",
  "n",
  "name",
  "out",
  "partialImages",
  "prompt",
  "promptFile",
  "quality",
  "responseFormat",
  "size",
  "style",
  "timeoutMs",
  "user",
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
    apiKeyEnv: "OPENAI_API_KEY",
    background: undefined,
    compression: undefined,
    dryRun: false,
    format: undefined,
    image: [],
    metadata: true,
    model: DEFAULT_MODEL,
    n: 1,
    out: DEFAULT_OUT_DIR,
    partialImages: undefined,
    quality: undefined,
    quiet: false,
    savePartials: false,
    size: undefined,
    stream: false,
    timeoutMs: DEFAULT_TIMEOUT_MS,
    ...raw,
  };

  options.n = toInteger(options.n, "n");
  options.timeoutMs = toInteger(options.timeoutMs, "timeout-ms");
  if (options.compression !== undefined) {
    options.compression = toInteger(options.compression, "compression");
  }
  if (options.partialImages !== undefined) {
    options.partialImages = toInteger(options.partialImages, "partial-images");
  }
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

function validateSharedOptions(options) {
  if (options.n < 1 || options.n > 10) {
    throw new UsageError("--n must be between 1 and 10.");
  }
  if (options.timeoutMs < 1000) {
    throw new UsageError("--timeout-ms must be at least 1000.");
  }
  if (options.format && !FORMATS.has(options.format)) {
    throw new UsageError("--format must be one of: png, jpeg, webp.");
  }
  if (options.quality && !QUALITIES.has(options.quality)) {
    throw new UsageError("--quality must be one of: auto, low, medium, high, standard, hd.");
  }
  if (options.background && !BACKGROUNDS.has(options.background)) {
    throw new UsageError("--background must be one of: auto, opaque, transparent.");
  }
  if (options.moderation && !MODERATION.has(options.moderation)) {
    throw new UsageError("--moderation must be one of: auto, low.");
  }
  if (options.compression !== undefined && (options.compression < 0 || options.compression > 100)) {
    throw new UsageError("--compression must be between 0 and 100.");
  }
  if (options.compression !== undefined && options.format === "png") {
    throw new UsageError("--compression is only valid with --format jpeg or --format webp.");
  }
  if (options.partialImages !== undefined && (options.partialImages < 0 || options.partialImages > 3)) {
    throw new UsageError("--partial-images must be between 0 and 3.");
  }
  if (options.partialImages !== undefined && !options.stream) {
    throw new UsageError("--partial-images requires --stream.");
  }
  if (options.background === "transparent" && options.model.startsWith("gpt-image-2")) {
    throw new UsageError("gpt-image-2 does not support transparent backgrounds. Use --background auto or opaque.");
  }
  if (options.size) {
    validateSize(options.size, options.model);
  }
}

function validateEditOptions(options) {
  if (!options.image || options.image.length === 0) {
    throw new UsageError("The edit command requires at least one --image PATH.");
  }
  if (options.image.length > 16) {
    throw new UsageError("GPT Image edit requests support up to 16 --image inputs.");
  }
  if (options.inputFidelity && !INPUT_FIDELITIES.has(options.inputFidelity)) {
    throw new UsageError("--input-fidelity must be low or high.");
  }
}

function validateSize(size, model) {
  if (size === "auto") {
    return;
  }
  const match = /^(\d+)x(\d+)$/.exec(size);
  if (!match) {
    throw new UsageError("--size must be auto or WIDTHxHEIGHT, for example 1536x1024.");
  }

  if (!model.startsWith("gpt-image-2")) {
    return;
  }

  const width = Number(match[1]);
  const height = Number(match[2]);
  const longEdge = Math.max(width, height);
  const shortEdge = Math.min(width, height);
  const pixels = width * height;
  if (width % 16 !== 0 || height % 16 !== 0) {
    throw new UsageError("For gpt-image-2, both --size edges must be divisible by 16.");
  }
  if (longEdge > 3840) {
    throw new UsageError("For gpt-image-2, the longest --size edge must be <= 3840.");
  }
  if (longEdge / shortEdge > 3) {
    throw new UsageError("For gpt-image-2, --size aspect ratio must not exceed 3:1.");
  }
  if (pixels < 655_360 || pixels > 8_294_400) {
    throw new UsageError("For gpt-image-2, --size must be between 655360 and 8294400 total pixels.");
  }
}

function buildRequestPayload(command, options, prompt) {
  const request = compact({
    model: options.model,
    prompt,
    n: options.n,
    size: options.size,
    quality: options.quality,
    output_format: options.format,
    output_compression: options.compression,
    background: options.background,
    moderation: command === "generate" ? options.moderation : undefined,
    partial_images: options.partialImages,
    response_format: options.responseFormat,
    stream: options.stream || undefined,
    style: command === "generate" ? options.style : undefined,
    user: options.user,
  });

  if (command === "edit") {
    request.image = options.image;
    request.mask = options.mask;
    request.input_fidelity = options.inputFidelity;
  }
  return compact(request);
}

async function callGenerationApi(request, options, apiKey) {
  const body = JSON.stringify(request);
  const response = await requestWithTimeout(endpointFor("generate", options.apiBase), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body,
  }, options.timeoutMs);

  if (request.stream) {
    return parseImageStream(response, options);
  }

  return parseJsonResponse(response);
}

async function callEditApi(request, options, apiKey) {
  const form = new FormData();
  for (const [key, value] of Object.entries(request)) {
    if (value === undefined || key === "image" || key === "mask") {
      continue;
    }
    form.append(key, String(value));
  }

  for (const [index, imagePath] of request.image.entries()) {
    const fieldName = request.image.length === 1 ? "image" : "image[]";
    form.append(fieldName, await fileBlob(imagePath), path.basename(imagePath));
    if (index === 0 && request.mask) {
      form.append("mask", await fileBlob(request.mask), path.basename(request.mask));
    }
  }

  const response = await requestWithTimeout(endpointFor("edit", options.apiBase), {
    method: "POST",
    headers: { Authorization: `Bearer ${apiKey}` },
    body: form,
  }, options.timeoutMs);

  if (request.stream) {
    return parseImageStream(response, options);
  }

  return parseJsonResponse(response);
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

async function parseJsonResponse(response) {
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(`OpenAI API returned non-JSON response (${response.status}): ${text.slice(0, 500)}`);
  }
  if (!response.ok) {
    const message = data?.error?.message ?? JSON.stringify(data);
    throw new Error(`OpenAI API error ${response.status}: ${message}`);
  }
  return data;
}

async function parseImageStream(response, options) {
  if (!response.ok) {
    return parseJsonResponse(response);
  }
  if (!response.body) {
    throw new Error("OpenAI API returned an empty stream.");
  }

  const decoder = new TextDecoder();
  let buffer = "";
  const events = [];
  for await (const chunk of response.body) {
    buffer += decoder.decode(chunk, { stream: true });
    let boundary = buffer.indexOf("\n\n");
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      handleStreamFrame(frame, events, options);
      boundary = buffer.indexOf("\n\n");
    }
  }
  if (buffer.trim()) {
    handleStreamFrame(buffer, events, options);
  }

  const completed = [...events].reverse().find((event) => event.type?.endsWith(".completed"));
  if (!completed?.b64_json) {
    throw new Error("Image stream ended without a completed image event.");
  }

  return {
    created: completed.created_at ?? Math.floor(Date.now() / 1000),
    data: [{ b64_json: completed.b64_json }],
    output_format: completed.output_format,
    quality: completed.quality,
    size: completed.size,
    usage: completed.usage,
    stream_events: options.savePartials ? events : redactStreamEvents(events),
  };
}

function handleStreamFrame(frame, events, options) {
  const lines = frame.split(/\r?\n/);
  const dataLines = lines
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim());
  if (dataLines.length === 0) {
    return;
  }
  const data = dataLines.join("\n");
  if (data === "[DONE]") {
    return;
  }
  let event;
  try {
    event = JSON.parse(data);
  } catch {
    return;
  }
  events.push(event);
}

function redactStreamEvents(events) {
  return events.map((event) => {
    if (!event.b64_json) {
      return event;
    }
    return { ...event, b64_json: `<omitted:${event.b64_json.length}>` };
  });
}

async function saveImages(result, context) {
  const { command, request, prompt, options } = context;
  const data = Array.isArray(result.data) ? result.data : [];
  if (data.length === 0) {
    throw new Error("OpenAI response contained no image data.");
  }

  const format = result.output_format ?? request.output_format ?? "png";
  const paths = outputPaths(options.out, options.name, prompt, format, data.length);
  const saved = [];

  for (let index = 0; index < data.length; index += 1) {
    const item = data[index];
    const target = paths[index];
    await mkdir(path.dirname(target), { recursive: true });

    if (item.b64_json) {
      await writeFile(target, Buffer.from(item.b64_json, "base64"));
    } else if (item.url) {
      await downloadFile(item.url, target, options.timeoutMs);
    } else {
      throw new Error(`Image ${index + 1} has neither b64_json nor url.`);
    }
    saved.push(path.resolve(target));
  }

  if (options.savePartials && Array.isArray(result.stream_events)) {
    await savePartials(result.stream_events, paths[0], format);
  }

  let metadataPath = null;
  if (options.metadata) {
    metadataPath = metadataOutputPath(paths[0]);
    const metadata = {
      generatedAt: new Date().toISOString(),
      command,
      endpoint: endpointFor(command, options.apiBase),
      request,
      response: sanitizeResponse(result),
      files: saved,
      docs: "https://developers.openai.com/api/docs/guides/image-generation",
    };
    await writeFile(metadataPath, `${JSON.stringify(metadata, null, 2)}\n`);
  }

  return { files: saved, metadata: metadataPath ? path.resolve(metadataPath) : null, response: sanitizeResponse(result) };
}

async function savePartials(events, finalPath, format) {
  const base = finalPath.replace(/\.[^.]+$/, "");
  const ext = EXT_BY_FORMAT[format] ?? "png";
  const partials = events.filter((event) => event.type?.endsWith(".partial_image") && event.b64_json);
  for (const event of partials) {
    const index = event.partial_image_index ?? partials.indexOf(event);
    const partialPath = `${base}.partial-${index}.${ext}`;
    await writeFile(partialPath, Buffer.from(event.b64_json, "base64"));
  }
}

function outputPaths(out, name, prompt, format, count) {
  const ext = EXT_BY_FORMAT[format] ?? "png";
  const parsed = path.parse(out);
  const outLooksLikeFile = parsed.ext.length > 0;
  const baseName = sanitizeSlug(name ?? prompt.slice(0, 72)) || "openai-image";
  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\..+$/, "Z");

  if (outLooksLikeFile) {
    const base = path.join(parsed.dir, parsed.name);
    return Array.from({ length: count }, (_, index) => (
      count === 1 ? out : `${base}-${String(index + 1).padStart(2, "0")}${parsed.ext}`
    ));
  }

  return Array.from({ length: count }, (_, index) => {
    const suffix = count === 1 ? "" : `-${String(index + 1).padStart(2, "0")}`;
    return path.join(out, `${stamp}-${baseName}${suffix}.${ext}`);
  });
}

function metadataOutputPath(firstImagePath) {
  const parsed = path.parse(firstImagePath);
  return path.join(parsed.dir, `${parsed.name}.metadata.json`);
}

async function downloadFile(url, target, timeoutMs) {
  const response = await requestWithTimeout(url, {}, timeoutMs);
  if (!response.ok) {
    throw new Error(`Failed to download image URL (${response.status}).`);
  }
  await writeFile(target, Buffer.from(await response.arrayBuffer()));
}

function sanitizeResponse(value) {
  if (Array.isArray(value)) {
    return value.map(sanitizeResponse);
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [
      key,
      key === "b64_json" && typeof item === "string" ? `<omitted:${item.length}>` : sanitizeResponse(item),
    ]));
  }
  return value;
}

async function fileBlob(filePath) {
  const bytes = await readFile(filePath);
  const type = MIME_BY_EXT[path.extname(filePath).toLowerCase()] ?? "application/octet-stream";
  return new Blob([bytes], { type });
}

function endpointFor(command, apiBase) {
  return `${apiBase}${command === "edit" ? "/images/edits" : "/images/generations"}`;
}

function readApiKey(envName) {
  const value = process.env[envName];
  if (!value) {
    throw new UsageError(`${envName} is not set. Export your OpenAI API key before running this script.`);
  }
  return value;
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
    console.error("Run: node scripts/openai-image.mjs --help");
    process.exit(2);
  }
  console.error(error?.stack ?? error);
  process.exit(1);
});
