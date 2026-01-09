#!/usr/bin/env python3
"""
CLI tool to pre-generate Pimsleur lessons.

This script generates lesson scripts and audio files for the Pimsleur
language learning method. It can generate individual units, ranges,
or all units across levels.

Usage:
    # Generate a single unit
    python scripts/generate_pimsleur_lessons.py --level 1 --unit 1

    # Generate a range of units
    python scripts/generate_pimsleur_lessons.py --level 1 --start 1 --end 10

    # Generate all units for a level
    python scripts/generate_pimsleur_lessons.py --level 1

    # Generate all available units (with vocabulary data)
    python scripts/generate_pimsleur_lessons.py --all

    # Script-only mode (no audio generation)
    python scripts/generate_pimsleur_lessons.py --level 1 --unit 1 --script-only

    # Force overwrite existing files
    python scripts/generate_pimsleur_lessons.py --level 1 --unit 1 --force

    # Show available units
    python scripts/generate_pimsleur_lessons.py --list

Environment Variables:
    OPENROUTER_API_KEY - Required for LLM script generation
    OPENROUTER_MODEL - Model to use for generation
    VOICEMAKER_API_KEY - Required for TTS audio generation
    DB_DSN - PostgreSQL connection string (for storing lessons)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Verify required environment variables are set."""
    required_vars = ["OPENROUTER_API_KEY", "OPENROUTER_MODEL"]
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("Please set these variables or create a .env file")
        sys.exit(1)


def get_output_dir(base_dir: str, lang: str, level: int) -> Path:
    """Get output directory for a specific language and level."""
    output_dir = Path(base_dir) / lang / f"level_{level:02d}"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ask_overwrite(filepath: Path, file_type: str) -> bool:
    """Ask user if they want to overwrite an existing file."""
    response = input(f"{file_type} already exists: {filepath}\nOverwrite? [y/N]: ")
    return response.lower() in ("y", "yes")


def list_available_units(lang_code: str):
    """List all available units with vocabulary data."""
    from bot.pimsleur.vocabulary_banks import VocabularyBank

    bank = VocabularyBank(lang_code)

    logger.info(f"Available units for {lang_code}:")

    for level in [1, 2, 3]:
        available = bank.get_available_units(level)
        logger.info(f"\n  Level {level}: {len(available)} units with content")
        for unit_num in available:
            unit = bank.get_unit(level, unit_num)
            if unit:
                logger.info(f"    Unit {unit_num:02d}: {unit['title']}")
                logger.info(f"             Vocabulary: {len(unit['vocabulary'])} words")


def generate_unit(
    lang_code: str,
    level: int,
    unit_num: int,
    output_dir: Path,
    script_only: bool = False,
    save_to_db: bool = True,
    force: bool = False,
) -> dict:
    """
    Generate a single Pimsleur unit.

    Args:
        lang_code: Language code (e.g., "is")
        level: Pimsleur level (1, 2, 3)
        unit_num: Unit number (1-30)
        output_dir: Directory to save output files
        script_only: If True, skip audio generation
        save_to_db: If True, save to database
        force: If True, overwrite existing files without asking

    Returns:
        Dictionary with generation results
    """
    from bot.languages import get_language_config_by_code
    from bot.pimsleur.generator import PimsleurLessonGenerator
    from bot.pimsleur.audio_assembler import PimsleurAudioAssembler

    # Get unit data from vocabulary bank
    from bot.pimsleur.vocabulary_banks import VocabularyBank

    vocab_bank = VocabularyBank(lang_code)
    unit_data = vocab_bank.get_unit(level, unit_num)

    if not unit_data or not unit_data.get("vocabulary"):
        logger.warning(f"No vocabulary data for Level {level} Unit {unit_num}")
        logger.info("Unit will be generated with LLM-only content")

    # Check for existing files
    script_filename = f"{lang_code}_L{level:02d}_U{unit_num:02d}_script.json"
    script_path = output_dir / script_filename
    audio_filename = f"{lang_code}_L{level:02d}_U{unit_num:02d}.mp3"
    audio_path = output_dir / audio_filename

    # Check script file
    if script_path.exists() and not force:
        if not ask_overwrite(script_path, "Script file"):
            logger.info("Skipping script generation (file exists)")
            return {"success": False, "error": "Script file exists, skipped"}

    # Check audio file (only if not script-only mode)
    if not script_only and audio_path.exists() and not force:
        if not ask_overwrite(audio_path, "Audio file"):
            logger.info("Skipping audio generation (file exists)")
            script_only = True

    logger.info("=" * 60)
    title = unit_data["title"] if unit_data else f"Unit {unit_num}"
    logger.info(f"Generating Level {level} Unit {unit_num}: {title}")
    logger.info("=" * 60)

    # Get language config
    lang_config = get_language_config_by_code(lang_code)
    if not lang_config:
        logger.error(f"Unknown language code: {lang_code}")
        return {"success": False, "error": "Unknown language"}

    # Initialize generator
    generator = PimsleurLessonGenerator(lang_config)

    # Prepare vocabulary for generation
    vocab_new = []
    vocab_review = []

    if unit_data and unit_data.get("vocabulary"):
        vocab_new = [
            {
                "word_target": w[0],
                "word_native": w[1],
                "word_type": w[2],
                "phonetic": w[3] if len(w) > 3 else "",
            }
            for w in unit_data["vocabulary"]
        ]

        # Get review vocabulary from previous units
        for prev_unit in unit_data.get("review_from_units", []):
            if lang_code == "is":
                from bot.pimsleur.vocabulary_banks import VocabularyBank

                bank = VocabularyBank(lang_code)
                prev_data = bank.get_unit(level, prev_unit)
                if prev_data and prev_data.get("vocabulary"):
                    for w in prev_data["vocabulary"][:3]:  # Take 3 words from each
                        vocab_review.append(
                            {
                                "word_target": w[0],
                                "word_native": w[1],
                                "word_type": w[2],
                                "phonetic": w[3] if len(w) > 3 else "",
                            }
                        )

    # Generate lesson script
    logger.info("Generating lesson script via LLM...")
    logger.info(f"  New vocabulary: {len(vocab_new)} words")
    logger.info(f"  Review vocabulary: {len(vocab_review)} words")

    try:
        # Map level to CEFR for backwards compatibility with generator
        cefr_map = {1: "A1", 2: "A2", 3: "B1"}
        cefr_level = cefr_map.get(level, "A1")

        script = generator.generate_lesson_script(
            level=cefr_level,
            lesson_number=unit_num,
            title=title,
            theme=unit_data.get("categories", ["general"])[0] if unit_data else None,
        )

        # Enhance script with unit data
        if unit_data:
            script["pimsleur_level"] = level
            script["pimsleur_unit"] = unit_num
            script["opening_dialogue"] = unit_data.get("opening_dialogue", [])
            script["grammar_notes"] = unit_data.get("grammar_notes", [])
            script["phrases"] = unit_data.get("phrases", [])

    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        return {"success": False, "error": str(e)}

    # Save script JSON
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    logger.info(f"Script saved to: {script_path}")

    # Get script statistics
    stats = generator.get_script_statistics(script)
    logger.info(f"Script stats: {json.dumps(stats, indent=2)}")

    result = {
        "success": True,
        "level": level,
        "unit_number": unit_num,
        "script_path": str(script_path),
        "stats": stats,
    }

    # Generate audio if not script-only mode
    if not script_only:
        if not os.environ.get("VOICEMAKER_API_KEY"):
            logger.warning("VOICEMAKER_API_KEY not set, skipping audio generation")
        else:
            logger.info("Generating lesson audio...")
            assembler = PimsleurAudioAssembler(lang_code, level=level)

            # Estimate cost first
            cost = assembler.estimate_cost(script)
            logger.info(f"Estimated TTS cost: ${cost['estimated_cost_usd']:.2f}")

            def progress_callback(current, total):
                logger.info(f"Audio progress: {current}/{total} segments")

            try:
                assembler.generate_lesson_audio(
                    script=script,
                    output_path=str(audio_path),
                    progress_callback=progress_callback,
                )
                result["audio_path"] = str(audio_path)
                logger.info(f"Audio saved to: {audio_path}")
            except Exception as e:
                logger.error(f"Audio generation failed: {e}")
                result["audio_error"] = str(e)

    # Save to database if requested
    if save_to_db and os.environ.get("DB_DSN"):
        try:
            save_unit_to_db(
                lang_code=lang_code,
                level=level,
                unit_num=unit_num,
                script=script,
                script_path=str(script_path),
                audio_path=result.get("audio_path"),
            )
            result["saved_to_db"] = True
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            result["db_error"] = str(e)

    return result


def save_unit_to_db(
    lang_code: str,
    level: int,
    unit_num: int,
    script: dict,
    script_path: str,
    audio_path: str | None = None,
):
    """Save generated unit to database."""
    from bot.db.database import db_session
    from bot.db.models import PimsleurLesson

    # Map level to string for DB compatibility
    level_str = f"L{level}"

    with db_session() as session:
        # Check if lesson already exists
        existing = (
            session.query(PimsleurLesson)
            .filter_by(
                language_code=lang_code,
                level=level_str,
                lesson_number=unit_num,
            )
            .first()
        )

        if existing:
            # Update existing
            existing.script_json = json.dumps(script, ensure_ascii=False)
            existing.vocabulary_json = json.dumps(
                script.get("vocabulary_summary", []), ensure_ascii=False
            )
            if audio_path:
                existing.audio_file_path = audio_path
                existing.is_generated = True
            existing.updated_at = datetime.utcnow()
            logger.info("Updated existing unit in database")
        else:
            # Create new
            lesson = PimsleurLesson(
                language_code=lang_code,
                level=level_str,
                lesson_number=unit_num,
                title=script.get("title", f"Level {level} Unit {unit_num}"),
                description=script.get("theme", ""),
                duration_seconds=script.get("calculated_duration", 1800),
                audio_file_path=audio_path,
                script_json=json.dumps(script, ensure_ascii=False),
                vocabulary_json=json.dumps(
                    script.get("vocabulary_summary", []), ensure_ascii=False
                ),
                review_from_lessons=json.dumps(script.get("review_from_lessons", [])),
                is_generated=audio_path is not None,
            )
            session.add(lesson)
            logger.info("Created new unit in database")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Pimsleur lessons",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--lang",
        default="is",
        help="Language code (default: is for Icelandic)",
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        help="Pimsleur level to generate (1, 2, or 3)",
    )
    parser.add_argument(
        "--unit",
        type=int,
        help="Single unit number to generate (1-30)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Start unit number (default: 1)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=30,
        help="End unit number (default: 30)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all available units (with vocabulary data)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available units with vocabulary data",
    )
    parser.add_argument(
        "--output",
        default="data/pimsleur",
        help="Output directory (default: data/pimsleur)",
    )
    parser.add_argument(
        "--script-only",
        action="store_true",
        help="Generate scripts only, skip audio",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Don't save to database",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without doing it",
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files without asking",
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        list_available_units(args.lang)
        return

    # Validate arguments
    if not args.all and not args.level:
        parser.error("Either --level or --all is required (or use --list)")

    if args.unit and (args.unit < 1 or args.unit > 30):
        parser.error("Unit number must be between 1 and 30")

    # Setup environment
    setup_environment()

    # Determine which units to generate
    units_to_generate = []

    if args.all:
        # Generate only units with vocabulary data
        if args.lang == "is":
            from bot.pimsleur.vocabulary_banks import VocabularyBank

            bank = VocabularyBank(args.lang)
            for level in [1]:  # Currently only level 1
                available = bank.get_available_units(level)
                for unit_num in available:
                    units_to_generate.append((level, unit_num))
    elif args.unit:
        units_to_generate.append((args.level, args.unit))
    else:
        for unit_num in range(args.start, args.end + 1):
            units_to_generate.append((args.level, unit_num))

    logger.info(f"Will generate {len(units_to_generate)} units")

    if args.dry_run:
        logger.info("Dry run - showing units to generate:")
        for level, unit_num in units_to_generate:
            logger.info(f"  Level {level} Unit {unit_num}")
        return

    # Generate units
    results = []
    for level, unit_num in units_to_generate:
        output_dir = get_output_dir(args.output, args.lang, level)
        result = generate_unit(
            lang_code=args.lang,
            level=level,
            unit_num=unit_num,
            output_dir=output_dir,
            script_only=args.script_only,
            save_to_db=not args.no_db,
            force=args.force,
        )
        results.append(result)

        if not result["success"]:
            logger.error(f"Failed: {result.get('error')}")
            # Continue with next unit

    # Summary
    successful = sum(1 for r in results if r["success"])
    logger.info("=" * 60)
    logger.info(f"Generation complete: {successful}/{len(results)} successful")


if __name__ == "__main__":
    main()
