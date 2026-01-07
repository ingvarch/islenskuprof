"""
Constants and curriculum data for Pimsleur lessons.
"""

# Lesson timing constants (in seconds)
LESSON_DURATION_TARGET = 1800  # 30 minutes
PAUSE_ANTICIPATION = 4  # Pause for user to formulate response
PAUSE_REPETITION = 3  # Pause for user to repeat
PAUSE_BETWEEN_SEGMENTS = 1  # Small pause between segments
PAUSE_BETWEEN_WORDS = 2  # Pause between new word introduction

# Spaced repetition intervals (in seconds from word introduction)
SPACED_REPETITION_INTERVALS = [5, 25, 120, 600, 1200]  # 5s, 25s, 2min, 10min, 20min

# Cross-lesson review: which previous lessons to review from
# For lesson N, review vocabulary from lessons N-offset
CROSS_LESSON_REVIEW_OFFSETS = [1, 2, 5, 10]

# Voice configuration
VOICES = {
    "narrator": {
        "voice_id": "ai3-Jony",
        "language_code": "en-US",
        "description": "English narrator for instructions",
    },
    "native_female_is": {
        "voice_id": "ai3-is-IS-Svana",
        "language_code": "is-IS",
        "description": "Icelandic female native speaker",
    },
    "native_male_is": {
        "voice_id": "ai3-is-IS-Ulfr",
        "language_code": "is-IS",
        "description": "Icelandic male native speaker",
    },
    "native_female_de": {
        "voice_id": "pro1-Helena",
        "language_code": "de-DE",
        "description": "German female native speaker",
    },
    "native_male_de": {
        "voice_id": "pro1-Thomas",
        "language_code": "de-DE",
        "description": "German male native speaker",
    },
}

# Vocabulary curriculum by CEFR level
VOCABULARY_CURRICULUM = {
    "A1": {
        "total_vocabulary": 500,
        "new_words_per_lesson": 15,
        "review_words_per_lesson": 10,
        "sentence_length_max": 8,
        "themes": [
            # Lessons 1-5: Basics
            "greetings_and_farewells",
            "introductions",
            "numbers_1_to_10",
            "yes_no_thanks",
            "basic_questions",
            # Lessons 6-10: People & Places
            "family_members",
            "countries_and_nationalities",
            "professions_basic",
            "places_in_city",
            "directions_basic",
            # Lessons 11-15: Daily Life
            "time_and_days",
            "food_and_drinks_basic",
            "shopping_basic",
            "weather_basic",
            "colors",
            # Lessons 16-20: Actions
            "daily_routines",
            "common_verbs",
            "likes_and_dislikes",
            "abilities",
            "needs_and_wants",
            # Lessons 21-25: Social
            "polite_expressions",
            "at_restaurant",
            "at_hotel",
            "telephone_basic",
            "emergencies",
            # Lessons 26-30: Review & Integration
            "travel_phrases",
            "small_talk",
            "review_greetings_intro",
            "review_daily_life",
            "comprehensive_review",
        ],
    },
    "A2": {
        "total_vocabulary": 1000,
        "new_words_per_lesson": 20,
        "review_words_per_lesson": 15,
        "sentence_length_max": 12,
        "themes": [
            # Lessons 1-5: Expanding Basics
            "numbers_to_100",
            "months_and_dates",
            "describing_people",
            "describing_places",
            "describing_things",
            # Lessons 6-10: Activities
            "hobbies_and_sports",
            "entertainment",
            "weekend_activities",
            "holidays",
            "celebrations",
            # Lessons 11-15: Practical Situations
            "at_doctor",
            "at_pharmacy",
            "at_bank",
            "at_post_office",
            "public_transport",
            # Lessons 16-20: Home & Work
            "rooms_and_furniture",
            "household_chores",
            "workplace_vocabulary",
            "colleagues_and_meetings",
            "schedules",
            # Lessons 21-25: Communication
            "opinions_and_preferences",
            "making_plans",
            "giving_directions",
            "complaints_and_requests",
            "comparisons",
            # Lessons 26-30: Integration
            "storytelling_past",
            "future_plans",
            "review_practical",
            "review_communication",
            "comprehensive_review",
        ],
    },
    "B1": {
        "total_vocabulary": 2000,
        "new_words_per_lesson": 25,
        "review_words_per_lesson": 20,
        "sentence_length_max": 18,
        "themes": [
            # Lessons 1-5: Abstract Concepts
            "emotions_and_feelings",
            "relationships",
            "personality_traits",
            "values_and_beliefs",
            "dreams_and_goals",
            # Lessons 6-10: Society
            "news_and_media",
            "environment",
            "technology",
            "education",
            "health_and_fitness",
            # Lessons 11-15: Professional
            "job_interviews",
            "business_vocabulary",
            "presentations",
            "negotiations",
            "workplace_culture",
            # Lessons 16-20: Complex Situations
            "problem_solving",
            "giving_advice",
            "hypothetical_situations",
            "explaining_processes",
            "cause_and_effect",
            # Lessons 21-25: Culture
            "traditions_and_customs",
            "arts_and_literature",
            "history_basic",
            "current_events",
            "cultural_differences",
            # Lessons 26-30: Mastery
            "formal_vs_informal",
            "idioms_and_expressions",
            "review_abstract",
            "review_professional",
            "comprehensive_mastery",
        ],
    },
}

# Icelandic core vocabulary for A1 (first 200 words)
# Structure: (icelandic, english, type, phonetic)
ICELANDIC_CORE_VOCABULARY_A1 = [
    # Greetings (Lessons 1-2)
    ("hæ", "hello", "greeting", "hai"),
    ("bless", "goodbye", "greeting", "bless"),
    ("góðan dag", "good day", "greeting", "GOH-than dahg"),
    ("gott kvöld", "good evening", "greeting", "goht kvuhld"),
    ("góða nótt", "good night", "greeting", "GOH-tha noht"),
    ("takk", "thank you", "courtesy", "tahk"),
    ("takk fyrir", "thank you (for)", "courtesy", "tahk FIR-ir"),
    ("gerðu svo vel", "you're welcome", "courtesy", "GYER-thu svo vel"),

    # Basic responses (Lessons 3-4)
    ("já", "yes", "response", "yow"),
    ("nei", "no", "response", "nay"),
    ("kannski", "maybe", "response", "KAHN-skee"),
    ("ég veit ekki", "I don't know", "phrase", "yeh vayt EH-kee"),
    ("afsakið", "excuse me", "courtesy", "AHF-sah-kith"),
    ("fyrirgefðu", "sorry", "courtesy", "FIR-ir-GYEV-thu"),

    # Introductions (Lessons 5-6)
    ("ég heiti", "my name is", "phrase", "yeh HAY-tee"),
    ("hvað heitir þú", "what is your name", "question", "kvath HAY-tir thoo"),
    ("ég er frá", "I am from", "phrase", "yeh er frow"),
    ("ég er íslenskur", "I am Icelandic (m)", "phrase", "yeh er EES-len-skur"),
    ("ég er íslensk", "I am Icelandic (f)", "phrase", "yeh er EES-lensk"),
    ("það er gott að hitta þig", "nice to meet you", "phrase", "thahth er goht ahth HIT-tah theeg"),

    # Numbers 1-10 (Lesson 7)
    ("einn", "one", "number", "aytn"),
    ("tveir", "two", "number", "tvair"),
    ("þrír", "three", "number", "threer"),
    ("fjórir", "four", "number", "FYOH-rir"),
    ("fimm", "five", "number", "fim"),
    ("sex", "six", "number", "seks"),
    ("sjö", "seven", "number", "syoh"),
    ("átta", "eight", "number", "OHT-ta"),
    ("níu", "nine", "number", "nee-u"),
    ("tíu", "ten", "number", "tee-u"),

    # Questions (Lessons 8-9)
    ("hvað", "what", "question_word", "kvath"),
    ("hver", "who", "question_word", "kver"),
    ("hvar", "where", "question_word", "kvar"),
    ("hvenær", "when", "question_word", "KVEN-air"),
    ("hvers vegna", "why", "question_word", "KVERS VEG-na"),
    ("hvernig", "how", "question_word", "KVER-nig"),
    ("hvað kostar", "how much does it cost", "question", "kvath KOS-tar"),

    # Family (Lessons 10-11)
    ("fjölskylda", "family", "noun", "FYUHL-skil-da"),
    ("mamma", "mother", "noun", "MAM-ma"),
    ("pabbi", "father", "noun", "PAB-bee"),
    ("systir", "sister", "noun", "SIS-tir"),
    ("bróðir", "brother", "noun", "BROH-thir"),
    ("barn", "child", "noun", "barn"),
    ("börn", "children", "noun", "buhrn"),
    ("eiginkona", "wife", "noun", "AY-gin-KO-na"),
    ("eiginmaður", "husband", "noun", "AY-gin-MAH-thur"),

    # Common verbs (Lessons 12-14)
    ("að vera", "to be", "verb", "ahth VE-ra"),
    ("að hafa", "to have", "verb", "ahth HA-va"),
    ("að fara", "to go", "verb", "ahth FA-ra"),
    ("að koma", "to come", "verb", "ahth KO-ma"),
    ("að tala", "to speak", "verb", "ahth TA-la"),
    ("að skilja", "to understand", "verb", "ahth SKIL-ya"),
    ("að borða", "to eat", "verb", "ahth BOR-tha"),
    ("að drekka", "to drink", "verb", "ahth DREK-ka"),
    ("að sofa", "to sleep", "verb", "ahth SO-va"),
    ("að vinna", "to work", "verb", "ahth VIN-na"),

    # Present tense forms (with "ég" - I)
    ("ég er", "I am", "verb_form", "yeh er"),
    ("ég hef", "I have", "verb_form", "yeh hev"),
    ("ég fer", "I go", "verb_form", "yeh fer"),
    ("ég kem", "I come", "verb_form", "yeh kem"),
    ("ég tala", "I speak", "verb_form", "yeh TA-la"),
    ("ég skil", "I understand", "verb_form", "yeh skil"),

    # Places (Lessons 15-16)
    ("heima", "home", "noun", "HAY-ma"),
    ("vinna", "work", "noun", "VIN-na"),
    ("verslun", "store", "noun", "VERS-lun"),
    ("veitingahús", "restaurant", "noun", "VAY-ting-a-hoos"),
    ("hótel", "hotel", "noun", "HOH-tel"),
    ("flugvöllur", "airport", "noun", "FLUG-vuh-lur"),
    ("stöð", "station", "noun", "stuhth"),
    ("sjúkrahús", "hospital", "noun", "SYOO-kra-hoos"),

    # Food & Drink (Lessons 17-18)
    ("matur", "food", "noun", "MA-tur"),
    ("vatn", "water", "noun", "vahtn"),
    ("kaffi", "coffee", "noun", "KAF-fee"),
    ("te", "tea", "noun", "teh"),
    ("brauð", "bread", "noun", "broith"),
    ("fiskur", "fish", "noun", "FIS-kur"),
    ("kjöt", "meat", "noun", "kyuht"),
    ("grænmeti", "vegetables", "noun", "GRYN-me-tee"),

    # Time (Lessons 19-20)
    ("klukkan", "the clock / it's ... o'clock", "noun", "KLUK-kan"),
    ("í dag", "today", "time", "ee dahg"),
    ("á morgun", "tomorrow", "time", "ow MOR-gun"),
    ("í gær", "yesterday", "time", "ee gair"),
    ("núna", "now", "time", "NOO-na"),
    ("seinna", "later", "time", "SAYT-na"),
    ("dagur", "day", "noun", "DA-gur"),
    ("vika", "week", "noun", "VEE-ka"),

    # Days of week (Lesson 21)
    ("mánudagur", "Monday", "day", "MOW-nu-DA-gur"),
    ("þriðjudagur", "Tuesday", "day", "THRITH-yu-DA-gur"),
    ("miðvikudagur", "Wednesday", "day", "MITH-vi-ku-DA-gur"),
    ("fimmtudagur", "Thursday", "day", "FIM-tu-DA-gur"),
    ("föstudagur", "Friday", "day", "FUH-stu-DA-gur"),
    ("laugardagur", "Saturday", "day", "LOI-gar-DA-gur"),
    ("sunnudagur", "Sunday", "day", "SUN-nu-DA-gur"),

    # Weather (Lesson 22)
    ("veður", "weather", "noun", "VE-thur"),
    ("sólin skín", "the sun is shining", "phrase", "SOH-lin skeen"),
    ("það rignir", "it's raining", "phrase", "thahth RIG-nir"),
    ("það snjóar", "it's snowing", "phrase", "thahth SNYOH-ar"),
    ("kalt", "cold", "adjective", "kahlt"),
    ("heitt", "hot", "adjective", "hayt"),
    ("vindur", "wind", "noun", "VIN-dur"),

    # Shopping (Lessons 23-24)
    ("að kaupa", "to buy", "verb", "ahth KOI-pa"),
    ("að borga", "to pay", "verb", "ahth BOR-ga"),
    ("peningur", "money", "noun", "PEN-ing-ur"),
    ("króna", "krona (currency)", "noun", "KROH-na"),
    ("ódýrt", "cheap", "adjective", "OH-deert"),
    ("dýrt", "expensive", "adjective", "deert"),
    ("stórt", "big", "adjective", "stohrt"),
    ("lítið", "small", "adjective", "LEE-tith"),

    # Colors (Lesson 25)
    ("rauður", "red", "adjective", "ROI-thur"),
    ("grænn", "green", "adjective", "graitn"),
    ("blár", "blue", "adjective", "blow-r"),
    ("gulur", "yellow", "adjective", "GU-lur"),
    ("svartur", "black", "adjective", "SVAR-tur"),
    ("hvítur", "white", "adjective", "KVEE-tur"),

    # Useful phrases (Lessons 26-30)
    ("ég tala ekki íslensku", "I don't speak Icelandic", "phrase", "yeh TA-la EH-kee EES-len-sku"),
    ("talarðu ensku", "do you speak English", "question", "TA-lar-thu EN-sku"),
    ("ég skil ekki", "I don't understand", "phrase", "yeh skil EH-kee"),
    ("geturðu endurtekið", "can you repeat", "question", "GE-tur-thu EN-dur-te-kith"),
    ("hvar er", "where is", "question", "kvar er"),
    ("ég þarf", "I need", "phrase", "yeh tharf"),
    ("ég vil", "I want", "phrase", "yeh vil"),
    ("má ég fá", "may I have", "phrase", "mow yeh fow"),
]

# Lesson title templates
LESSON_TITLES = {
    "A1": [
        "First Steps: Hello and Goodbye",
        "Meeting People",
        "Numbers and Counting",
        "Yes, No, and Thank You",
        "Asking Simple Questions",
        "Family Members",
        "Where Are You From?",
        "Jobs and Professions",
        "Around the City",
        "Finding Your Way",
        "Time and Days",
        "Food and Drink Basics",
        "At the Shop",
        "Weather Talk",
        "Colors All Around",
        "Morning Routines",
        "Common Actions",
        "Likes and Dislikes",
        "What Can You Do?",
        "Needs and Wants",
        "Being Polite",
        "At the Restaurant",
        "At the Hotel",
        "Phone Conversations",
        "Emergency Situations",
        "Travel Essentials",
        "Making Small Talk",
        "Review: Meeting People",
        "Review: Daily Life",
        "Putting It All Together",
    ],
    "A2": [f"A2 Lesson {i}: {VOCABULARY_CURRICULUM['A2']['themes'][i-1].replace('_', ' ').title()}" for i in range(1, 31)],
    "B1": [f"B1 Lesson {i}: {VOCABULARY_CURRICULUM['B1']['themes'][i-1].replace('_', ' ').title()}" for i in range(1, 31)],
}
