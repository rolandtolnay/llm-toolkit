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
const hasLocal = has('--local', '-l');
const hasLink = has('--link');
const hasForce = has('--force', '-f');
const hasHelp = has('--help', '-h');

if (hasHelp) {
  console.log(`
Usage: node install.js --global [--link] | --local [options]

Options:
  -g, --global   Install to ~/.claude/ (copies by default)
  -l, --local    Install to ./.claude/ in current directory (always copies)
      --link     Symlink instead of copy (global only, author convenience)
  -f, --force    Overwrite modified files without prompting
  -h, --help     Show this help message

Examples:
  node install.js --global          # Copy files to ~/.claude/
  node install.js --global --link   # Symlink into ~/.claude/ (auto-updates with git pull)
  node install.js --local           # Copy files to ./.claude/ for team sharing
`);
  process.exit(0);
}

if (!hasGlobal && !hasLocal) {
  console.error('Error: specify --global or --local');
  process.exit(1);
}
if (hasGlobal && hasLocal) {
  console.error('Error: cannot specify both --global and --local');
  process.exit(1);
}
if (hasLink && hasLocal) {
  console.error('Error: --link is only valid with --global');
  process.exit(1);
}
if (hasLink && process.platform === 'win32') {
  console.error('Error: --link is not supported on Windows (symlinks require admin privileges)');
  process.exit(1);
}

const SCRIPT_DIR = __dirname;
const MANIFEST_VERSION = '1.0.0';
const SKIP_PATTERNS = ['.DS_Store', '__pycache__', '.git'];

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

const mode = hasLink ? 'link' : 'copy';
const manifestDir = path.join(targetDir, 'claude-code-toolkit');
const manifestPath = path.join(manifestDir, '.manifest.json');

// ── Phase 2: Read old manifest ──────────────────────────────────────────────

function readManifest() {
  try {
    if (!fs.existsSync(manifestPath)) return null;
    return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
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
        const target = fs.readlinkSync(full);
        if (target.startsWith(SCRIPT_DIR + path.sep) || target === SCRIPT_DIR) {
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

  // commands/ (recursive — includes subdirs like consider/)
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'commands'), 'commands'));

  // skills/ (recursive — each skill dir with all contents)
  files.push(...collectFiles(path.join(SCRIPT_DIR, 'skills'), 'skills'));

  // prompt-quality-guide.md -> references/prompt-quality-guide.md
  const pqg = path.join(SCRIPT_DIR, 'prompt-quality-guide.md');
  if (fs.existsSync(pqg)) {
    files.push({ rel: 'references/prompt-quality-guide.md', abs: pqg });
  }

  return files;
}

// ── Phase 5: Compare manifests ──────────────────────────────────────────────

function compareManifests(oldManifest, newFiles) {
  const orphans = [];
  const conflicts = [];

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

    // Conflicts (copy mode only — symlinks always match source)
    if (mode === 'copy') {
      for (const f of newFiles) {
        const dest = path.join(targetDir, relToFsPath(f.rel));
        if (!fs.existsSync(dest) || isSymlink(dest)) continue;
        assertFilePathIsNotDirectory(dest);

        const oldChecksum = oldFiles[f.rel];
        if (!oldChecksum) continue;

        // Check if on-disk differs from what we last installed
        const diskContent = fs.readFileSync(dest, 'utf8');
        const diskChecksum = computeChecksum(diskContent);
        if (diskChecksum === oldChecksum) continue;

        // Check if source also differs from on-disk (true conflict)
        const srcContent = fs.readFileSync(f.abs, 'utf8');
        const srcChecksum = computeChecksum(srcContent);
        if (srcChecksum !== diskChecksum) {
          conflicts.push(f.rel);
        }
      }
    }
  }

  return { orphans, conflicts };
}

function isSymlink(p) {
  try { return fs.lstatSync(p).isSymbolicLink(); } catch { return false; }
}

// ── Phase 6: Resolve conflicts ──────────────────────────────────────────────

async function resolveConflicts(conflicts) {
  const overwrite = new Set();
  const keep = new Set();

  if (conflicts.length === 0) return { overwrite, keep };

  if (hasForce || !isInteractive()) {
    for (const c of conflicts) overwrite.add(c);
    const reason = hasForce ? 'force' : 'non-interactive';
    console.log(`  ${yellow}Warning:${reset} overwriting ${conflicts.length} modified file(s) (${reason})`);
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
      default: overwrite.add(file);
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
  const installed = { commands: 0, skills: 0, references: 0 };
  const skillDirs = mode === 'link' ? getSkillDirs() : new Map();
  const handledSkillDirs = new Set();

  // In copy->link migrations, verify all skill directories are safe to replace
  // before modifying any files to avoid partial installs on error.
  if (mode === 'link' && oldManifest && oldManifest.mode === 'copy' && !hasForce) {
    const changedSkills = [];
    for (const [skillName, skillSourceDir] of skillDirs) {
      const skillInstallDir = path.join(targetDir, 'skills', skillName);
      if (!fs.existsSync(skillInstallDir) || isSymlink(skillInstallDir)) continue;
      if (!fs.statSync(skillInstallDir).isDirectory()) continue;
      if (hasSkillDirLocalChanges(skillSourceDir, skillInstallDir)) {
        changedSkills.push(`skills/${skillName}`);
      }
    }
    if (changedSkills.length > 0) {
      throw new Error(
        `Local changes detected in ${changedSkills.join(', ')}. Refusing to replace with symlinks; back up changes or re-run with --force.`
      );
    }
  }

  // In copy mode, replace any skill directory symlinks with real directories first.
  // Without this, writing files "into" a skill dir symlink would write into the repo.
  if (mode === 'copy') {
    const skillsInstallDir = path.join(targetDir, 'skills');
    if (fs.existsSync(skillsInstallDir)) {
      for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
        const full = path.join(skillsInstallDir, entry.name);
        if (entry.isSymbolicLink()) {
          const target = fs.readlinkSync(full);
          if (target.startsWith(SCRIPT_DIR)) {
            fs.unlinkSync(full);
            // Real directory will be created by mkdirSync in the copy loop
          }
        }
      }
    }
  }

  for (const f of newFiles) {
    if (keep.has(f.rel)) continue;

    const dest = path.join(targetDir, relToFsPath(f.rel));

    if (mode === 'link') {
      // For skills, use directory symlinks (one per skill dir)
      if (f.rel.startsWith('skills/')) {
        const parts = normalizeRelPath(f.rel).split('/');
        const skillName = parts[1]; // e.g. "linear"
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
            // Real directory exists — only OK if we previously installed it (copy→link switch)
            if (oldManifest && oldManifest.mode === 'copy') {
              fs.rmSync(linkPath, { recursive: true });
              fs.symlinkSync(linkTarget, linkPath);
              installed.skills++;
            } else {
              console.error(`  Error: real directory exists at ${linkPath}. Remove it before using --link.`);
              process.exit(1);
            }
          } else {
            fs.symlinkSync(linkTarget, linkPath);
            installed.skills++;
          }
        }
        continue; // individual skill files handled by dir symlink
      }

      // For commands and references: individual file symlinks
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
    if (f.rel.startsWith('commands/')) installed.commands++;
    else if (f.rel.startsWith('skills/')) {
      // Count per skill directory, not per file
      const skillName = normalizeRelPath(f.rel).split('/')[1];
      if (!handledSkillDirs.has(skillName)) {
        handledSkillDirs.add(skillName);
        installed.skills++;
      }
    }
    else if (f.rel.startsWith('references/')) installed.references++;
  }

  return installed;
}

// ── Phase 8: Remove orphans ─────────────────────────────────────────────────

function removeOrphans(orphans) {
  if (orphans.length === 0) return;

  const dirsToCheck = new Set();
  const protectedDirs = new Set(['commands', 'skills', 'references']);

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
          const target = fs.readlinkSync(full);
          if (target.startsWith(SCRIPT_DIR + path.sep) && !fs.existsSync(target)) {
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

  for (const f of newFiles) {
    const dest = path.join(targetDir, relToFsPath(f.rel));
    if (keep.has(f.rel)) {
      // User kept their version — record its current checksum
      try {
        const content = fs.readFileSync(dest, 'utf8');
        files[f.rel] = computeChecksum(content);
      } catch {
        files[f.rel] = 'kept';
      }
    } else if (mode === 'link') {
      // For symlinks, checksum the source file
      try {
        const content = fs.readFileSync(f.abs, 'utf8');
        files[f.rel] = computeChecksum(content);
      } catch {
        // Binary file — checksum from buffer
        const buf = fs.readFileSync(f.abs);
        files[f.rel] = computeChecksum(buf);
      }
    } else {
      // Checksum the installed copy
      try {
        const content = fs.readFileSync(dest, 'utf8');
        files[f.rel] = computeChecksum(content);
      } catch {
        const buf = fs.readFileSync(dest);
        files[f.rel] = computeChecksum(buf);
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

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
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
  const { overwrite, keep } = await resolveConflicts(conflicts);

  // Phase 7: Install files
  const counts = installFiles(newFiles, keep, oldManifest);

  // Phase 8: Remove orphans
  removeOrphans(orphans);

  // Phase 9: Write new manifest
  buildAndWriteManifest(newFiles, keep);

  // Summary
  const total = counts.commands + counts.skills + counts.references;
  if (total === 0 && orphans.length === 0 && conflicts.length === 0) {
    console.log('Everything is up to date.');
  } else {
    const parts = [];
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
