#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const crypto = require('crypto');

// ── Colors ──────────────────────────────────────────────────────────────────
const green = '\x1b[32m';
const yellow = '\x1b[33m';
const dim = '\x1b[2m';
const reset = '\x1b[0m';

// ── CLI parsing ─────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
const has = (long, short) => args.includes(long) || (short && args.includes(short));

const hasGlobal = has('--global', '-g');
const hasCopy = has('--copy');
const hasForce = has('--force', '-f');
const hasHelp = has('--help', '-h');
const hasUninstall = has('--uninstall');

// Hidden backward-compat flags (no-ops)
// --local / -l is the default scope, --link is the default mode
const _hasLocal = has('--local', '-l');
const _hasLink = has('--link');

if (hasHelp) {
  console.log(`
Usage: ${process.argv[1]} [options]

Installs skills, agents, commands, and references for Claude Code
by creating symlinks from your project (or global ~/.claude/) to this toolkit.

Options:
  -g, --global   Install to ~/.claude/ (default: current project ./.claude/)
      --copy     Copy files instead of symlinking
  -f, --force    Overwrite modified files without prompting
      --uninstall  Remove all toolkit files from the target scope
  -h, --help     Show this help message

Examples:
  # Clone the toolkit once
  git clone https://github.com/rolandtolnay/llm-toolkit.git ~/toolkits/llm-toolkit

  # Install into a project (creates symlinks in ./.claude/)
  cd your-project
  ~/toolkits/llm-toolkit/install.js

  # Install globally (creates symlinks in ~/.claude/)
  ~/toolkits/llm-toolkit/install.js --global

  # Copy files instead of symlinking (e.g. for team sharing via git)
  ~/toolkits/llm-toolkit/install.js --copy

  # Uninstall from a project
  cd your-project
  ~/toolkits/llm-toolkit/install.js --uninstall

  # Uninstall globally
  ~/toolkits/llm-toolkit/install.js --uninstall --global
`);
  process.exit(0);
}

if (hasGlobal && _hasLocal) {
  console.error('Error: cannot specify both --global and --local');
  process.exit(1);
}
if (!hasCopy && process.platform === 'win32') {
  console.error('Error: symlinks require admin privileges on Windows. Use --copy instead.');
  process.exit(1);
}

const SCRIPT_DIR = __dirname;
const SCRIPT_DIR_REAL = fs.realpathSync(SCRIPT_DIR);
const MANIFEST_VERSION = '1.0.0';
const SKIP_PATTERNS = ['.DS_Store', '__pycache__', '.git'];

// Safety check: don't install into the toolkit repo itself
if (!hasGlobal && !hasUninstall && fs.realpathSync(process.cwd()) === SCRIPT_DIR_REAL) {
  console.error('Error: Run this from your project directory, not from the toolkit repo.');
  console.error('  cd your-project');
  console.error(`  ${process.argv[1]}`);
  process.exit(1);
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function computeChecksum(content) {
  return crypto.createHash('sha256').update(content).digest('hex').slice(0, 16);
}

function isInteractive() {
  return process.stdin.isTTY && process.stdout.isTTY;
}

function normalizeRelPath(rel) {
  return rel.replace(/\\/g, '/');
}

function relToFsPath(rel) {
  return normalizeRelPath(rel).split('/').join(path.sep);
}

function getSkillNameFromRel(rel) {
  const normalized = normalizeRelPath(rel);
  if (!normalized.startsWith('skills/')) return null;
  const parts = normalized.split('/');
  return parts[1] || null;
}

function getKeptSkillDirs(keep) {
  const keptSkillDirs = new Set();
  for (const rel of keep) {
    const normalized = normalizeRelPath(rel);
    const skillName = getSkillNameFromRel(normalized);
    if (!skillName) continue;
    if (normalized.split('/').length === 2) {
      keptSkillDirs.add(skillName);
    }
  }
  return keptSkillDirs;
}

function isPathWithinOrEqual(basePath, candidatePath) {
  const relative = path.relative(basePath, candidatePath);
  return relative === '' || (!relative.startsWith('..') && !path.isAbsolute(relative));
}

function resolveSymlinkTargetAbsolute(linkPath) {
  const linkTarget = fs.readlinkSync(linkPath);
  return path.resolve(path.dirname(linkPath), linkTarget);
}

function resolveSymlinkTargetForScopeCheck(linkPath) {
  const resolved = resolveSymlinkTargetAbsolute(linkPath);
  try {
    return fs.realpathSync(resolved);
  } catch {
    return resolved;
  }
}

function symlinkPointsIntoScriptDir(linkPath) {
  try {
    const resolvedTarget = resolveSymlinkTargetForScopeCheck(linkPath);
    return isPathWithinOrEqual(SCRIPT_DIR_REAL, resolvedTarget);
  } catch {
    return false;
  }
}

function assertFilePathIsNotDirectory(fullPath) {
  if (!fs.existsSync(fullPath)) return;
  if (isSymlink(fullPath)) return;
  if (fs.statSync(fullPath).isDirectory()) {
    throw new Error(`Expected file at ${fullPath}, but found directory. Remove or rename it, then re-run.`);
  }
}

function normalizeManifestFiles(files = {}) {
  const normalized = {};
  const source = files || {};
  for (const [rel, checksum] of Object.entries(source)) {
    normalized[normalizeRelPath(rel)] = checksum;
  }
  return normalized;
}

/**
 * Recursively collect files from a directory, returning relative paths.
 * @param {string} dir - Directory to scan
 * @param {string} prefix - Path prefix for the destination
 * @returns {Array<{rel: string, abs: string}>}
 */
function collectFiles(dir, prefix) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    if (SKIP_PATTERNS.includes(entry.name)) continue;
    const abs = path.join(dir, entry.name);
    const rel = normalizeRelPath(prefix ? path.posix.join(prefix, entry.name) : entry.name);
    if (entry.isDirectory()) {
      results.push(...collectFiles(abs, rel));
    } else {
      results.push({ rel, abs });
    }
  }
  return results;
}

// ── Phase 1: Determine target ───────────────────────────────────────────────

const targetDir = hasGlobal
  ? path.join(os.homedir(), '.claude')
  : path.join(process.cwd(), '.claude');

const mode = hasCopy ? 'copy' : 'link';
const manifestDir = path.join(targetDir, 'llm-toolkit');
const manifestPath = path.join(manifestDir, '.manifest.json');

// ── Phase 2: Read old manifest ──────────────────────────────────────────────

function readManifest() {
  try {
    if (fs.existsSync(manifestPath)) {
      return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    }
    // Fallback: check for manifest from before the rename (claude-code-toolkit -> llm-toolkit)
    const legacyManifestPath = path.join(targetDir, 'claude-code-toolkit', '.manifest.json');
    if (fs.existsSync(legacyManifestPath)) {
      console.log(`  Migrating manifest from claude-code-toolkit to llm-toolkit`);
      return JSON.parse(fs.readFileSync(legacyManifestPath, 'utf8'));
    }
    return null;
  } catch {
    console.log(`  ${yellow}Warning:${reset} manifest corrupted, treating as fresh install`);
    return null;
  }
}

// ── Phase 3: Migrate from install.sh ────────────────────────────────────────

/**
 * If no manifest exists, scan for symlinks pointing into this toolkit repo.
 * Build a synthetic manifest so orphan/conflict logic works on first migration.
 */
function migrateFromInstallSh() {
  const files = {};

  function scanForSymlinks(dir, prefix) {
    if (!fs.existsSync(dir)) return;
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const full = path.join(dir, entry.name);
      const rel = normalizeRelPath(prefix ? path.posix.join(prefix, entry.name) : entry.name);

      if (entry.isSymbolicLink()) {
        if (symlinkPointsIntoScriptDir(full)) {
          // This is a symlink into our repo
          if (fs.statSync(full).isDirectory()) {
            // Directory symlink (e.g. skills/linear -> repo/skills/linear/)
            // Expand into individual file entries
            const realFiles = collectFiles(full, rel);
            for (const f of realFiles) {
              try {
                const content = fs.readFileSync(f.abs, 'utf8');
                files[f.rel] = computeChecksum(content);
              } catch {
                files[f.rel] = 'migrated';
              }
            }
          } else {
            // File symlink
            try {
              const content = fs.readFileSync(full, 'utf8');
              files[rel] = computeChecksum(content);
            } catch {
              files[rel] = 'migrated';
            }
          }
        }
      } else if (entry.isDirectory()) {
        scanForSymlinks(full, rel);
      }
    }
  }

  // Scan the directories the old install.sh would have touched
  scanForSymlinks(path.join(targetDir, 'agents'), 'agents');
  scanForSymlinks(path.join(targetDir, 'commands'), 'commands');
  scanForSymlinks(path.join(targetDir, 'skills'), 'skills');
  scanForSymlinks(path.join(targetDir, 'references'), 'references');

  if (Object.keys(files).length === 0) return null;

  console.log(`  Migrating from install.sh (found ${Object.keys(files).length} tracked files)`);
  return {
    version: '0.0.0',
    installedAt: new Date().toISOString(),
    mode: 'link',
    files
  };
}

// ── Phase 4: Build new file list ────────────────────────────────────────────

function buildFileList() {
  const files = [];
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'agents'), 'agents'));
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'commands'), 'commands'));
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'skills'), 'skills'));
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'references'), 'references'));
  return files;
}

// ── Phase 5: Compare manifests ──────────────────────────────────────────────

function compareManifests(oldManifest, newFiles) {
  const orphans = [];
  const conflicts = new Set();

  const newSet = new Set(newFiles.map(f => f.rel));
  const oldFiles = normalizeManifestFiles(oldManifest && oldManifest.files);

  if (oldManifest && oldManifest.files) {
    // Orphans: in old manifest but not in new file list
    for (const oldPath of Object.keys(oldFiles)) {
      if (!newSet.has(oldPath)) {
        const full = path.join(targetDir, relToFsPath(oldPath));
        if (fs.existsSync(full) || isSymlink(full)) {
          orphans.push(oldPath);
        }
      }
    }

    const hasFileConflict = (f) => {
      const dest = path.join(targetDir, relToFsPath(f.rel));
      if (!fs.existsSync(dest) || isSymlink(dest)) return false;
      assertFilePathIsNotDirectory(dest);

      const oldChecksum = oldFiles[f.rel];
      if (!oldChecksum) return false;

      // Check if on-disk differs from what we last installed
      const diskContent = fs.readFileSync(dest, 'utf8');
      const diskChecksum = computeChecksum(diskContent);
      if (diskChecksum === oldChecksum) return false;

      // Check if source also differs from on-disk (true conflict)
      const srcContent = fs.readFileSync(f.abs, 'utf8');
      const srcChecksum = computeChecksum(srcContent);
      return srcChecksum !== diskChecksum;
    };

    // Conflicts in copy mode
    if (mode === 'copy') {
      for (const f of newFiles) {
        if (hasFileConflict(f)) {
          conflicts.add(f.rel);
        }
      }
    }

    // Conflicts when switching copy -> link:
    // modified local copies would otherwise be silently replaced by symlinks.
    if (mode === 'link' && oldManifest.mode === 'copy') {
      const skillDirsToCheck = new Set();
      for (const f of newFiles) {
        const skillName = getSkillNameFromRel(f.rel);
        if (skillName) {
          skillDirsToCheck.add(skillName);
          continue;
        }
        if (hasFileConflict(f)) {
          conflicts.add(f.rel);
        }
      }

      for (const skillName of skillDirsToCheck) {
        const skillInstallDir = path.join(targetDir, 'skills', skillName);
        const skillSourceDir = path.join(SCRIPT_DIR, 'skills', skillName);
        if (!fs.existsSync(skillInstallDir) || isSymlink(skillInstallDir)) continue;
        if (!fs.statSync(skillInstallDir).isDirectory()) {
          conflicts.add(`skills/${skillName}`);
          continue;
        }
        if (hasSkillDirLocalChanges(skillSourceDir, skillInstallDir)) {
          conflicts.add(`skills/${skillName}`);
        }
      }
    }
  }

  return { orphans, conflicts: Array.from(conflicts) };
}

function isSymlink(p) {
  try { return fs.lstatSync(p).isSymbolicLink(); } catch { return false; }
}

// ── Phase 6: Resolve conflicts ──────────────────────────────────────────────

async function resolveConflicts(conflicts, options = {}) {
  const { strictNonInteractive = false } = options;
  const overwrite = new Set();
  const keep = new Set();

  if (conflicts.length === 0) return { overwrite, keep };

  if (hasForce) {
    for (const c of conflicts) overwrite.add(c);
    console.log(`  ${yellow}Warning:${reset} overwriting ${conflicts.length} modified file(s) (force)`);
    return { overwrite, keep };
  }

  if (!isInteractive()) {
    if (strictNonInteractive) {
      throw new Error(
        `Local modifications detected in ${conflicts.length} path(s). Re-run interactively to choose overwrite/keep, or re-run with --force to overwrite.`
      );
    }
    for (const c of conflicts) overwrite.add(c);
    console.log(`  ${yellow}Warning:${reset} overwriting ${conflicts.length} modified file(s) (non-interactive)`);
    return { overwrite, keep };
  }

  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const ask = (q) => new Promise((resolve) => rl.question(q, resolve));

  console.log(`\n  ${yellow}${conflicts.length} file(s) have local modifications:${reset}\n`);

  let overwriteAll = false;
  let keepAll = false;

  for (const file of conflicts) {
    if (overwriteAll) { overwrite.add(file); continue; }
    if (keepAll) { keep.add(file); continue; }

    console.log(`  ${dim}${file}${reset}`);
    const answer = await ask('  [O]verwrite / [K]eep / [A]ll overwrite / [N]one keep? ');

    switch (answer.toLowerCase().trim()) {
      case 'o': case 'overwrite': overwrite.add(file); break;
      case 'k': case 'keep': keep.add(file); break;
      case 'a': case 'all': overwriteAll = true; overwrite.add(file); break;
      case 'n': case 'none': keepAll = true; keep.add(file); break;
      default:
        if (strictNonInteractive) keep.add(file);
        else overwrite.add(file);
    }
  }

  rl.close();
  console.log('');
  return { overwrite, keep };
}

// ── Phase 7: Install files ──────────────────────────────────────────────────

/**
 * Determine which skill directories need directory-level symlinks in link mode.
 * Returns a Map of skill dir name -> source path.
 */
function getSkillDirs() {
  const skillsDir = path.join(SCRIPT_DIR, 'skills');
  if (!fs.existsSync(skillsDir)) return new Map();

  const dirs = new Map();
  for (const entry of fs.readdirSync(skillsDir, { withFileTypes: true })) {
    if (entry.isDirectory() && !SKIP_PATTERNS.includes(entry.name)) {
      dirs.set(entry.name, path.join(skillsDir, entry.name));
    }
  }
  return dirs;
}

function hasSkillDirLocalChanges(skillSourceDir, skillInstallDir) {
  const sourceFiles = collectFiles(skillSourceDir, '');
  const sourceSet = new Set(sourceFiles.map(f => normalizeRelPath(f.rel)));

  for (const f of sourceFiles) {
    const rel = normalizeRelPath(f.rel);
    const dest = path.join(skillInstallDir, relToFsPath(rel));
    if (!fs.existsSync(dest) || isSymlink(dest)) return true;
    if (fs.statSync(dest).isDirectory()) return true;
    const srcBuf = fs.readFileSync(f.abs);
    const destBuf = fs.readFileSync(dest);
    if (!srcBuf.equals(destBuf)) return true;
  }

  for (const f of collectFiles(skillInstallDir, '')) {
    const rel = normalizeRelPath(f.rel);
    if (!sourceSet.has(rel)) {
      return true;
    }
  }

  return false;
}

function installFiles(newFiles, keep, oldManifest) {
  const installed = { agents: 0, commands: 0, skills: 0, references: 0 };
  const skillDirs = mode === 'link' ? getSkillDirs() : new Map();
  const keptSkillDirs = getKeptSkillDirs(keep);
  const handledSkillDirs = new Set();

  // In copy mode, replace any skill directory symlinks with real directories first.
  // Without this, writing files "into" a skill dir symlink would write into the repo.
  if (mode === 'copy') {
    const skillsInstallDir = path.join(targetDir, 'skills');
    if (fs.existsSync(skillsInstallDir)) {
      for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
        const full = path.join(skillsInstallDir, entry.name);
        if (entry.isSymbolicLink()) {
          if (symlinkPointsIntoScriptDir(full)) {
            fs.unlinkSync(full);
            // Real directory will be created by mkdirSync in the copy loop
          }
        }
      }
    }
  }

  for (const f of newFiles) {
    const rel = normalizeRelPath(f.rel);
    const skillName = getSkillNameFromRel(rel);
    if (keep.has(rel) || (skillName && keptSkillDirs.has(skillName))) continue;

    const dest = path.join(targetDir, relToFsPath(rel));

    if (mode === 'link') {
      // For skills, use directory symlinks (one per skill dir)
      if (rel.startsWith('skills/')) {
        if (!handledSkillDirs.has(skillName) && skillDirs.has(skillName)) {
          handledSkillDirs.add(skillName);
          const linkPath = path.join(targetDir, 'skills', skillName);
          const linkTarget = skillDirs.get(skillName);
          fs.mkdirSync(path.join(targetDir, 'skills'), { recursive: true });

          if (isSymlink(linkPath)) {
            const current = fs.readlinkSync(linkPath);
            if (current === linkTarget || current === linkTarget + '/') {
              // Already correct — don't count
            } else {
              fs.unlinkSync(linkPath);
              fs.symlinkSync(linkTarget, linkPath);
              installed.skills++;
            }
          } else if (fs.existsSync(linkPath) && fs.statSync(linkPath).isDirectory()) {
            // Real directory exists — OK if copy→link switch or --force
            if ((oldManifest && oldManifest.mode === 'copy') || hasForce) {
              fs.rmSync(linkPath, { recursive: true });
              fs.symlinkSync(linkTarget, linkPath);
              installed.skills++;
            } else {
              console.error(`  Error: real directory exists at ${linkPath}. Remove it or re-run with --force.`);
              process.exit(1);
            }
          } else {
            fs.symlinkSync(linkTarget, linkPath);
            installed.skills++;
          }
        }
        continue; // individual skill files handled by dir symlink
      }

      // For agents, commands, and references: individual file symlinks
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      assertFilePathIsNotDirectory(dest);
      if (isSymlink(dest)) {
        const current = fs.readlinkSync(dest);
        if (current === f.abs) continue; // already correct
        fs.unlinkSync(dest);
      } else if (fs.existsSync(dest)) {
        fs.unlinkSync(dest); // remove real file before symlinking
      }
      fs.symlinkSync(f.abs, dest);
    } else {
      // Copy mode
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      assertFilePathIsNotDirectory(dest);
      // Remove pre-existing symlink before copying
      if (isSymlink(dest)) {
        fs.unlinkSync(dest);
      } else if (fs.existsSync(dest)) {
        // Check if content is identical — skip if so
        const srcBuf = fs.readFileSync(f.abs);
        const destBuf = fs.readFileSync(dest);
        if (srcBuf.equals(destBuf)) continue;
      }
      fs.copyFileSync(f.abs, dest);

      // chmod for executables
      if (f.abs.endsWith('.sh') || f.abs.endsWith('.py')) {
        fs.chmodSync(dest, 0o755);
      }
    }

    // Count categories (only reached when something actually changed)
    if (rel.startsWith('agents/')) installed.agents++;
    else if (rel.startsWith('commands/')) installed.commands++;
    else if (rel.startsWith('skills/')) {
      // Count per skill directory, not per file
      if (!handledSkillDirs.has(skillName)) {
        handledSkillDirs.add(skillName);
        installed.skills++;
      }
    }
    else if (rel.startsWith('references/')) installed.references++;
  }

  return installed;
}

// ── Phase 8: Remove orphans ─────────────────────────────────────────────────

function removeOrphans(orphans) {
  if (orphans.length === 0) return;

  const dirsToCheck = new Set();
  const protectedDirs = new Set(['agents', 'commands', 'skills', 'references']);

  for (const rel of orphans) {
    const full = path.join(targetDir, relToFsPath(rel));
    try {
      if (isSymlink(full)) {
        fs.unlinkSync(full);
      } else if (fs.existsSync(full)) {
        fs.unlinkSync(full);
      }
      console.log(`  ${yellow}Removed${reset} ${rel}`);
      dirsToCheck.add(path.dirname(full));
    } catch (e) {
      console.log(`  ${yellow}Warning:${reset} failed to remove ${rel}: ${e.message}`);
    }
  }

  // Also check if any skill directory symlinks are orphaned
  // (skill was removed entirely from repo)
  if (mode === 'link') {
    const skillsInstallDir = path.join(targetDir, 'skills');
    if (fs.existsSync(skillsInstallDir)) {
      for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
        const full = path.join(skillsInstallDir, entry.name);
        if (entry.isSymbolicLink()) {
          if (!symlinkPointsIntoScriptDir(full)) continue;
          const resolvedTarget = resolveSymlinkTargetAbsolute(full);
          if (!fs.existsSync(resolvedTarget)) {
            fs.unlinkSync(full);
            console.log(`  ${yellow}Removed${reset} skills/${entry.name} (stale symlink)`);
          }
        }
      }
    }
  }

  // Remove empty parent directories (deepest first), but never the top-level category dirs
  const sorted = Array.from(dirsToCheck).sort((a, b) => b.length - a.length);
  for (const dir of sorted) {
    try {
      const relDir = path.relative(targetDir, dir);
      if (protectedDirs.has(relDir)) continue;
      if (dir === targetDir) continue;
      const entries = fs.readdirSync(dir);
      if (entries.length === 0) {
        fs.rmdirSync(dir);
      }
    } catch {
      // ignore
    }
  }
}

// ── Phase 9: Write new manifest ─────────────────────────────────────────────

function buildAndWriteManifest(newFiles, keep) {
  const files = {};
  const keptSkillDirs = getKeptSkillDirs(keep);

  for (const f of newFiles) {
    const rel = normalizeRelPath(f.rel);
    const skillName = getSkillNameFromRel(rel);
    const isKeptSkill = skillName && keptSkillDirs.has(skillName);
    const dest = path.join(targetDir, relToFsPath(rel));
    if (keep.has(rel) || isKeptSkill) {
      // User kept their version — record its current checksum
      try {
        const content = fs.readFileSync(dest, 'utf8');
        files[rel] = computeChecksum(content);
      } catch {
        files[rel] = 'kept';
      }
    } else if (mode === 'link') {
      // For symlinks, checksum the source file
      try {
        const content = fs.readFileSync(f.abs, 'utf8');
        files[rel] = computeChecksum(content);
      } catch {
        // Binary file — checksum from buffer
        const buf = fs.readFileSync(f.abs);
        files[rel] = computeChecksum(buf);
      }
    } else {
      // Checksum the installed copy
      try {
        const content = fs.readFileSync(dest, 'utf8');
        files[rel] = computeChecksum(content);
      } catch {
        const buf = fs.readFileSync(dest);
        files[rel] = computeChecksum(buf);
      }
    }
  }

  const manifest = {
    version: MANIFEST_VERSION,
    installedAt: new Date().toISOString(),
    mode,
    files
  };

  fs.mkdirSync(manifestDir, { recursive: true });
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2) + '\n');
}

// ── Uninstall ────────────────────────────────────────────────────────────────

function uninstall() {
  const targetLabel = hasGlobal
    ? targetDir.replace(os.homedir(), '~')
    : targetDir.replace(process.cwd(), '.');

  console.log(`\nUninstalling from ${targetLabel}\n`);

  const oldManifest = readManifest();
  if (!oldManifest) {
    console.log('  Nothing to uninstall (no manifest found).');
    console.log('');
    return;
  }

  const files = normalizeManifestFiles(oldManifest.files);
  const fileKeys = Object.keys(files);

  let removed = 0;
  const dirsToCheck = new Set();
  const protectedDirs = new Set(['agents', 'commands', 'skills', 'references']);

  // Remove all tracked files
  for (const rel of fileKeys) {
    const full = path.join(targetDir, relToFsPath(rel));
    try {
      if (isSymlink(full) || fs.existsSync(full)) {
        fs.unlinkSync(full);
        removed++;
      }
    } catch (e) {
      console.log(`  ${yellow}Warning:${reset} failed to remove ${rel}: ${e.message}`);
    }
    // Collect all ancestor directories for cleanup
    let dir = path.dirname(full);
    while (dir !== targetDir && dir.startsWith(targetDir)) {
      dirsToCheck.add(dir);
      dir = path.dirname(dir);
    }
  }

  // Remove skill directory symlinks pointing into this toolkit
  const skillsInstallDir = path.join(targetDir, 'skills');
  if (fs.existsSync(skillsInstallDir)) {
    for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
      const full = path.join(skillsInstallDir, entry.name);
      if (entry.isSymbolicLink() && symlinkPointsIntoScriptDir(full)) {
        fs.unlinkSync(full);
        removed++;
        dirsToCheck.add(skillsInstallDir);
      }
    }
  }

  // Clean up empty directories (deepest first), skip top-level category dirs
  const sorted = Array.from(dirsToCheck).sort((a, b) => b.length - a.length);
  for (const dir of sorted) {
    try {
      const relDir = path.relative(targetDir, dir);
      if (protectedDirs.has(relDir)) continue;
      if (dir === targetDir) continue;
      const entries = fs.readdirSync(dir);
      if (entries.length === 0) {
        fs.rmdirSync(dir);
      }
    } catch {
      // ignore
    }
  }

  // Remove manifest file, then try removing manifest directory if empty
  try { fs.unlinkSync(manifestPath); } catch { /* ignore */ }
  try {
    const entries = fs.readdirSync(manifestDir);
    if (entries.length === 0) {
      fs.rmdirSync(manifestDir);
    }
  } catch { /* ignore */ }

  // Clean up legacy claude-code-toolkit directory if present
  const legacyManifestDir = path.join(targetDir, 'claude-code-toolkit');
  if (fs.existsSync(legacyManifestDir)) {
    fs.rmSync(legacyManifestDir, { recursive: true });
    console.log(`  Removed legacy ${legacyManifestDir.replace(os.homedir(), '~')}`);
  }

  if (removed > 0) {
    console.log(`  ${green}Removed${reset} ${removed} file(s)`);
  } else {
    console.log('  Nothing to remove (files already cleaned up).');
  }

  console.log('');
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  if (hasUninstall) {
    uninstall();
    return;
  }

  const targetLabel = hasGlobal
    ? targetDir.replace(os.homedir(), '~')
    : targetDir.replace(process.cwd(), '.');

  console.log(`\nInstalling to ${targetLabel} (${mode} mode)\n`);

  // Phase 2: Read old manifest
  let oldManifest = readManifest();

  // Phase 3: Migrate from install.sh if needed
  if (!oldManifest) {
    oldManifest = migrateFromInstallSh();
  }

  // Phase 4: Build new file list
  const newFiles = buildFileList();

  // Phase 5: Compare manifests
  const { orphans, conflicts } = compareManifests(oldManifest, newFiles);

  // Phase 6: Resolve conflicts
  const strictConflictHandling = mode === 'link' && oldManifest && oldManifest.mode === 'copy';
  const { overwrite, keep } = await resolveConflicts(conflicts, { strictNonInteractive: strictConflictHandling });

  // Phase 7: Install files
  const counts = installFiles(newFiles, keep, oldManifest);

  // Phase 8: Remove orphans
  removeOrphans(orphans);

  // Phase 9: Write new manifest
  buildAndWriteManifest(newFiles, keep);

  // Phase 10: Clean up legacy manifest directory
  const legacyManifestDir = path.join(targetDir, 'claude-code-toolkit');
  if (fs.existsSync(legacyManifestDir)) {
    fs.rmSync(legacyManifestDir, { recursive: true });
    console.log(`  Removed legacy ${legacyManifestDir.replace(os.homedir(), '~')}`);
  }

  // Summary
  const total = counts.agents + counts.commands + counts.skills + counts.references;
  if (total === 0 && orphans.length === 0 && conflicts.length === 0) {
    console.log('Everything is up to date.');
  } else {
    const parts = [];
    if (counts.agents > 0) parts.push(`${counts.agents} agents`);
    if (counts.commands > 0) parts.push(`${counts.commands} commands`);
    if (counts.skills > 0) parts.push(`${counts.skills} skills`);
    if (counts.references > 0) parts.push(`${counts.references} references`);
    if (parts.length > 0) {
      console.log(`  ${green}Installed${reset} ${parts.join(', ')}`);
    }
    if (orphans.length > 0) {
      console.log(`  Cleaned up ${orphans.length} orphaned file(s)`);
    }
  }

  console.log('');
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
