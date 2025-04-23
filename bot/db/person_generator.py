"""
Module for generating random persons and populating the persons table.
"""
import logging
import random
from sqlalchemy import delete, func
from bot.db.database import get_db_session
from bot.db.models import Person, Name, Job, City, Activity

# Get logger for this module
logger = logging.getLogger(__name__)

def clear_and_fill_persons_table():
    """
    Clear the persons table and fill it with 30 random persons.
    This function should be called at bot startup.
    """
    logger.info("Clearing and filling persons table")
    session = get_db_session()

    try:
        # Clear the persons table
        logger.info("Clearing persons table")
        session.execute(delete(Person))
        session.commit()

        # Get all names, jobs, cities, and activities from the database
        names = session.query(Name).all()
        jobs = session.query(Job).all()
        cities = session.query(City).all()
        weekend_activities = session.query(Activity).filter(Activity.type == "weekend").all()
        plan_activities = session.query(Activity).filter(Activity.type == "plan").all()

        # Check if we have enough data to generate persons
        if not names or not jobs or not cities:
            logger.error("Not enough data to generate persons")
            return

        # Generate 30 random persons
        logger.info("Generating 30 random persons")
        persons = []
        for _ in range(30):
            # Select random data
            name = random.choice(names)
            job = random.choice(jobs)
            city = random.choice(cities)
            age = random.randint(20, 65)  # Random age between 20 and 65
            children = random.randint(0, 3)  # Random number of children between 0 and 3

            # Select random activities if available
            weekend_activity = random.choice(weekend_activities).activity if weekend_activities else None
            plan_activity = random.choice(plan_activities).activity if plan_activities else None

            # Create a new person
            person = Person(
                name_id=name.id,
                age=age,
                origin=city.id,
                job_id=job.id,
                children=children,
                weekend_activity=weekend_activity,
                plan_activity=plan_activity
            )
            persons.append(person)

        # Add all persons to the database
        session.add_all(persons)
        session.commit()
        logger.info(f"Successfully added {len(persons)} persons to the database")

    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing and filling persons table: {e}")
        raise
    finally:
        session.close()

def get_random_person_data():
    """
    Fetch a random person from the database and format their data for use in a prompt.

    Returns:
        dict: A dictionary containing formatted person data for use in a prompt
    """
    logger.info("Fetching random person from database")
    session = get_db_session()

    try:
        # Get a random person from the database
        person_count = session.query(func.count(Person.id)).scalar()
        if person_count == 0:
            logger.error("No persons found in database")
            return None

        random_offset = random.randint(0, person_count - 1)
        person = session.query(Person).offset(random_offset).limit(1).first()

        if not person:
            logger.error("Failed to fetch random person")
            return None

        # Get related data
        name = session.query(Name).filter(Name.id == person.name_id).first()
        city = session.query(City).filter(City.id == person.origin).first()
        job = session.query(Job).filter(Job.id == person.job_id).first()

        # Determine gender based on name (simplified approach)
        # In a real application, you might want to store gender in the database
        # or use a more sophisticated approach to determine gender
        # For now, we'll just assume names ending with 'a' are female, others are male
        gender = "female" if name.first_name.endswith('a') else "male"

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
            "current_plan": person.plan_activity or "relaxing"
        }

        logger.info(f"Successfully fetched random person: {name.first_name} {name.last_name}")
        return person_data

    except Exception as e:
        logger.error(f"Error fetching random person: {e}")
        return None
    finally:
        session.close()
