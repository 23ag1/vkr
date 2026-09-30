"""Run: python -m app.seed"""

import asyncio
import os
import secrets

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.models.department import Department
from app.models.module import Module
from app.models.phishing import PhishingTemplate
from app.models.user import User

_URL = (
    f"postgresql+asyncpg://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}"
    f"@{os.environ.get('POSTGRES_HOST', 'localhost')}:{os.environ.get('POSTGRES_PORT', '5432')}"
    f"/{os.environ['POSTGRES_DB']}"
)


def _password(role: str) -> str:
    """Демо-пароль из SEED_<ROLE>_PASSWORD; если не задан — случайный, печатается один раз."""
    value = os.environ.get(f"SEED_{role}_PASSWORD")
    if value:
        return value
    value = secrets.token_urlsafe(12)
    print(f"seed: {role.lower()} password = {value}")
    return value


async def seed() -> None:
    engine = create_async_engine(_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        dept = Department(name="Information Security")
        db.add(dept)
        await db.flush()

        users = [
            User(
                email="admin@vkr.example.com",
                hashed_password=hash_password(_password("ADMIN")),
                full_name="Главный администратор",
                role="admin",
                department_id=dept.id,
            ),
            User(
                email="specialist@vkr.example.com",
                hashed_password=hash_password(_password("SPECIALIST")),
                full_name="Специалист ИБ",
                role="security_specialist",
                department_id=dept.id,
            ),
            User(
                email="manager@vkr.example.com",
                hashed_password=hash_password(_password("MANAGER")),
                full_name="Руководитель отдела",
                role="manager",
                department_id=dept.id,
            ),
            User(
                email="employee@vkr.example.com",
                hashed_password=hash_password(_password("EMPLOYEE")),
                full_name="Сотрудник Иванов",
                role="employee",
                department_id=dept.id,
            ),
        ]
        for u in users:
            db.add(u)

        modules = [
            Module(
                title="Основы информационной безопасности",
                description="Базовые понятия ИБ для всех сотрудников.",
                content_md="# Основы информационной безопасности\n\n## Триада CIA\n\n- **Конфиденциальность** — информация доступна только авторизованным лицам.\n- **Целостность** — информация не изменена несанкционированно.\n- **Доступность** — информация доступна авторизованным пользователям.\n\n## Виды угроз\n\n- **Внешние**: хакерские атаки, вредоносное ПО, фишинг.\n- **Внутренние**: ошибки сотрудников, кража данных инсайдерами.\n\n## Нормативная база\n\n- **ФЗ-152** — защита персональных данных.\n- **ФЗ-187** — безопасность КИИ.\n- **Приказ ФСТЭК №21** — меры защиты ПДн.",
                target_roles=[],  # базовый — для всех ролей
                order_index=1,
                is_published=True,
            ),
            Module(
                title="Фишинг и социальная инженерия",
                description="Как распознать фишинговые атаки.",
                content_md="# Фишинг и социальная инженерия\n\n## Что такое фишинг\n\nФишинг — атака, при которой злоумышленник маскируется под доверенный источник.\n\n## Признаки письма\n\n1. Срочность и угрозы блокировки.\n2. Подозрительный адрес отправителя.\n3. Просьба перейти по ссылке.\n\n## Защита\n\n- Проверяй URL перед вводом данных.\n- Используй MFA.\n- Сообщай об инцидентах в ИБ.",
                target_roles=["employee"],
                order_index=2,
                is_published=True,
            ),
            Module(
                title="Безопасная работа с паролями",
                description="Правила создания и хранения паролей.",
                content_md="# Безопасная работа с паролями\n\n## Надёжный пароль\n\n- Длина не менее **12 символов**.\n- Заглавные/строчные, цифры, спецсимволы.\n- Уникален для каждого сервиса.\n\n## Запрещено\n\n- «123456», «password», «qwerty».\n- Один пароль для всех сервисов.\n\n## Менеджеры паролей\n\nKeePass, Bitwarden хранят пароли в зашифрованном виде.",
                target_roles=["employee"],
                order_index=3,
                is_published=True,
            ),
            Module(
                title="Управление рисками ИБ для руководителей",
                description="Оценка рисков, KPI безопасности, отчётность.",
                content_md="# Управление рисками ИБ\n\n## Роль руководителя\n\nРуководитель отвечает за формирование культуры безопасности в подразделении.\n\n## Ключевые метрики\n\n- % сотрудников, прошедших обучение.\n- Количество инцидентов за период.\n- Время реакции на инциденты.\n\n## Отчётность\n\nЕжеквартальный отчёт для CISO включает метрики по подразделению.",
                target_roles=["manager"],
                order_index=4,
                is_published=True,
            ),
            Module(
                title="Реагирование на инциденты ИБ",
                description="Процедуры обнаружения и расследования инцидентов.",
                content_md="# Реагирование на инциденты\n\n## Классификация\n\n- **P1**: критический — немедленное реагирование.\n- **P2**: высокий — реагирование в течение 4 часов.\n- **P3**: средний — реагирование в течение суток.\n\n## Шаги расследования\n\n1. Локализация инцидента.\n2. Сбор доказательств (логи, артефакты).\n3. Устранение угрозы.\n4. Восстановление работоспособности.\n5. Документирование и разбор.",
                target_roles=["security_specialist"],
                order_index=5,
                is_published=True,
            ),
        ]
        for m in modules:
            db.add(m)

        templates = [
            PhishingTemplate(
                name="Письмо от IT-отдела",
                subject="Срочно: смените пароль",
                body_html="<p>Уважаемый сотрудник, перейдите по <a href='{{link}}'>ссылке</a>.</p>",
                difficulty="easy",
            ),
            PhishingTemplate(
                name="Корпоративный опрос",
                subject="Пройдите обязательный опрос",
                body_html="<p>Для участия в опросе <a href='{{link}}'>нажмите здесь</a>.</p>",
                difficulty="medium",
            ),
            PhishingTemplate(
                name="Уведомление банка",
                subject="Подозрительная активность на вашем счёте",
                body_html="<p>Для подтверждения личности <a href='{{link}}'>войдите в систему</a>.</p>",
                difficulty="hard",
            ),
        ]
        for t in templates:
            db.add(t)

        await db.commit()

    await engine.dispose()
    print("✓ Seed complete")


if __name__ == "__main__":
    asyncio.run(seed())
