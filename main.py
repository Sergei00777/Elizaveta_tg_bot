import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from mistralai.client import MistralClient
from datetime import datetime, timedelta
import pytz
import sqlite3
import random
import os




# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Конфигурация из переменных окружения
BOT_TOKEN =  "7529656586:AAHLqQ5mOZXgcl0el8YKBZqiCfp"
MISTRAL_API_KEY = "3pu7nqyufOMsVOJljn"
CHANNEL_ID = -1002540  # ID вашего канала
ADMIN_ID = 43638  # ID администратора
MODEL_NAME = "mistral-small-latest"
TIMEZONE = pytz.timezone('Europe/Moscow')
DB_FILE = "elizabeth_bot.db"

# Инициализация
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)


# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# Инициализация БД
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS posts 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      content TEXT,
                      post_type TEXT,
                      created_at TIMESTAMP,
                      views INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS admins
                     (user_id INTEGER PRIMARY KEY)''')
    # Добавляем основного администратора, если его нет
    cursor.execute("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (ADMIN_ID,))
    conn.commit()
    conn.close()


init_db()

# Темы для постов
PERSONAL_STORIES = [

    # Путешествия и приключения
    "Мое путешествие по Италии на стареньком Fiat",
    "Как я купила свой первый автомобиль",
    "Жизнь в дороге: месяц в путешествии по России",
    "Случай на границе: история одного приключения",
    "Мои любимые автомобильные маршруты в Европе",
    "Как я научилась ремонтировать машину самостоятельно",
    "Автомобиль и семья: как совмещать",
    "Fiat 500 против Альп: как маленькая машина покорила горные серпантины",
    "Дорога без конца: как мы проехали 10 000 км за один месяц",
    "Где ночевать в дороге: кемпинги, мотели и неожиданные находки",
    "Почему я предпочитаю путешествовать на машине, а не на самолете",
    "Самые опасные дороги, по которым я проехал(а)",

    # Личный опыт и истории
    "Как я перестал(а) бояться дальних поездок",
    "Мой худший поломка в пути (и как я с ней справился(ась))",
    "Почему я никогда не куплю новую машину",
    "Как автомобиль изменил мою жизнь",
    "История моей первой аварии и что я из этого вынес(ла)",

    # Советы и лайфхаки
    "Как подготовить машину к долгой поездке: чек-лист",
    "Что должно быть в багажнике у каждого автопутешественника",
    "Как экономить на путешествиях на машине",
    "Навигаторы против карт: что лучше в дороге?",
    "Как не уснуть за рулем: проверенные методы",

    # Семья и автомобили
    "Путешествие с ребенком: как не сойти с ума в дороге",
    "Как мы с мужем/женой выбирали наш семейный автомобиль",
    "Почему совместные поездки укрепляют отношения",
    "Автопутешествия с собакой: советы и лайфхаки",

    # Ностальгия и философия
    "Почему старые машины лучше новых",
    "Как звук мотора влияет на настроение",
    "Дорога как терапия: почему я люблю ездить один(а)",
    "Машины, которые я продал(а) и о которых до сих пор жалею"


]

CAR_NEWS = [

    # Новые автомобили и технологии
    "Новые модели автомобилей 2024 года",
    "Электромобили: последние тенденции",
    "Авторынок России: что изменилось?",
    "Технологии будущего в автомобилестроении",
    "Безопасность на дорогах: новые стандарты",
    "Автоспорт: последние новости и события",
    "Как выбрать автомобиль для путешествий",
    "Гибриды vs электромобили: что выгоднее в 2024?",
    "Самые ожидаемые новинки автосалонов этого года",
    "Китайские автомобили: стоит ли покупать?",
    "Как беспилотные технологии меняют авторынок",
    "Автомобили класса люкс 2024: обзор топ-моделей",

    # Экология и электромобильность
    "Правда ли, что электромобили экологичнее?",
    "Где и как заряжать электрокар: гид для новичков",
    "Сколько реально служат аккумуляторы в электромобилях?",
    "Водородные автомобили: есть ли будущее?",
    "Как правительства поддерживают переход на электромобили",
    "Самые дешевые электромобили 2024 года",

    # Авторынок и экономика
    "Подержанные авто в 2024: на что обратить внимание?",
    "Как кризис повлиял на цены на автомобили?",
    "Лучшие кредитные программы на покупку авто",
    "Страхование КАСКО: новые правила и лайфхаки",
    "Какие машины лучше всего сохраняют стоимость?",
    "Автолизинг: плюсы и минусы в 2024 году",

    # Технологии и безопасность
    "Искусственный интеллект в автомобилях: что умеет?",
    "Новые системы помощи водителю (ADAS) в 2024",
    "Кибербезопасность автомобилей: миф или реальность?",
    "Как работают системы автоматического торможения?",
    "Обзор самых безопасных автомобилей по версии Euro NCAP",
    "Технология V2X: машины учатся 'общаться' с дорогой",

    # Автоспорт и тюнинг
    "Формула-1 2024: главные изменения сезона",
    "Ралли Дакар 2024: самые неожиданные моменты",
    "Как легально тюнинговать авто в России?",
    "Электрический автоспорт: будущее или мода?",
    "Лучшие гоночные симуляторы для тренировок",
    "Уличные гонки: почему это до сих пор популярно?",

    # Покупка и обслуживание
    "Как проверить автомобиль перед покупкой?",
    "Главные ошибки при выборе первого авто",
    "Где дешевле обслуживать машину: дилер или сервис?",
    "Как сэкономить на запчастях без риска?",
    "Зимняя резина 2024: какой производитель лучше?",
    "Как часто нужно менять масло в современных авто?",

    # Путешествия и дороги
    "Лучшие дороги России для автомобильных путешествий",
    "Как подготовить машину к длинной поездке?",
    "Необычные дорожные правила в разных странах",
    "Где можно проехать на машине, но лучше не стоит",
    "Автомобильные кемпинги: новый тренд путешествий",
    "Как не попасть в пробку: полезные сервисы и советы"

]




# Клавиатура
def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="🚀 Запустить Елизавету"))
    builder.add(types.KeyboardButton(text="📅 Автозаполнение канала"))
    builder.add(types.KeyboardButton(text="📝 Личная история"))
    builder.add(types.KeyboardButton(text="🚗 Автомобильные новости"))
    builder.add(types.KeyboardButton(text="📊 Статистика"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


# Генерация поста
async def generate_post(theme: str, is_personal: bool) -> str:
    try:
        if is_personal:
            prompt = (f"Напиши личную историю от имени Елизаветы на тему '{theme}'. "
                      f"Используй неформальный стиль, эмодзи, сделай текст живым и эмоциональным. "
                      f"Пиши от первого лица, как будто это дневниковая запись.")
        else:
            prompt = (f"Напиши информативный пост об автомобилях на тему '{theme}'. "
                      f"Используй эмодзи, но сохраняй профессиональный тон. "
                      f"Добавь интересные факты и актуальную информацию.")

        response = mistral_client.chat(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Ошибка генерации поста: {e}")
        return None


# Публикация поста
async def publish_post(theme: str = None, is_personal: bool = True):
    if not theme:
        theme = random.choice(PERSONAL_STORIES if is_personal else CAR_NEWS)

    post_content = await generate_post(theme, is_personal)
    if post_content:
        # Сохраняем в БД
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        post_type = "personal" if is_personal else "news"
        cursor.execute("INSERT INTO posts (content, post_type, created_at) VALUES (?, ?, ?)",
                       (post_content, post_type, datetime.now()))
        post_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Публикуем в канал
        if is_personal:
            header = "🌟 Личная история Елизаветы 🌟\n\n"
            footer = "\n\n#личное #путешествия #история"
        else:
            header = "🚗 Автомобильные новости 🚗\n\n"
            footer = "\n\n#новости #авто #технологии"

        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"{header}{post_content}{footer}",
            parse_mode="Markdown"
        )
        return True
    return False


# Автопостинг
async def auto_posting():
    while True:
        now = datetime.now(TIMEZONE)
        if now.hour == 9:  # Утренний пост - личная история
            await publish_post(is_personal=True)
            await asyncio.sleep(3600 * 12)  # Следующий пост через 12 часов
        elif now.hour == 21:  # Вечерний пост - автомобильные новости
            await publish_post(is_personal=False)
            await asyncio.sleep(3600 * 12)  # Следующий пост через 12 часов
        await asyncio.sleep(3600)  # Проверка каждый час


# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к этому боту")
        return

    await message.answer("🛠️ Админ-панель Елизаветы:", reply_markup=get_main_keyboard())


@dp.message(lambda message: message.text == "🚀 Запустить Елизавету")
async def start_elizabeth(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только администратор может управлять ботом")
        return

    asyncio.create_task(auto_posting())
    await message.answer(
        "✅ Елизавета запущена! Посты будут публиковаться автоматически (личные истории утром и новости вечером).")


@dp.message(lambda message: message.text == "📅 Автозаполнение канала")
async def auto_fill_channel(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только администратор может управлять ботом")
        return

    await message.answer("⏳ Начинаю автозаполнение канала...")
    for _ in range(3):  # 3 личные истории
        if await publish_post(is_personal=True):
            await asyncio.sleep(600)
    for _ in range(3):  # 3 новости
        if await publish_post(is_personal=False):
            await asyncio.sleep(600)
    await message.answer("✅ Канал успешно заполнен!")


@dp.message(lambda message: message.text == "📝 Личная история")
async def personal_story(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только администратор может управлять ботом")
        return

    theme = random.choice(PERSONAL_STORIES)
    if await publish_post(theme, is_personal=True):
        await message.answer("✅ Личная история опубликована!")
    else:
        await message.answer("⚠️ Не удалось опубликовать историю")


@dp.message(lambda message: message.text == "🚗 Автомобильные новости")
async def car_news(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только администратор может управлять ботом")
        return

    theme = random.choice(CAR_NEWS)
    if await publish_post(theme, is_personal=False):
        await message.answer("✅ Новость опубликована!")
    else:
        await message.answer("⚠️ Не удалось опубликовать новость")


@dp.message(lambda message: message.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Только администратор может управлять ботом")
        return

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='personal'")
    personal_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM posts WHERE post_type='news'")
    news_count = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(views) FROM posts")
    total_views = cursor.fetchone()[0] or 0

    conn.close()

    await message.answer(
        f"📊 Статистика канала Елизаветы:\n\n"
        f"• Личных историй: {personal_count}\n"
        f"• Автомобильных новостей: {news_count}\n"
        f"• Всего просмотров: {total_views}"
    )


# Запуск бота
async def main():
    try:
        logging.info("Starting Елизавета...")
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


















