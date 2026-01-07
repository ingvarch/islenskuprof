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

# Segment types for lesson script
SEGMENT_TYPES = {
    "instruction": "English narrator explanations",
    "new_word": "Introduce vocabulary (native speaker)",
    "prompt": "Ask user to produce language",
    "pause": "Silent period for user response",
    "model_answer": "Correct answer after pause",
    "repeat_after": "Instruction to repeat",
    "native_model": "Native model for repetition",
    "dialogue_segment": "Short contextual dialogues",
}

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
    ("hallo", "hello", "greeting", "HAL-lo"),
    ("bless", "goodbye", "greeting", "bless"),
    ("godan dag", "good day", "greeting", "GO-than dahg"),
    ("gott kvold", "good evening", "greeting", "goht kvuhld"),
    ("goda nott", "good night", "greeting", "GO-tha noht"),
    ("takk", "thank you", "courtesy", "tahk"),
    ("takk fyrir", "thank you (for)", "courtesy", "tahk FIR-ir"),
    ("gjordu svo vel", "you're welcome", "courtesy", "GYUHR-thu svo vel"),

    # Basic responses (Lessons 3-4)
    ("ja", "yes", "response", "yow"),
    ("nei", "no", "response", "nay"),
    ("kannski", "maybe", "response", "KAHN-skee"),
    ("eg veit ekki", "I don't know", "phrase", "yeh vayt EH-kee"),
    ("afsakid", "excuse me", "courtesy", "AHF-sah-kith"),
    ("fyrirgefdu", "sorry", "courtesy", "FIR-ir-GEV-thu"),

    # Introductions (Lessons 5-6)
    ("eg heiti", "my name is", "phrase", "yeh HAY-tee"),
    ("hvad heitir thu", "what is your name", "question", "kvath HAY-tir thoo"),
    ("eg er fra", "I am from", "phrase", "yeh er frow"),
    ("eg er islenskur", "I am Icelandic (m)", "phrase", "yeh er EES-len-skur"),
    ("eg er islensk", "I am Icelandic (f)", "phrase", "yeh er EES-lensk"),
    ("thad er gott ad hitta thig", "nice to meet you", "phrase", "thahth er goht ahth HIT-tah theeg"),

    # Numbers 1-10 (Lesson 7)
    ("einn", "one", "number", "aytn"),
    ("tveir", "two", "number", "tvair"),
    ("thrir", "three", "number", "threer"),
    ("fjorir", "four", "number", "FYOH-rir"),
    ("fimm", "five", "number", "fim"),
    ("sex", "six", "number", "seks"),
    ("sjo", "seven", "number", "syoh"),
    ("atta", "eight", "number", "OHT-ta"),
    ("niu", "nine", "number", "nee-u"),
    ("tiu", "ten", "number", "tee-u"),

    # Questions (Lessons 8-9)
    ("hvad", "what", "question_word", "kvath"),
    ("hver", "who", "question_word", "kver"),
    ("hvar", "where", "question_word", "kvar"),
    ("hvenær", "when", "question_word", "KVEN-air"),
    ("hvers vegna", "why", "question_word", "KVERS VEG-na"),
    ("hvernig", "how", "question_word", "KVER-nig"),
    ("hvad kostar", "how much does it cost", "question", "kvath KOS-tar"),

    # Family (Lessons 10-11)
    ("fjolskylda", "family", "noun", "FYUHL-skil-da"),
    ("mamma", "mother", "noun", "MAM-ma"),
    ("pabbi", "father", "noun", "PAB-bee"),
    ("systir", "sister", "noun", "SIS-tir"),
    ("brodur", "brother", "noun", "BROH-thur"),
    ("barn", "child", "noun", "barn"),
    ("born", "children", "noun", "buhrn"),
    ("eiginkona", "wife", "noun", "AY-gin-KO-na"),
    ("eiginmadur", "husband", "noun", "AY-gin-MAH-thur"),

    # Common verbs (Lessons 12-14)
    ("ad vera", "to be", "verb", "ahth VE-ra"),
    ("ad hafa", "to have", "verb", "ahth HA-va"),
    ("ad fara", "to go", "verb", "ahth FA-ra"),
    ("ad koma", "to come", "verb", "ahth KO-ma"),
    ("ad tala", "to speak", "verb", "ahth TA-la"),
    ("ad skilja", "to understand", "verb", "ahth SKIL-ya"),
    ("ad borða", "to eat", "verb", "ahth BOR-tha"),
    ("ad drekka", "to drink", "verb", "ahth DREK-ka"),
    ("ad sofa", "to sleep", "verb", "ahth SO-va"),
    ("ad vinna", "to work", "verb", "ahth VIN-na"),

    # Present tense forms (with "eg" - I)
    ("eg er", "I am", "verb_form", "yeh er"),
    ("eg hef", "I have", "verb_form", "yeh hev"),
    ("eg fer", "I go", "verb_form", "yeh fer"),
    ("eg kem", "I come", "verb_form", "yeh kem"),
    ("eg tala", "I speak", "verb_form", "yeh TA-la"),
    ("eg skil", "I understand", "verb_form", "yeh skil"),

    # Places (Lessons 15-16)
    ("heima", "home", "noun", "HAY-ma"),
    ("vinna", "work", "noun", "VIN-na"),
    ("verslun", "store", "noun", "VERS-lun"),
    ("veitingahus", "restaurant", "noun", "VAY-ting-a-hus"),
    ("hotel", "hotel", "noun", "ho-TEL"),
    ("flugvollur", "airport", "noun", "FLUG-vuh-lur"),
    ("stod", "station", "noun", "stuhth"),
    ("sjukrahus", "hospital", "noun", "SYOO-kra-hoos"),

    # Food & Drink (Lessons 17-18)
    ("matur", "food", "noun", "MA-tur"),
    ("vatn", "water", "noun", "vahtn"),
    ("kaffi", "coffee", "noun", "KAF-fee"),
    ("te", "tea", "noun", "teh"),
    ("braud", "bread", "noun", "broith"),
    ("fiskur", "fish", "noun", "FIS-kur"),
    ("kjot", "meat", "noun", "kyuht"),
    ("glerðneyti", "vegetables", "noun", "GREN-me-tee"),

    # Time (Lessons 19-20)
    ("klukkan", "the clock / it's ... o'clock", "noun", "KLUK-kan"),
    ("i dag", "today", "time", "ee dahg"),
    ("a morgun", "tomorrow", "time", "ow MOR-gun"),
    ("i gaer", "yesterday", "time", "ee gair"),
    ("nuna", "now", "time", "NOO-na"),
    ("seinna", "later", "time", "SAYT-na"),
    ("dagur", "day", "noun", "DA-gur"),
    ("vika", "week", "noun", "VEE-ka"),

    # Days of week (Lesson 21)
    ("manudagur", "Monday", "day", "MAH-nu-DA-gur"),
    ("thridjudagur", "Tuesday", "day", "THRITH-yu-DA-gur"),
    ("midvikudagur", "Wednesday", "day", "MITH-vi-ku-DA-gur"),
    ("fimmtudagur", "Thursday", "day", "FIM-tu-DA-gur"),
    ("fostudagur", "Friday", "day", "FOS-tu-DA-gur"),
    ("laugardagur", "Saturday", "day", "LOI-gar-DA-gur"),
    ("sunnudagur", "Sunday", "day", "SUN-nu-DA-gur"),

    # Weather (Lesson 22)
    ("vedur", "weather", "noun", "VE-thur"),
    ("solin skinn", "the sun is shining", "phrase", "SO-lin skin"),
    ("thad rignar", "it's raining", "phrase", "thahth RIG-nar"),
    ("thad snjóar", "it's snowing", "phrase", "thahth SNYOH-ar"),
    ("kalt", "cold", "adjective", "kahlt"),
    ("heitt", "hot", "adjective", "hayt"),
    ("vindur", "wind", "noun", "VIN-dur"),

    # Shopping (Lessons 23-24)
    ("ad kaupa", "to buy", "verb", "ahth KOI-pa"),
    ("ad borga", "to pay", "verb", "ahth BOR-ga"),
    ("pening", "money", "noun", "PEN-ing"),
    ("krona", "krona (currency)", "noun", "KROH-na"),
    ("odyr", "cheap", "adjective", "OH-deer"),
    ("dyrt", "expensive", "adjective", "deert"),
    ("stort", "big", "adjective", "stohrt"),
    ("litid", "small", "adjective", "LEE-tith"),

    # Colors (Lesson 25)
    ("raudur", "red", "adjective", "ROI-thur"),
    ("graenn", "green", "adjective", "graitn"),
    ("blar", "blue", "adjective", "blow-r"),
    ("gulur", "yellow", "adjective", "GU-lur"),
    ("svartur", "black", "adjective", "SVAR-tur"),
    ("hvitur", "white", "adjective", "KVEE-tur"),

    # Useful phrases (Lessons 26-30)
    ("eg tala ekki islensku", "I don't speak Icelandic", "phrase", "yeh TA-la EH-kee EES-len-sku"),
    ("talardu ensku", "do you speak English", "question", "TA-lar-thu EN-sku"),
    ("eg skil ekki", "I don't understand", "phrase", "yeh skil EH-kee"),
    ("geturu endurtekid", "can you repeat", "question", "GE-tur-u EN-dur-te-kith"),
    ("hvar er", "where is", "question", "kvar er"),
    ("eg tharf", "I need", "phrase", "yeh tharf"),
    ("eg vil", "I want", "phrase", "yeh vil"),
    ("ma eg fa", "may I have", "phrase", "mow yeh fow"),
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
