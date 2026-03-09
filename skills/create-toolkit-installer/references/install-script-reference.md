# Install Script Reference

Complete template for toolkit installation scripts. Customize the 6 constants at the top — the rest adapts automatically.

## Configuration Constants

| Constant | Purpose | Example |
|---|---|---|
| `TOOLKIT_NAME` | Manifest subdirectory, log messages (kebab-case) | `flutter-llm-toolkit` |
| `TOOLKIT_DESCRIPTION` | Help text one-liner | `Flutter/Dart skills and commands for Claude Code` |
| `REPO_URL` | Clone URL in help examples | `https://github.com/user/my-toolkit.git` |
| `REPO_CLONE_NAME` | Directory name in help examples | `my-toolkit` |
| `INSTALLABLE_DIRS` | Which directories the toolkit ships | `['commands', 'skills', 'references']` |
| `LEGACY_MANIFEST_DIR_NAME` | Old toolkit name for migration, or `null` | `'old-toolkit-name'` |

`INSTALLABLE_DIRS` drives everything: file collection, migration scanning, install counts, orphan protection, and summary output. Add or remove entries to match what your toolkit ships.

## Architecture

10-phase pipeline, each phase isolated in its own function:

1. **CLI parsing** — flags, backward-compat no-ops, Windows check, self-install guard
2. **Read manifest** — from `<target>/<TOOLKIT_NAME>/.manifest.json`, with legacy fallback
3. **Migrate legacy symlinks** — build synthetic manifest from existing symlinks (first run only)
4. **Build file list** — recursive scan of INSTALLABLE_DIRS
5. **Compare manifests** — detect orphans (removed files), tracked modifications, and unmanaged destination collisions
6. **Resolve conflicts** — interactive prompt, force mode, or strict-non-interactive error
7. **Install files** — symlink or copy, with skill directory-level symlinks in link mode
8. **Remove orphans** — delete tracked files no longer in the toolkit, clean empty dirs
9. **Write manifest** — record checksums for next run's conflict detection
10. **Summary** — report what changed

## Gotchas

**1. Symlink resolution requires realpathSync.** `fs.readlinkSync` returns the raw target, which may be relative. Always resolve through `path.resolve(path.dirname(linkPath), target)` then `realpathSync`. String prefix matching like `target.startsWith(SCRIPT_DIR)` breaks with relative symlinks. The template uses `symlinkPointsIntoScriptDir()` which handles this correctly.

**2. Skills get directory-level symlinks.** In link mode, each skill directory becomes a single symlink (`skills/my-skill -> repo/skills/my-skill`), not individual file symlinks. This means conflict detection during copy-to-link migration must check the entire skill directory for changes, not individual files. The `hasSkillDirLocalChanges()` function handles this.

**3. Link-mode uninstall must remove skill symlink roots, not tracked files inside them.** The manifest still records per-file checksums for skills, but uninstall cannot blindly `unlink target/skills/my-skill/...` because that path traverses the directory symlink into the source repo. Remove the skill directory symlink itself (`target/skills/my-skill`) and skip per-file deletion for linked skills.

**4. Legacy migration must tolerate broken symlinks.** Old installs can leave stale symlinks behind. When scanning legacy symlinks, `fs.statSync(linkPath)` may throw even if `lstat` says the entry is a symlink. Catch that and skip the broken entry so a partially broken install does not abort migration.

**5. Fresh installs must treat unmanaged destinations as conflicts.** A missing manifest does not mean the target is empty. If `.claude/commands/foo.md` or `skills/my-skill` already exists and is not tracked by this toolkit, do not silently replace it in non-interactive mode. Surface it as a conflict and require interactive confirmation or `--force`.

**6. Copy mode must unlink skill dir symlinks first.** Writing files "into" a symlinked skill directory actually writes into the source repo. The install function unlinks skill directory symlinks pointing into the script dir before any copy-mode writes.

**7. Self-install guard prevents circular symlinks.** Without it, running `install.js` from inside the toolkit repo creates `.claude/` with symlinks pointing at itself. The guard compares `realpathSync(process.cwd())` against `SCRIPT_DIR_REAL`.

**8. Manifest lives in a subdirectory.** Path: `<target>/<TOOLKIT_NAME>/.manifest.json`. Multiple toolkits coexist at the same target (`~/.claude/`), each with its own manifest directory. Never use a flat manifest at target root.

**9. Protected directories survive orphan cleanup.** Top-level category dirs (`agents/`, `commands/`, etc.) are never deleted during cleanup — other toolkits or user files may live there.

**10. Copy-to-link migration needs strict conflict handling.** Switching from copy to link replaces entire skill directories with symlinks. In non-interactive mode, this throws an error (strictNonInteractive) rather than silently overwriting. Users must run interactively or with `--force`.

**11. Unmanaged collisions should also trigger strict non-interactive handling.** If the installer would overwrite user-owned files or symlinks that are not in the manifest, non-interactive mode must stop instead of defaulting to overwrite. Silent replacement is only acceptable for already-tracked destinations, and even then only within the existing conflict policy.

**12. Windows symlinks require admin.** Default to erroring with `--copy` suggestion when `process.platform === 'win32'` and `--copy` isn't set.

**13. Backward-compat flags are silent no-ops.** When defaults change (e.g., link becomes default instead of copy), keep old flags (`--link`, `--local`) accepted but ignored. Prevents breaking existing scripts or documentation.

**14. Executables need chmod after copy.** Files ending in `.sh` or `.py` get `chmod 755` after copying. Symlinks inherit source permissions automatically.

## Complete Template

Only the 6 constants at the top need customization. Remove entries from `INSTALLABLE_DIRS` for directories your toolkit doesn't ship.

```js
#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');
const readline = require('readline');
const crypto = require('crypto');

// ── Configuration ───────────────────────────────────────────────────────────
// Customize these constants for your toolkit. Everything else adapts automatically.

const TOOLKIT_NAME = 'my-toolkit';
const TOOLKIT_DESCRIPTION = 'skills, commands, and references for Claude Code';
const REPO_URL = 'https://github.com/user/my-toolkit.git';
const REPO_CLONE_NAME = 'my-toolkit';
const INSTALLABLE_DIRS = ['agents', 'commands', 'skills', 'references'];
const LEGACY_MANIFEST_DIR_NAME = null; // Set to old name if renaming a toolkit

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

// Backward-compat no-ops
const _hasLocal = has('--local', '-l');
const _hasLink = has('--link');

if (hasHelp) {
  console.log(`
Usage: ${process.argv[1]} [options]

Installs ${TOOLKIT_DESCRIPTION}
by creating symlinks from your project (or global ~/.claude/) to this toolkit.

Options:
  -g, --global     Install to ~/.claude/ (default: current project ./.claude/)
      --copy       Copy files instead of symlinking
  -f, --force      Overwrite modified files without prompting
      --uninstall  Remove all toolkit files from the target scope
  -h, --help       Show this help message

Examples:
  git clone ${REPO_URL} ~/toolkits/${REPO_CLONE_NAME}

  cd your-project && ~/toolkits/${REPO_CLONE_NAME}/install.js
  ~/toolkits/${REPO_CLONE_NAME}/install.js --global
  ~/toolkits/${REPO_CLONE_NAME}/install.js --copy
  ~/toolkits/${REPO_CLONE_NAME}/install.js --uninstall
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

// Safety: don't install into the toolkit repo itself
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
  return normalized.split('/')[1] || null;
}

function getKeptSkillDirs(keep) {
  const keptSkillDirs = new Set();
  for (const rel of keep) {
    const normalized = normalizeRelPath(rel);
    const skillName = getSkillNameFromRel(normalized);
    if (!skillName) continue;
    if (normalized.split('/').length === 2) keptSkillDirs.add(skillName);
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
  try { return fs.realpathSync(resolved); } catch { return resolved; }
}

function symlinkPointsIntoScriptDir(linkPath) {
  try {
    const resolvedTarget = resolveSymlinkTargetForScopeCheck(linkPath);
    return isPathWithinOrEqual(SCRIPT_DIR_REAL, resolvedTarget);
  } catch { return false; }
}

function isSymlink(p) {
  try { return fs.lstatSync(p).isSymbolicLink(); } catch { return false; }
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
  for (const [rel, checksum] of Object.entries(files || {})) {
    normalized[normalizeRelPath(rel)] = checksum;
  }
  return normalized;
}

function collectFiles(dir, prefix) {
  const results = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (SKIP_PATTERNS.includes(entry.name)) continue;
    const abs = path.join(dir, entry.name);
    const rel = normalizeRelPath(prefix ? path.posix.join(prefix, entry.name) : entry.name);
    if (entry.isDirectory()) results.push(...collectFiles(abs, rel));
    else results.push({ rel, abs });
  }
  return results;
}

// ── Phase 1: Determine target ───────────────────────────────────────────────

const targetDir = hasGlobal
  ? path.join(os.homedir(), '.claude')
  : path.join(process.cwd(), '.claude');

const mode = hasCopy ? 'copy' : 'link';
const manifestDir = path.join(targetDir, TOOLKIT_NAME);
const manifestPath = path.join(manifestDir, '.manifest.json');

// ── Phase 2: Read old manifest ──────────────────────────────────────────────

function readManifest() {
  try {
    if (fs.existsSync(manifestPath)) {
      return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    }
    if (LEGACY_MANIFEST_DIR_NAME) {
      const legacyPath = path.join(targetDir, LEGACY_MANIFEST_DIR_NAME, '.manifest.json');
      if (fs.existsSync(legacyPath)) {
        console.log(`  Migrating manifest from ${LEGACY_MANIFEST_DIR_NAME} to ${TOOLKIT_NAME}`);
        return JSON.parse(fs.readFileSync(legacyPath, 'utf8'));
      }
    }
    return null;
  } catch {
    console.log(`  ${yellow}Warning:${reset} manifest corrupted, treating as fresh install`);
    return null;
  }
}

// ── Phase 3: Migrate legacy symlinks ────────────────────────────────────────

function migrateFromLegacySymlinks() {
  const files = {};

  function scanForSymlinks(dir, prefix) {
    if (!fs.existsSync(dir)) return;
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      const rel = normalizeRelPath(prefix ? path.posix.join(prefix, entry.name) : entry.name);

      if (entry.isSymbolicLink()) {
        if (symlinkPointsIntoScriptDir(full)) {
          let targetStat;
          try {
            targetStat = fs.statSync(full);
          } catch {
            continue;
          }
          if (targetStat.isDirectory()) {
            for (const f of collectFiles(full, rel)) {
              try { files[f.rel] = computeChecksum(fs.readFileSync(f.abs, 'utf8')); }
              catch { files[f.rel] = 'migrated'; }
            }
          } else {
            try { files[rel] = computeChecksum(fs.readFileSync(full, 'utf8')); }
            catch { files[rel] = 'migrated'; }
          }
        }
      } else if (entry.isDirectory()) {
        scanForSymlinks(full, rel);
      }
    }
  }

  for (const dir of INSTALLABLE_DIRS) {
    scanForSymlinks(path.join(targetDir, dir), dir);
  }

  if (Object.keys(files).length === 0) return null;

  console.log(`  Migrating legacy symlinks (found ${Object.keys(files).length} tracked files)`);
  return { version: '0.0.0', installedAt: new Date().toISOString(), mode: 'link', files };
}

// ── Phase 4: Build new file list ────────────────────────────────────────────

function buildFileList() {
  const files = [];
  for (const dir of INSTALLABLE_DIRS) {
    files.push(...collectFiles(path.join(SCRIPT_DIR, dir), dir));
  }
  return files;
}

// ── Phase 5: Compare manifests ──────────────────────────────────────────────

function hasSkillDirLocalChanges(skillSourceDir, skillInstallDir) {
  const sourceFiles = collectFiles(skillSourceDir, '');
  const sourceSet = new Set(sourceFiles.map(f => normalizeRelPath(f.rel)));

  for (const f of sourceFiles) {
    const rel = normalizeRelPath(f.rel);
    const dest = path.join(skillInstallDir, relToFsPath(rel));
    if (!fs.existsSync(dest) || isSymlink(dest)) return true;
    if (fs.statSync(dest).isDirectory()) return true;
    if (!fs.readFileSync(f.abs).equals(fs.readFileSync(dest))) return true;
  }

  for (const f of collectFiles(skillInstallDir, '')) {
    if (!sourceSet.has(normalizeRelPath(f.rel))) return true;
  }

  return false;
}

function compareManifests(oldManifest, newFiles) {
  const orphans = [];
  const conflicts = new Set();
  let hasUnmanagedConflicts = false;

  const newSet = new Set(newFiles.map(f => f.rel));
  const oldFiles = normalizeManifestFiles(oldManifest && oldManifest.files);
  const trackedSkillDirs = new Set(
    Object.keys(oldFiles)
      .map(getSkillNameFromRel)
      .filter(Boolean)
  );

  const addConflict = (rel, options = {}) => {
    conflicts.add(rel);
    if (options.unmanaged) hasUnmanagedConflicts = true;
  };

  const hasTrackedFile = (rel) => Object.prototype.hasOwnProperty.call(oldFiles, rel);

  const hasFileConflict = (f) => {
    const dest = path.join(targetDir, relToFsPath(f.rel));
    if (!fs.existsSync(dest) || isSymlink(dest)) return false;
    assertFilePathIsNotDirectory(dest);
    const oldChecksum = oldFiles[f.rel];
    if (!oldChecksum) return false;
    const diskChecksum = computeChecksum(fs.readFileSync(dest, 'utf8'));
    if (diskChecksum === oldChecksum) return false;
    return computeChecksum(fs.readFileSync(f.abs, 'utf8')) !== diskChecksum;
  };

  const hasUnmanagedFileCollision = (f) => {
    const dest = path.join(targetDir, relToFsPath(f.rel));
    if ((!fs.existsSync(dest) && !isSymlink(dest)) || hasTrackedFile(f.rel)) return false;

    if (isSymlink(dest)) {
      return !(mode === 'link' && fs.readlinkSync(dest) === f.abs);
    }

    const destStat = fs.statSync(dest);
    if (destStat.isDirectory()) return true;

    if (mode === 'copy') {
      return !fs.readFileSync(f.abs).equals(fs.readFileSync(dest));
    }

    return true;
  };

  const skillDirsToCheck = new Set();
  for (const f of newFiles) {
    const skillName = getSkillNameFromRel(f.rel);
    if (skillName) {
      skillDirsToCheck.add(skillName);
      if (mode === 'copy' && hasUnmanagedFileCollision(f)) addConflict(f.rel, { unmanaged: true });
      continue;
    }

    if (hasUnmanagedFileCollision(f)) addConflict(f.rel, { unmanaged: true });
  }

  if (mode === 'link') {
    for (const skillName of skillDirsToCheck) {
      const skillInstallDir = path.join(targetDir, 'skills', skillName);
      if (!fs.existsSync(skillInstallDir) && !isSymlink(skillInstallDir)) continue;

      if (isSymlink(skillInstallDir)) {
        if (!symlinkPointsIntoScriptDir(skillInstallDir)) {
          addConflict(`skills/${skillName}`, { unmanaged: true });
        }
        continue;
      }

      if (!fs.statSync(skillInstallDir).isDirectory()) {
        addConflict(`skills/${skillName}`, { unmanaged: true });
        continue;
      }

      if (!trackedSkillDirs.has(skillName) || (oldManifest && oldManifest.mode === 'link')) {
        addConflict(`skills/${skillName}`, { unmanaged: true });
      }
    }
  }

  if (oldManifest && oldManifest.files) {
    for (const oldPath of Object.keys(oldFiles)) {
      if (!newSet.has(oldPath)) {
        const full = path.join(targetDir, relToFsPath(oldPath));
        if (fs.existsSync(full) || isSymlink(full)) orphans.push(oldPath);
      }
    }

    if (mode === 'copy') {
      for (const f of newFiles) {
        if (hasFileConflict(f)) addConflict(f.rel);
      }
    }

    if (mode === 'link' && oldManifest.mode === 'copy') {
      for (const f of newFiles) {
        const skillName = getSkillNameFromRel(f.rel);
        if (skillName) continue;
        if (hasFileConflict(f)) addConflict(f.rel);
      }
      for (const skillName of skillDirsToCheck) {
        const skillInstallDir = path.join(targetDir, 'skills', skillName);
        const skillSourceDir = path.join(SCRIPT_DIR, 'skills', skillName);
        if (!fs.existsSync(skillInstallDir) || isSymlink(skillInstallDir)) continue;
        if (!fs.statSync(skillInstallDir).isDirectory()) {
          addConflict(`skills/${skillName}`);
          continue;
        }
        if (hasSkillDirLocalChanges(skillSourceDir, skillInstallDir)) {
          addConflict(`skills/${skillName}`);
        }
      }
    }
  }

  return { orphans, conflicts: Array.from(conflicts), hasUnmanagedConflicts };
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
        `Local modifications detected in ${conflicts.length} path(s). Re-run interactively or with --force.`
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

function installFiles(newFiles, keep, oldManifest) {
  const installed = {};
  for (const dir of INSTALLABLE_DIRS) installed[dir] = 0;

  const skillDirs = mode === 'link' ? getSkillDirs() : new Map();
  const keptSkillDirs = getKeptSkillDirs(keep);
  const handledSkillDirs = new Set();

  // In copy mode, replace skill directory symlinks with real directories first
  if (mode === 'copy') {
    const skillsInstallDir = path.join(targetDir, 'skills');
    if (fs.existsSync(skillsInstallDir)) {
      for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
        const full = path.join(skillsInstallDir, entry.name);
        if (entry.isSymbolicLink() && symlinkPointsIntoScriptDir(full)) {
          fs.unlinkSync(full);
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
      // Skills: directory-level symlinks (one per skill)
      if (rel.startsWith('skills/')) {
        if (!handledSkillDirs.has(skillName) && skillDirs.has(skillName)) {
          handledSkillDirs.add(skillName);
          const linkPath = path.join(targetDir, 'skills', skillName);
          const linkTarget = skillDirs.get(skillName);
          fs.mkdirSync(path.join(targetDir, 'skills'), { recursive: true });

          if (isSymlink(linkPath)) {
            const current = fs.readlinkSync(linkPath);
            if (current !== linkTarget && current !== linkTarget + '/') {
              fs.unlinkSync(linkPath);
              fs.symlinkSync(linkTarget, linkPath);
              installed.skills++;
            }
          } else if (fs.existsSync(linkPath) && fs.statSync(linkPath).isDirectory()) {
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
        continue;
      }

      // Everything else: individual file symlinks
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      assertFilePathIsNotDirectory(dest);
      if (isSymlink(dest)) {
        const current = fs.readlinkSync(dest);
        if (current === f.abs) continue;
        fs.unlinkSync(dest);
      } else if (fs.existsSync(dest)) {
        fs.unlinkSync(dest);
      }
      fs.symlinkSync(f.abs, dest);
    } else {
      // Copy mode
      fs.mkdirSync(path.dirname(dest), { recursive: true });
      assertFilePathIsNotDirectory(dest);
      if (isSymlink(dest)) {
        fs.unlinkSync(dest);
      } else if (fs.existsSync(dest)) {
        if (fs.readFileSync(f.abs).equals(fs.readFileSync(dest))) continue;
      }
      fs.copyFileSync(f.abs, dest);
      if (f.abs.endsWith('.sh') || f.abs.endsWith('.py')) fs.chmodSync(dest, 0o755);
    }

    // Count by category
    const category = rel.split('/')[0];
    if (category === 'skills') {
      if (!handledSkillDirs.has(skillName)) {
        handledSkillDirs.add(skillName);
        installed.skills++;
      }
    } else if (installed[category] !== undefined) {
      installed[category]++;
    }
  }

  return installed;
}

// ── Phase 8: Remove orphans ─────────────────────────────────────────────────

function removeOrphans(orphans) {
  if (orphans.length === 0) return;

  const dirsToCheck = new Set();
  const protectedDirs = new Set(INSTALLABLE_DIRS);

  for (const rel of orphans) {
    const full = path.join(targetDir, relToFsPath(rel));
    try {
      if (isSymlink(full) || fs.existsSync(full)) fs.unlinkSync(full);
      console.log(`  ${yellow}Removed${reset} ${rel}`);
      dirsToCheck.add(path.dirname(full));
    } catch (e) {
      console.log(`  ${yellow}Warning:${reset} failed to remove ${rel}: ${e.message}`);
    }
  }

  if (mode === 'link') {
    const skillsInstallDir = path.join(targetDir, 'skills');
    if (fs.existsSync(skillsInstallDir)) {
      for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
        const full = path.join(skillsInstallDir, entry.name);
        if (entry.isSymbolicLink()) {
          if (!symlinkPointsIntoScriptDir(full)) continue;
          if (!fs.existsSync(resolveSymlinkTargetAbsolute(full))) {
            fs.unlinkSync(full);
            console.log(`  ${yellow}Removed${reset} skills/${entry.name} (stale symlink)`);
          }
        }
      }
    }
  }

  const sorted = Array.from(dirsToCheck).sort((a, b) => b.length - a.length);
  for (const dir of sorted) {
    try {
      const relDir = path.relative(targetDir, dir);
      if (protectedDirs.has(relDir) || dir === targetDir) continue;
      if (fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
    } catch { /* ignore */ }
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
      try { files[rel] = computeChecksum(fs.readFileSync(dest, 'utf8')); }
      catch { files[rel] = 'kept'; }
    } else if (mode === 'link') {
      try { files[rel] = computeChecksum(fs.readFileSync(f.abs, 'utf8')); }
      catch { files[rel] = computeChecksum(fs.readFileSync(f.abs)); }
    } else {
      try { files[rel] = computeChecksum(fs.readFileSync(dest, 'utf8')); }
      catch { files[rel] = computeChecksum(fs.readFileSync(dest)); }
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
  const linkedSkillDirs = new Set();
  let removed = 0;
  const dirsToCheck = new Set();
  const protectedDirs = new Set(INSTALLABLE_DIRS);

  for (const rel of Object.keys(files)) {
    const skillName = getSkillNameFromRel(rel);
    if (oldManifest.mode === 'link' && skillName) {
      linkedSkillDirs.add(skillName);
      continue;
    }

    const full = path.join(targetDir, relToFsPath(rel));
    try {
      if (isSymlink(full) || fs.existsSync(full)) { fs.unlinkSync(full); removed++; }
    } catch (e) {
      console.log(`  ${yellow}Warning:${reset} failed to remove ${rel}: ${e.message}`);
    }
    let dir = path.dirname(full);
    while (dir !== targetDir && dir.startsWith(targetDir)) {
      dirsToCheck.add(dir);
      dir = path.dirname(dir);
    }
  }

  const skillsInstallDir = path.join(targetDir, 'skills');
  if (fs.existsSync(skillsInstallDir)) {
    for (const skillName of linkedSkillDirs) {
      const full = path.join(skillsInstallDir, skillName);
      if (!isSymlink(full) || !symlinkPointsIntoScriptDir(full)) continue;
      fs.unlinkSync(full);
      removed++;
      dirsToCheck.add(skillsInstallDir);
    }

    for (const entry of fs.readdirSync(skillsInstallDir, { withFileTypes: true })) {
      const full = path.join(skillsInstallDir, entry.name);
      if (!entry.isSymbolicLink() || !symlinkPointsIntoScriptDir(full)) continue;
      if (linkedSkillDirs.has(entry.name)) continue;
      fs.unlinkSync(full);
      removed++;
      dirsToCheck.add(skillsInstallDir);
    }
  }

  const sorted = Array.from(dirsToCheck).sort((a, b) => b.length - a.length);
  for (const dir of sorted) {
    try {
      const relDir = path.relative(targetDir, dir);
      if (protectedDirs.has(relDir) || dir === targetDir) continue;
      if (fs.readdirSync(dir).length === 0) fs.rmdirSync(dir);
    } catch { /* ignore */ }
  }

  try { fs.unlinkSync(manifestPath); } catch { /* ignore */ }
  try {
    if (fs.readdirSync(manifestDir).length === 0) fs.rmdirSync(manifestDir);
  } catch { /* ignore */ }

  if (LEGACY_MANIFEST_DIR_NAME) {
    const legacyDir = path.join(targetDir, LEGACY_MANIFEST_DIR_NAME);
    if (fs.existsSync(legacyDir)) {
      fs.rmSync(legacyDir, { recursive: true });
      console.log(`  Removed legacy ${legacyDir.replace(os.homedir(), '~')}`);
    }
  }

  if (removed > 0) console.log(`  ${green}Removed${reset} ${removed} file(s)`);
  else console.log('  Nothing to remove (files already cleaned up).');
  console.log('');
}

// ── Main ────────────────────────────────────────────────────────────────────

async function main() {
  if (hasUninstall) { uninstall(); return; }

  const targetLabel = hasGlobal
    ? targetDir.replace(os.homedir(), '~')
    : targetDir.replace(process.cwd(), '.');

  console.log(`\nInstalling to ${targetLabel} (${mode} mode)\n`);

  let oldManifest = readManifest();
  if (!oldManifest) oldManifest = migrateFromLegacySymlinks();

  const newFiles = buildFileList();
  const { orphans, conflicts, hasUnmanagedConflicts } = compareManifests(oldManifest, newFiles);

  const strictConflictHandling =
    hasUnmanagedConflicts || (mode === 'link' && oldManifest && oldManifest.mode === 'copy');
  const { overwrite, keep } = await resolveConflicts(conflicts, { strictNonInteractive: strictConflictHandling });

  const counts = installFiles(newFiles, keep, oldManifest);
  removeOrphans(orphans);
  buildAndWriteManifest(newFiles, keep);

  if (LEGACY_MANIFEST_DIR_NAME) {
    const legacyDir = path.join(targetDir, LEGACY_MANIFEST_DIR_NAME);
    if (fs.existsSync(legacyDir)) {
      fs.rmSync(legacyDir, { recursive: true });
      console.log(`  Removed legacy ${legacyDir.replace(os.homedir(), '~')}`);
    }
  }

  const total = INSTALLABLE_DIRS.reduce((sum, dir) => sum + (counts[dir] || 0), 0);
  if (total === 0 && orphans.length === 0 && conflicts.length === 0) {
    console.log('Everything is up to date.');
  } else {
    const parts = [];
    for (const dir of INSTALLABLE_DIRS) {
      if (counts[dir] > 0) parts.push(`${counts[dir]} ${dir}`);
    }
    if (parts.length > 0) console.log(`  ${green}Installed${reset} ${parts.join(', ')}`);
    if (orphans.length > 0) console.log(`  Cleaned up ${orphans.length} orphaned file(s)`);
  }

  console.log('');
}

main().catch((err) => {
  console.error(`Error: ${err.message}`);
  process.exit(1);
});
```
