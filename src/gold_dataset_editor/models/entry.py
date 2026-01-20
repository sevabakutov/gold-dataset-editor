"""Pydantic models for gold dataset entries."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Source(BaseModel):
    """Source information for an entry."""

    drive_path: str
    thread_dir: str = ""
    message_index: int

    model_config = ConfigDict(extra="allow")


class Message(BaseModel):
    """A single message in the conversation."""

    role: str
    text: str
    ts_ms: int

    model_config = ConfigDict(extra="allow")


class Gold(BaseModel):
    """Gold annotation data with slots and evidence."""

    slots: dict[str, Any] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class Entry(BaseModel):
    """A single entry in the gold dataset."""

    id: str
    source: Source
    message: Message | dict
    context: list[dict] = Field(default_factory=list)
    gold: Gold
    qa_hint: str | None = None
    reviewed: bool = False

    model_config = ConfigDict(extra="allow")

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        """Create an Entry from a raw dictionary, preserving all fields."""
        return cls.model_validate(data)

    def to_dict(self) -> dict:
        """Convert to dictionary, preserving all fields including extras."""
        return self.model_dump(mode="json")


class SlotUpdate(BaseModel):
    """Update for a single slot value."""

    slot_name: str
    value: Any
    evidence: Any | None = None


class EntryUpdate(BaseModel):
    """Update payload for an entry."""

    slots: dict[str, Any] | None = None
    evidence: dict[str, Any] | None = None
    intentions: list[str] | None = None  # Array of intention types
    qa_hint: str | None = None
    reviewed: bool | None = None
    message_role: str | None = None  # Update main message role
    context_updates: list[dict] | None = None  # [{"index": 0, "role": "brand"}]


# Intention types
INTENTION_TYPES = [
    "greet",
    "ask_question",
    "ask_work_schedule",
    "book_appointment",
    "reschedule_appointment",
    "cancel_appointment",
    "existing_appointment",
    "ask_about_the_price",
    "appointment_availability",
    "end_conversation",
]

# Slot type definitions (ordered for UI display)
STRING_SLOTS = [
    "treatment",
    "hair_removal_areas",  # list[str] in data, displayed/edited as comma-separated string
    "hair_removal_type",
    "hair_type_on_face",
    "tattoo_removal_category",
    "tattoo_equipment",
    "blood_vessels_area",
    "specialist",
    "specialist_name",
    "city",
    "address",
    "number_phone",
    "name",
    "date_time",
]
BOOL_SLOTS = [
    "has_contraindications",
    "is_first_time",
    "can_visit_center",
    "is_consultation",
]
ALL_SLOTS = STRING_SLOTS + BOOL_SLOTS

# Multi-select slots (fields with predefined dropdown options)
MULTI_SELECT_SLOTS = {
    "treatment",
    "hair_removal_areas",
    "hair_removal_type",
    "hair_type_on_face",
    "tattoo_removal_category",
    "tattoo_equipment",
    "blood_vessels_area",
    "specialist",
    "city",
    "address",
}

# Predefined options for multi-select slots
SLOT_OPTIONS: dict[str, list[str]] = {
    "treatment": [
        "hair_removal",
        "blood_vessels_removal",
        "tattoo_removal",
        "pigmentation_removal",
        "photorejuvenation",
        "3d_rejuvenation",
        "thermolifting",
        "laser_treatment_of_nail_fungus",
        "laser_resurfacing_of_scars",
        "laser_stretch_mark_resurfacing",
        "laser_peeling",
        "laser_posta_acne_resurfacing",
        "laser_hair_treatment",
        "laser_blepharoplasty",
        "intimate_area_whitening",
        "focus_rejuvenation",
        "heel_treatment",
        "pms",
        "endosphere",
        "other",
    ],
    "hair_removal_areas": [
        "full_face",
        "forehead_line",
        "glabella",
        "eyebrows",
        "nose_outer_part",
        "cheeks",
        "temples",
        "ears",
        "upper_lip",
        "chin",
        "neck_front_or_back",
        "neck_full",
        "sclap",
        "armpits",
        "full_arms",
        "forearms",
        "hands",
        "fingers",
        "decollete",
        "chest",
        "areolae",
        "abdomen",
        "linea_alba",
        "shoulders",
        "upper_back",
        "back",
        "lumbar_area",
        "sacral_area",
        "buttocks",
        "buttocks_half",
        "full_legs",
        "thighs",
        "thighs_partial",
        "shins",
        "knees",
        "instep",
        "toes",
        "shallow_bikini",
        "deep_bikini",
        "pubic_area",
        "scrotum",
        "labia",
        "intergluteal_crease",
        "single_hairs_removal",
        "arms",
        "full_body",
        "legs",
        "bikini",
    ],
    "hair_removal_type": ["nano", "gold_standard", "exclusive"],
    "hair_type_on_face": [
        "coarse_pigmented_hair",
        "fine_pigmented_hair",
        "hair_has_no_pigment",
        "doesnt_know_or_mixed",
    ],
    "tattoo_removal_category": ["first", "second", "third", "fourth", "eyeild", "test_area"],
    "tattoo_equipment": ["qswitch", "picoseconds_lazer"],
    "blood_vessels_area": ["peri_orbital", "face", "legs", "arms"],
    "specialist": ["podiatrist", "other"],
    "city": [
        "Київ",
        "Харків",
        "Дніпро",
        "Одеса",
        "Львів",
        "Вінниця",
        "Житомир",
        "Івано-Франківськ",
        "Запоріжжя",
        "Кривій Ріг",
        "Чернігів",
        "Черкаси",
        "Хмельницький",
        "Миколаїв",
        "Рівне",
        "Полтава",
        "Тернопіль",
        "Луцьк",
        "Кропивницький",
        "Кременчук",
        "Ужгород",
        "Кам'янець-Подільський",
        "Суми",
        "Біла Церква",
        "Нікополь",
        "Умань",
        "Васильків",
        "Краматорськ",
        "Мукачево",
        "Ізмаїл",
        "Павлоград",
        "Дрогобич",
        "Kamianske",
        "Ірпінь",
        "Вишгород",
        "Вишневе",
        "Бориспіль",
        "Бровари",
        "Коломия",
        "Ковель",
        "Стрий",
        "Самбір",
        "Чернівці",
        "Бердичів",
        "Шептицький",
        "Олександрія",
    ],
    "address": [
        "м. Палац Україна, вул. Ковпака, 17",
        "м. Золоті Ворота, вул. Володимирська, 49а",
        "м. Палац Спорту, вул. Басейна, 1/2а",
        "м. Золоті Ворота\\Універститет, вул. Леонтовича, 6а",
        "м. Голосіївська, проспект Голосіївський, 68",
        "м. Контрактова, вул. Межигірська, 3",
        "м. Оболонь, пр. Оболонський, 6а",
        "м. Шулявська, вул. Михайла Брайчевського, 35/15",
        "м. Звіринецька, бульвар Марії Приймаченко, 7",
        "м. Вокзальна, вул. Івана Огієнка, 21",
        "вул. Солом'янська, 28",
        "пр. Академіка Глушкова, 27",
        "бул. Академіка Вернадського, 73а",
        "м. Лівобережна, вул. Микільсько-Слобідська, 2г",
        "м. Осокорки, вул. Трускавецька, 10в",
        "Троєщина, пр-т Червоної Калини, 8",
        "м. Харківська, пр. Бажана, 26",
        "м. Позняки, вул. Драгоманова, 25",
        "вул. Русанівська Набережна, 22",
        "вул. Святошинська, 26",
        "вул. Київська, 235 (ЖК Medison Gardens)",
        "вул. Європейська, 11",
        "вул. Матвія Донцова, 15",
        "вул. Набережна, 6г",
        "вул. Київський шлях, 95",
        "вул. Грушевського, 16",
        "бульвар Олександрійський, 25/2",
        "вул. Старокозацька, 25",
        "вул. Культури, 12",
        "провулок Отонівський, 8",
        "вул. Генуезька, 5 (район Аркадії)",
        "вул. Під Дубом, 26 а",
        "вул. Володимира Великого, 61",
        "вул. Угорська, 12е",
        "вул. Монастирська, 41",
        "вул. В'ячеслава Чорновола, 4",
        "вул. Михайла Мулика, 27",
        "б-р Марії Примайченко, 18",
        "вул. Степана Бандери, 6",
        "пр-т Перемоги, 145",
        "вул. Гоголя, 276",
        "вул. Панаса Саксаганського, 39",
        "вул. Гетьмана Мазепи, 3",
        "площа Філармонії, 4",
        "вул. Героїв Майдану, 160",
        "вул. Проскурівська, 51",
        "вул. Сінна, 8/1",
        "площа Героїв Євромайдану, 9",
        "вул. Рівненська, 25Р",
        "вул. Шевченка, 50/40",
        "бул. Українського Відродження, 11",
        "вул. Тлехаса, 16",
        "вул. Лесі Українки, 31",
        "вул. Харківська, 4",
        "проспект Трубників, 6",
        "вул. Тищика, 19",
        "вул. Василя Стуса, 35",
        "вул. Олександра Духновича, 42",
        "вул. Гетьмана Мазепи, 24",
        "вул. Центральна, 56",
        "вул. Любомирівська, 5",
        "вул. Тараса Шевченка, 3/2",
        "вул. Незалежності, 92",
        "вул. Людкевича, 12/1",
        "вул. Різницька, 20а",
        "вул. Тараса Шевченка, 7",
        "вул. Європейська, 65/1",
        "вул. Григорія Усика, 40",
        "вул. Паркова, 2",
    ],
}
