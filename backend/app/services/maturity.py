_LEVELS = [
    (1, "Compliance-Focused", "Обучение проводится формально, показатели низкие."),
    (2, "Awareness Promotion", "Сотрудники знают об угрозах, но поведение не изменилось."),
    (3, "Long-Term Sustainment", "Программа регулярна, показатели улучшаются."),
    (4, "Cultural Change", "Безопасность вошла в корпоративную культуру."),
    (5, "Metrics Framework", "Программа управляется данными, риск минимален."),
]

_INDICATORS = [
    ("Завершаемость модулей ≥ 90%", lambda o: o.get("completion_rate", 0) >= 0.90),
    ("Средний балл тестов ≥ 80%", lambda o: o.get("avg_score", 0) >= 0.80),
    ("Клики фишинга < 10%", lambda o: o.get("phishing_click_rate", 1) < 0.10),
    ("Сабмиты фишинга < 5%", lambda o: o.get("phishing_submit_rate", 1) < 0.05),
    ("Репортинг фишинга ≥ 40%", lambda o: o.get("phishing_report_rate", 0) >= 0.40),
    ("Завершаемость ≥ 70%", lambda o: o.get("completion_rate", 0) >= 0.70),
    ("Клики фишинга < 25%", lambda o: o.get("phishing_click_rate", 1) < 0.25),
    ("Средний балл ≥ 65%", lambda o: o.get("avg_score", 0) >= 0.65),
]


def compute_maturity(overview: dict) -> dict:
    indicators = [
        {"label": label, "met": check(overview)}
        for label, check in _INDICATORS
    ]
    met_count = sum(1 for i in indicators if i["met"])
    score = round(met_count / len(_INDICATORS) * 100)

    if score >= 90:
        level = 5
    elif score >= 70:
        level = 4
    elif score >= 50:
        level = 3
    elif score >= 25:
        level = 2
    else:
        level = 1

    _, label, description = _LEVELS[level - 1]
    return {
        "level": level,
        "score": score,
        "label": label,
        "description": description,
        "indicators": indicators,
    }
