"""
Module for generating random persons and populating the persons table.

Supports multi-language generation based on TARGET_LANGUAGES environment variable.
"""
import logging
import random
from sqlalchemy import delete, func
from sqlalchemy.orm import joinedload
from bot.db.database import get_db_session
from bot.db.models import Person, Name, Job, City, Activity
from bot.languages import get_language_config, get_all_language_configs, get_language_config_by_code

# Get logger for this module
logger = logging.getLogger(__name__)

PERSONS_PER_LANGUAGE = 30


def clear_and_fill_persons_table():
    """
    Clear the persons table and fill it with random persons for all configured languages.
    This function should be called at bot startup.
    """
    logger.info("Clearing and filling persons table")
    session = get_db_session()

    try:
        # Clear the persons table
        logger.info("Clearing persons table")
        session.execute(delete(Person))
        session.commit()

        # Get all configured languages
        lang_configs = get_all_language_configs()

        total_persons = 0
        for lang_config in lang_configs:
            code = lang_config.code
            logger.info(f"Generating persons for {lang_config.name} ({code})")

            # Get seed data filtered by language_code
            names = session.query(Name).filter(Name.language_code == code).all()
            jobs = session.query(Job).filter(Job.language_code == code).all()
            cities = session.query(City).filter(City.language_code == code).all()
            weekend_activities = session.query(Activity).filter(
                Activity.type == "weekend",
                Activity.language_code == code
            ).all()
            plan_activities = session.query(Activity).filter(
                Activity.type == "plan",
                Activity.language_code == code
            ).all()

            # Check if we have enough data to generate persons
            if not names or not jobs or not cities:
                logger.warning(f"Not enough data to generate persons for {lang_config.name}")
                continue

            # Generate random persons for this language
            persons = []
            for _ in range(PERSONS_PER_LANGUAGE):
                # Select random data
                name = random.choice(names)
                job = random.choice(jobs)
                city = random.choice(cities)
                age = random.randint(20, 65)
                children = random.randint(0, 3)

                # Select random activities if available
                weekend_activity = random.choice(weekend_activities).activity if weekend_activities else None
                plan_activity = random.choice(plan_activities).activity if plan_activities else None

                # Create a new person with language_code
                person = Person(
                    name_id=name.id,
                    age=age,
                    origin=city.id,
                    job_id=job.id,
                    children=children,
                    weekend_activity=weekend_activity,
                    plan_activity=plan_activity,
                    language_code=code
                )
                persons.append(person)

            # Add all persons to the database
            session.add_all(persons)
            total_persons += len(persons)
            logger.info(f"Generated {len(persons)} persons for {lang_config.name}")

        session.commit()
        logger.info(f"Successfully added {total_persons} persons to the database")

    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing and filling persons table: {e}")
        raise
    finally:
        session.close()

def get_random_person_data(language_code: str = None):
    """
    Fetch a random person from the database and format their data for use in a prompt.

    Args:
        language_code: ISO language code to filter persons (e.g., 'de', 'is').
                       If None, uses the default TARGET_LANGUAGE.

    Returns:
        dict: A dictionary containing formatted person data for use in a prompt
    """
    # Determine which language to use
    if language_code:
        lang_config = get_language_config_by_code(language_code)
        if not lang_config:
            logger.warning(f"Unknown language code: {language_code}, falling back to default")
            lang_config = get_language_config()
            language_code = lang_config.code
    else:
        lang_config = get_language_config()
        language_code = lang_config.code

    logger.info(f"Fetching random person from database for language: {language_code}")
    session = get_db_session()

    try:
        # Get a random person with related data using eager loading (avoids N+1 queries)
        person = session.query(Person).options(
            joinedload(Person.name),
            joinedload(Person.city),
            joinedload(Person.job)
        ).filter(
            Person.language_code == language_code
        ).order_by(func.random()).limit(1).first()

        if not person:
            logger.error(f"No persons found in database for language: {language_code}")
            return None

        # Access eagerly loaded relationships
        name = person.name
        city = person.city
        job = person.job

        # Determine gender based on name using language-specific rules
        gender = lang_config.detect_gender(name.first_name)

        # Generate ages of children if the person has children
        children_ages = []
        if person.children and person.children > 0:
            # Generate random ages for children between 1 and 18
            children_ages = [random.randint(1, 18) for _ in range(person.children)]
            children_ages.sort()  # Sort ages in ascending order

        # Format the data for use in a prompt
        person_data = {
            "name": f"{name.first_name} {name.last_name}",
            "gender": gender,
            "age": person.age,
            "origin": city.name,
            "job_title": job.title,
            "job_workplace": job.workplace,
            "number_of_children": person.children or 0,
            "age_of_children": ", ".join(map(str, children_ages)) if children_ages else "N/A",
            "weekend_activity": person.weekend_activity or "staying at home",
            "current_plan": person.plan_activity or "relaxing",
            "language_code": language_code
        }

        logger.info(f"Successfully fetched random person: {name.first_name} {name.last_name}")
        return person_data

    except Exception as e:
        logger.error(f"Error fetching random person: {e}")
        return None
    finally:
        session.close()
