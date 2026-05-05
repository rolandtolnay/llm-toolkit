import json
import subprocess
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "research.py"


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")


def make_fixture(root: Path) -> Path:
    research_dir = root / "Research"
    write_file(
        research_dir / "INDEX.md",
        """
        # Research Index

        ### Stale INDEX SoftPOS Title — 2026-04-29
        **Tags:** softpos, tap-to-pay, indexed-only
        - [Synthesis](2026-04-29-indexed-softpos/00-synthesis.md) — Decision summary for SoftPOS onboarding friction.
        - [Compliance friction](2026-04-29-indexed-softpos/01-compliance-friction.md) — SoftPOS onboarding friction splits into compliance-mandated and product-reducible work.
        - [Merchant sentiment](2026-04-29-indexed-softpos/02-merchant-sentiment.md) — Merchant complaints focus on NFC reliability.
        """,
    )
    write_file(
        research_dir / "2026-04-29-indexed-softpos" / "00-synthesis.md",
        """
        ---
        title: "Indexed SoftPOS Run"
        date: 2026-04-29
        run_id: 2026-04-29-indexed-softpos
        role: synthesis
        query: "What causes tap to pay onboarding friction?"
        confidence: likely
        tags: [softpos-onboarding, tap-to-pay]
        sources:
          - url: https://example.com/synthesis-primary
            role: primary
        ---

        # Synthesis
        """,
    )
    write_file(
        research_dir / "2026-04-29-indexed-softpos" / "01-compliance-friction.md",
        """
        ---
        title: "Compliance vs product onboarding friction"
        date: 2026-04-29
        run_id: 2026-04-29-indexed-softpos
        role: angle
        sub_question: "Which SoftPOS onboarding friction is compliance mandated versus reducible?"
        confidence: verified
        tags: [softpos-onboarding, compliance-friction, progressive-kyc]
        sources:
          - url: https://example.com/secondary
            role: secondary
          - url: https://example.com/primary-a
            role: primary
          - url: https://example.com/tertiary
            role: tertiary
          - url: https://example.com/primary-b
            role: primary
          - url: https://example.com/primary-c
            role: primary
          - url: https://example.com/primary-d
            role: primary
        ---

        # Compliance vs product friction
        """,
    )
    write_file(
        research_dir / "2026-04-29-indexed-softpos" / "02-merchant-sentiment.md",
        """
        ---
        title: "Merchant NFC reliability sentiment"
        date: 2026-04-29
        run_id: 2026-04-29-indexed-softpos
        role: angle
        sub_question: "What do merchants complain about in tap to pay apps?"
        confidence: likely
        tags: [merchant-sentiment, nfc-reliability]
        sources:
          - url: https://example.com/community
            role: tertiary
        ---

        # Sentiment
        """,
    )
    write_file(
        research_dir / "2026-04-01-unindexed-android" / "01-android-sdk36.md",
        """
        ---
        title: "Android SDK 36 side effects"
        date: 2026-04-01
        run_id: 2026-04-01-unindexed-android
        role: angle
        sub_question: "What are Android SDK 36 Flutter side effects?"
        confidence: verified
        tags: [android-sdk-36, flutter]
        sources:
          - url: https://developer.android.com/example
            role: primary
        ---

        # Android SDK 36
        """,
    )
    write_file(
        research_dir / "_archive" / "2026-04-30-archived" / "01-archived.md",
        """
        ---
        title: "Archived hidden result"
        date: 2026-04-30
        run_id: 2026-04-30-archived
        role: angle
        tags: [archived-hidden-token]
        ---
        """,
    )
    return research_dir


def run_prior(research_dir: Path, query: str, *args: str) -> dict:
    completed = subprocess.run(
        ["uv", "run", str(SCRIPT), "prior", query, "--research-dir", str(research_dir), *args],
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return json.loads(completed.stdout)


def test_prior_returns_file_level_results_with_core_metadata(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    result = run_prior(research_dir, "softpos onboarding compliance friction", "--limit", "3")

    assert result["metadata"]["search_unit"] == "file"
    assert result["metadata"]["total_files_indexed"] == 4
    first = result["results"][0]
    assert first["file"].endswith("01-compliance-friction.md")
    assert first["role"] == "angle"
    assert first["run_id"] == "2026-04-29-indexed-softpos"
    assert first["run_title"] == "Indexed SoftPOS Run"
    assert first["confidence"] == "verified"
    assert first["index_bullet"].startswith("SoftPOS onboarding friction splits")
    assert 0 <= first["score"] <= 1
    assert any(match.startswith("tags:") for match in first["matched_on"])


def test_prior_scans_filesystem_even_when_run_is_not_in_index(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    result = run_prior(research_dir, "Android SDK 36 Flutter side effects", "--limit", "2")

    files = [item["file"] for item in result["results"]]
    assert any(file.endswith("01-android-sdk36.md") for file in files)


def test_prior_filters_weak_matches_by_default_but_allows_broad_recall(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    default_result = run_prior(research_dir, "summary", "--limit", "10")
    broad_result = run_prior(research_dir, "summary", "--limit", "10", "--min-score", "0")

    assert default_result["results"] == []
    assert len(broad_result["results"]) > 0


def test_prior_caps_sources_and_prioritizes_primary_sources(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    result = run_prior(research_dir, "softpos onboarding compliance friction", "--limit", "1")

    sources = result["results"][0]["sources"]
    assert [source["url"] for source in sources] == [
        "https://example.com/primary-a",
        "https://example.com/primary-b",
        "https://example.com/primary-c",
        "https://example.com/primary-d",
        "https://example.com/secondary",
    ]
    assert "https://example.com/tertiary" not in [source["url"] for source in sources]


def test_prior_excludes_archive_directories(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    result = run_prior(research_dir, "archived hidden token", "--limit", "10", "--min-score", "0")

    assert result["results"] == []


def test_prior_works_without_index_file(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)
    (research_dir / "INDEX.md").unlink()

    result = run_prior(research_dir, "Android SDK 36 Flutter side effects", "--limit", "2")

    assert result["metadata"]["total_files_indexed"] == 4
    assert result["results"][0]["file"].endswith("01-android-sdk36.md")
    assert result["results"][0]["index_bullet"] == ""


def test_prior_since_filters_by_file_date_and_run_id_fallback(tmp_path: Path) -> None:
    research_dir = tmp_path / "Research"
    today = datetime.now(timezone.utc).date()
    old_day = today - timedelta(days=90)
    today_text = today.strftime("%Y-%m-%d")
    old_text = old_day.strftime("%Y-%m-%d")

    write_file(
        research_dir / f"{today_text}-fresh-fallback" / "01-fresh.md",
        f"""
        ---
        title: "Fresh retention fallback result"
        run_id: {today_text}-fresh-fallback
        role: angle
        sub_question: "fresh retention fallback unique"
        tags: [fresh-retention]
        ---
        """,
    )
    write_file(
        research_dir / f"{old_text}-old-fallback" / "01-old.md",
        f"""
        ---
        title: "Old retention fallback result"
        run_id: {old_text}-old-fallback
        role: angle
        sub_question: "fresh retention fallback unique"
        tags: [fresh-retention]
        ---
        """,
    )

    result = run_prior(research_dir, "fresh retention fallback unique", "--since", "30d", "--limit", "10")

    files = [item["file"] for item in result["results"]]
    assert any(file.endswith("01-fresh.md") for file in files)
    assert not any(file.endswith("01-old.md") for file in files)


def test_prior_demotes_synthesis_when_angle_has_equivalent_match(tmp_path: Path) -> None:
    research_dir = tmp_path / "Research"
    write_file(
        research_dir / "2026-04-29-equal-match" / "00-synthesis.md",
        """
        ---
        title: "Equal alpha beta gamma"
        date: 2026-04-29
        run_id: 2026-04-29-equal-match
        role: synthesis
        query: "alpha beta gamma"
        tags: [alpha-beta-gamma]
        ---
        """,
    )
    write_file(
        research_dir / "2026-04-29-equal-match" / "01-angle.md",
        """
        ---
        title: "Equal alpha beta gamma"
        date: 2026-04-29
        run_id: 2026-04-29-equal-match
        role: angle
        sub_question: "alpha beta gamma"
        tags: [alpha-beta-gamma]
        ---
        """,
    )

    result = run_prior(research_dir, "alpha beta gamma", "--limit", "2")

    assert [item["role"] for item in result["results"]] == ["angle", "synthesis"]
    assert result["results"][0]["score"] > result["results"][1]["score"]


def test_prior_rejects_out_of_range_min_score(tmp_path: Path) -> None:
    research_dir = make_fixture(tmp_path)

    completed = subprocess.run(
        [
            "uv",
            "run",
            str(SCRIPT),
            "prior",
            "softpos",
            "--research-dir",
            str(research_dir),
            "--min-score",
            "1.5",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 1
    result = json.loads(completed.stdout)
    assert result["success"] is False
    assert result["error"]["code"] == "FILESYSTEM_ERROR"
    assert "--min-score" in result["error"]["message"]
