#!/usr/bin/env python3
"""
CLI tool to pre-generate Pimsleur lessons.

This script generates lesson scripts and audio files for the Pimsleur
language learning method. It can generate individual lessons, ranges,
or all 90 lessons across 3 CEFR levels (A1, A2, B1).

Usage:
    # Generate a single lesson
    python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1

    # Generate a range of lessons
    python scripts/generate_pimsleur_lessons.py --level A1 --start 1 --end 10

    # Generate all lessons for a level
    python scripts/generate_pimsleur_lessons.py --level A1

    # Generate all 90 lessons
    python scripts/generate_pimsleur_lessons.py --all

    # Script-only mode (no audio generation)
    python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1 --script-only

    # Force overwrite existing files
    python scripts/generate_pimsleur_lessons.py --level A1 --lesson 1 --force

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


def get_output_dir(base_dir: str, lang: str, level: str) -> Path:
    """Get output directory for a specific language and level."""
    output_dir = Path(base_dir) / lang / level
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def ask_overwrite(filepath: Path, file_type: str) -> bool:
    """Ask user if they want to overwrite an existing file."""
    response = input(f"{file_type} already exists: {filepath}\nOverwrite? [y/N]: ")
    return response.lower() in ("y", "yes")


def generate_lesson(
    lang_code: str,
    level: str,
    lesson_num: int,
    output_dir: Path,
    script_only: bool = False,
    save_to_db: bool = True,
    force: bool = False,
) -> dict:
    """
    Generate a single Pimsleur lesson.

    Args:
        lang_code: Language code (e.g., "is")
        level: CEFR level (A1, A2, B1)
        lesson_num: Lesson number (1-30)
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
    from bot.pimsleur.constants import LESSON_TITLES

    # Check for existing files
    script_filename = f"{lang_code}_{level}_L{lesson_num:02d}_script.json"
    script_path = output_dir / script_filename
    audio_filename = f"{lang_code}_{level}_L{lesson_num:02d}.mp3"
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
            # Still might want to generate script only
            script_only = True

    logger.info(f"=" * 60)
    logger.info(f"Generating {level} Lesson {lesson_num}")
    logger.info(f"=" * 60)

    # Get language config
    lang_config = get_language_config_by_code(lang_code)
    if not lang_config:
        logger.error(f"Unknown language code: {lang_code}")
        return {"success": False, "error": "Unknown language"}

    # Initialize generator
    generator = PimsleurLessonGenerator(lang_config)

    # Generate lesson script
    logger.info("Generating lesson script via LLM...")
    try:
        script = generator.generate_lesson_script(
            level=level,
            lesson_number=lesson_num,
        )
    except Exception as e:
        logger.error(f"Failed to generate script: {e}")
        return {"success": False, "error": str(e)}

    # Save script JSON (script_path already defined above)
    with open(script_path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=2)
    logger.info(f"Script saved to: {script_path}")

    # Get script statistics
    stats = generator.get_script_statistics(script)
    logger.info(f"Script stats: {json.dumps(stats, indent=2)}")

    result = {
        "success": True,
        "level": level,
        "lesson_number": lesson_num,
        "script_path": str(script_path),
        "stats": stats,
    }

    # Generate audio if not script-only mode
    if not script_only:
        if not os.environ.get("VOICEMAKER_API_KEY"):
            logger.warning("VOICEMAKER_API_KEY not set, skipping audio generation")
        else:
            logger.info("Generating lesson audio...")
            assembler = PimsleurAudioAssembler(lang_code)

            # Estimate cost first
            cost = assembler.estimate_cost(script)
            logger.info(f"Estimated TTS cost: ${cost['estimated_cost_usd']:.2f}")

            # audio_path already defined above

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
            save_lesson_to_db(
                lang_code=lang_code,
                level=level,
                lesson_num=lesson_num,
                script=script,
                script_path=str(script_path),
                audio_path=result.get("audio_path"),
            )
            result["saved_to_db"] = True
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            result["db_error"] = str(e)

    return result


def save_lesson_to_db(
    lang_code: str,
    level: str,
    lesson_num: int,
    script: dict,
    script_path: str,
    audio_path: str = None,
):
    """Save generated lesson to database."""
    from bot.db.database import db_session
    from bot.db.models import PimsleurLesson

    with db_session() as session:
        # Check if lesson already exists
        existing = session.query(PimsleurLesson).filter_by(
            language_code=lang_code,
            level=level,
            lesson_number=lesson_num,
        ).first()

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
            logger.info("Updated existing lesson in database")
        else:
            # Create new
            lesson = PimsleurLesson(
                language_code=lang_code,
                level=level,
                lesson_number=lesson_num,
                title=script.get("title", f"{level} Lesson {lesson_num}"),
                description=script.get("theme", ""),
                duration_seconds=script.get("calculated_duration", 1800),
                audio_file_path=audio_path,
                script_json=json.dumps(script, ensure_ascii=False),
                vocabulary_json=json.dumps(
                    script.get("vocabulary_summary", []), ensure_ascii=False
                ),
                review_from_lessons=json.dumps(
                    script.get("review_from_lessons", [])
                ),
                is_generated=audio_path is not None,
            )
            session.add(lesson)
            logger.info("Created new lesson in database")


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
        choices=["A1", "A2", "B1"],
        help="CEFR level to generate",
    )
    parser.add_argument(
        "--lesson",
        type=int,
        help="Single lesson number to generate (1-30)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Start lesson number (default: 1)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=30,
        help="End lesson number (default: 30)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all 90 lessons (A1, A2, B1)",
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

    # Validate arguments
    if not args.all and not args.level:
        parser.error("Either --level or --all is required")

    if args.lesson and (args.lesson < 1 or args.lesson > 30):
        parser.error("Lesson number must be between 1 and 30")

    # Setup environment
    setup_environment()

    # Determine which lessons to generate
    lessons_to_generate = []

    if args.all:
        for level in ["A1", "A2", "B1"]:
            for lesson_num in range(1, 31):
                lessons_to_generate.append((level, lesson_num))
    elif args.lesson:
        lessons_to_generate.append((args.level, args.lesson))
    else:
        for lesson_num in range(args.start, args.end + 1):
            lessons_to_generate.append((args.level, lesson_num))

    logger.info(f"Will generate {len(lessons_to_generate)} lessons")

    if args.dry_run:
        logger.info("Dry run - showing lessons to generate:")
        for level, lesson_num in lessons_to_generate:
            logger.info(f"  {level} Lesson {lesson_num}")
        return

    # Generate lessons
    results = []
    for level, lesson_num in lessons_to_generate:
        output_dir = get_output_dir(args.output, args.lang, level)
        result = generate_lesson(
            lang_code=args.lang,
            level=level,
            lesson_num=lesson_num,
            output_dir=output_dir,
            script_only=args.script_only,
            save_to_db=not args.no_db,
            force=args.force,
        )
        results.append(result)

        if not result["success"]:
            logger.error(f"Failed: {result.get('error')}")
            # Continue with next lesson

    # Summary
    successful = sum(1 for r in results if r["success"])
    logger.info(f"=" * 60)
    logger.info(f"Generation complete: {successful}/{len(results)} successful")


if __name__ == "__main__":
    main()
