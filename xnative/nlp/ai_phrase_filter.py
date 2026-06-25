AI_PHRASES = [
    "bu bağlamda",
    "özetle",
    "dikkat çekici bir gelişme",
    "futbolseverler için",
    "sosyal medyada gündem oldu",
    "kritik bir gelişme yaşandı",
    "x platformunda",
    "taraftarlar ikiye bölündü",
    "büyük yankı uyandırdı",
    "futbol dünyasında gündem",
]


def find_ai_phrases(text: str) -> list[str]:
    low = (text or "").lower()
    return [p for p in AI_PHRASES if p in low]
