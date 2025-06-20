import asyncio
import json
import logging
import os

from collections import defaultdict, Counter
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8012401893:AAFAFY0V3YVEeqf3gX6QJKBo6tixje2s1A0"
ADMIN_ID = 5825453938

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

default_lang = "uz"
user_languages = defaultdict(lambda: default_lang)
SAVOLLAR_FILE = "savollar.json"
USERS_FILE = "users.json"

class TestState(StatesGroup):
    question_index = State()
    questions = State()

def save_user(user):
    if not os.path.exists(USERS_FILE):
        data = {}
    else:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}

    user_id = str(user.id)
    username = user.username or ""
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    data[user_id] = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name
    }

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Menyuni ochish"),
        BotCommand(command="help", description="Bot haqida ma'lumot"),
    ]
    await bot.set_my_commands(commands)

def get_language_changed_message(lang):
    return {
        "uz": "Til o‘zgartirildi ✅",
        "en": "Language has been changed ✅",
        "ru": "Язык был изменен ✅"
    }.get(lang, "Til o‘zgartirildi ✅")

def get_main_menu(user_id):
    lang = user_languages[user_id]
    is_admin = (user_id == ADMIN_ID)
    if lang == "ru":
        keyboard = [
            [KeyboardButton(text="Пройти тест"), KeyboardButton(text="Настройки")],
            [KeyboardButton(text="Связаться с админом")]
        ]
        if is_admin:
            keyboard.insert(1, [KeyboardButton(text="Добавить тест (для админа)")])
            keyboard.append([KeyboardButton(text="Список пользователей")])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    elif lang == "en":
        keyboard = [
            [KeyboardButton(text="Take a test"), KeyboardButton(text="Settings")],
            [KeyboardButton(text="Contact admin")]
        ]
        if is_admin:
            keyboard.insert(1, [KeyboardButton(text="Add test (for admin)")])
            keyboard.append([KeyboardButton(text="User list")])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    else:  # default uz
        keyboard = [
            [KeyboardButton(text="Test yechish"), KeyboardButton(text="Sozlamalar")],
            [KeyboardButton(text="Admin bilan bogʻlanish")]
        ]
        if is_admin:
            keyboard.insert(1, [KeyboardButton(text="Test qo‘shish (admin uchun)")])
            keyboard.append([KeyboardButton(text="Foydalanuvchi ro'yxati")])
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

@router.message(F.text.in_([
    "Foydalanuvchi ro'yxati",
    "User list",
    "Список пользователей"
]))
async def show_users_menu(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Siz admin emassiz!")
        return
    if not os.path.exists(USERS_FILE):
        await message.answer("Hali foydalanuvchilar yo‘q.")
        return
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    text = "👥 Foydalanuvchilar ro‘yxati:\n\n"
    for user_id, info in data.items():
        username = info.get("username", "")
        name = (info.get("first_name", "") + " " + info.get("last_name", "")).strip()
        text += f"{user_id} | @{username if username else '-'} | {name}\n"
    text += f"\nJami foydalanuvchilar: {len(data)}"
    await message.answer(text)

def get_category_menu(user_id):
    lang = user_languages[user_id]
    if lang == "ru":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🖐 Математика"), KeyboardButton(text="🖐 Английский")],
                [KeyboardButton(text="🖐 География"), KeyboardButton(text="🖐 История")],
                [KeyboardButton(text="🖐 Химия"), KeyboardButton(text="🖐 Биология")],
                [KeyboardButton(text="🧠 Психологический тест"), KeyboardButton(text="🖐 IELTS Reading")],
                [KeyboardButton(text="🖐 Назад")]
            ],
            resize_keyboard=True
        )
    elif lang == "en":
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🖐 Math"), KeyboardButton(text="🖐 English")],
                [KeyboardButton(text="🖐 Geography"), KeyboardButton(text="🖐 History")],
                [KeyboardButton(text="🖐 Chemistry"), KeyboardButton(text="🖐 Biology")],
                [KeyboardButton(text="🧠 Psychological test"), KeyboardButton(text="🖐 IELTS Reading")],
                [KeyboardButton(text="🖐 Back")]
            ],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🖐 Matematika"), KeyboardButton(text="🖐 Ingliz tili")],
                [KeyboardButton(text="🖐 Geografiya"), KeyboardButton(text="🖐 Tarix")],
                [KeyboardButton(text="🖐 Kimyo"), KeyboardButton(text="🖐 Biologiya")],
                [KeyboardButton(text="🧠 Psixologik test"), KeyboardButton(text="🖐 IELTS Reading")],
                [KeyboardButton(text="🖐 Ortga")]
            ],
            resize_keyboard=True
        )

language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="lang_uz")],
    [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
    [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
])

def get_text(user_id, uz="", ru="", en=""):
    lang = user_languages[user_id]
    return {"ru": ru, "en": en}.get(lang, uz)

subject_mapping = {
    "🖐 Matematika": "matematika",
    "🖐 Математика": "matematika",
    "🖐 Math": "matematika",
    "🖐 Ingliz tili": "ingliz_tili",
    "🖐 Английский": "ingliz_tili",
    "🖐 English": "ingliz_tili",
    "🖐 Geografiya": "geografiya",
    "🖐 География": "geografiya",
    "🖐 Geography": "geografiya",
    "🖐 Tarix": "tarix",
    "🖐 История": "tarix",
    "🖐 History": "tarix",
    "🖐 Kimyo": "kimyo",
    "🖐 Химия": "kimyo",
    "🖐 Chemistry": "kimyo",
    "🖐 Biologiya": "biologiya",
    "🖐 Биология": "biologiya",
    "🖐 Biology": "biologiya",
    "🖐 IELTS Reading": "ielts_reading",
    "🧠 Psixologik test": "psixologik_test",
    "🧠 Психологический тест": "psixologik_test",
    "🧠 Psychological test": "psixologik_test",
    "🖐 Ortga": "back",
    "🖐 Назад": "back",
    "🖐 Back": "back"
}

async def load_and_start_test(subject, message: Message, state: FSMContext):
    save_user(message.from_user)
    if not os.path.exists(SAVOLLAR_FILE):
        await message.answer(get_text(
            message.from_user.id,
            uz="Bu fandan savollar yo‘q.",
            ru="По этому предмету нет вопросов.",
            en="No questions for this subject."
        ))
        return

    lang = user_languages[message.from_user.id]
    with open(SAVOLLAR_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if subject in ["ingliz_tili", "ielts_reading"]:
        questions = data.get(subject, [])
    elif subject == "psixologik_test":
        questions = data.get(subject, {}).get(lang, [])
    else:
        questions = data.get(subject, {}).get(lang, [])

    if not questions:
        await message.answer(get_text(
            message.from_user.id,
            uz="Bu fandan savollar yo‘q.",
            ru="По этому предмету нет вопросов.",
            en="No questions for this subject."
        ))
        return

    if subject == "psixologik_test":
        await state.set_state(TestState.question_index)
        await state.update_data(questions=questions, index=0, answers=[], subject=subject)
    else:
        await state.set_state(TestState.question_index)
        await state.update_data(questions=questions, index=0, subject=subject, correct_count=0, wrong_count=0)
    await send_question(message, 0, state)

async def send_question(message: Message, index: int, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    if index >= len(questions):
        await message.answer(get_text(message.from_user.id, uz="✅ Barcha testlar yakunlandi.", ru="✅ Все тесты завершены.", en="✅ All tests completed."))
        await state.clear()
        return

    question = questions[index]
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=question["options"][0], callback_data=f"answer_A_{index}")],
        [InlineKeyboardButton(text=question["options"][1], callback_data=f"answer_B_{index}")],
        [InlineKeyboardButton(text=question["options"][2], callback_data=f"answer_C_{index}")]
    ])
    await message.answer(f"{index + 1}) {question['question']}", reply_markup=markup)

def get_psix_result(answers, user_id):
    lang = user_languages[user_id]
    count = Counter(answers)
    a, b, c = count.get("A", 0), count.get("B", 0), count.get("C", 0)
    if a >= b and a >= c:
        return {
            "uz": "Siz ochiqko‘ngil, faol va ijtimoiy odamsiz. Yangi tanishuv va sarguzashtlarni yaxshi ko‘rasiz.",
            "ru": "Вы открытый, активный и общительный человек. Любите новые знакомства и приключения.",
            "en": "You are open, active, and sociable. You love new acquaintances and adventures."
        }[lang]
    elif b >= a and b >= c:
        return {
            "uz": "Siz tahlilchi, tinch va mustaqil odamsiz. O‘zingizni rivojlantirishni va bilim orttirishni xush ko‘rasiz.",
            "ru": "Вы аналитик, спокойный и независимый человек. Любите саморазвитие и получать новые знания.",
            "en": "You are analytical, calm, and independent. You enjoy self-development and gaining new knowledge."
        }[lang]
    else:
        return {
            "uz": "Siz ijodiy va o‘ziga xos odamsiz. Odamlar bilan ishlash va jamoada bo‘lish sizga yoqadi.",
            "ru": "Вы креативный и необычный человек. Любите работать с людьми и быть в команде.",
            "en": "You are creative and unique. You like working with people and being part of a team."
        }[lang]

def get_test_result(correct, wrong, total, user_id):
    lang = user_languages[user_id]
    return {
        "uz": f"Test yakuni:\n\nSavollar soni: {total}\nTo‘g‘ri javoblar: {correct}\nNoto‘g‘ri javoblar: {wrong}\n\n{('Ajoyib natija!' if correct == total else 'Yaxshi harakat!')}",
        "ru": f"Результаты теста:\n\nВсего вопросов: {total}\nПравильных ответов: {correct}\nНеправильных ответов: {wrong}\n\n{('Отличный результат!' if correct == total else 'Хорошая попытка!')}",
        "en": f"Test result:\n\nTotal questions: {total}\nCorrect answers: {correct}\nWrong answers: {wrong}\n\n{('Excellent result!' if correct == total else 'Good try!')}"
    }[lang]

@router.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    save_user(callback.from_user)
    data = await state.get_data()
    if not data:
        await callback.answer("❗ Holat mavjud emas. /start dan boshlang.")
        return

    parts = callback.data.split("_")
    user_answer = parts[1]
    index = int(parts[2])
    questions = data.get("questions", [])
    subject = data.get("subject", "")
    answers = data.get("answers", [])
    correct_count = data.get("correct_count", 0)
    wrong_count = data.get("wrong_count", 0)

    if index >= len(questions):
        await callback.answer("❗ Savol topilmadi.")
        return

    if subject == "psixologik_test":
        answers.append(user_answer)
        await state.update_data(answers=answers)
        await callback.message.answer(get_text(
            callback.from_user.id,
            uz="✅ Javobingiz qabul qilindi.",
            ru="✅ Ваш ответ принят.",
            en="✅ Your answer has been accepted."
        ))
        if index + 1 >= len(questions):
            result = get_psix_result(answers, callback.from_user.id)
            await callback.message.answer(result)
            await state.clear()
            await callback.answer()
            return
    else:
        question = questions[index]
        correct_letter = question.get("answer", "")[0] if question.get("answer") else ""
        if user_answer == correct_letter:
            correct_count += 1
            await callback.message.answer(get_text(callback.from_user.id, uz="✅ To‘g‘ri javob!", ru="✅ Правильный ответ!", en="✅ Correct answer!"))
        else:
            wrong_count += 1
            await callback.message.answer(get_text(callback.from_user.id, uz=f"❌ Noto‘g‘ri. To‘g‘ri javob: {question['answer']}", ru=f"❌ Неправильно. Правильный ответ: {question['answer']}", en=f"❌ Incorrect. Correct answer: {question['answer']}"))
        if index + 1 >= len(questions):
            total = correct_count + wrong_count
            result = get_test_result(correct_count, wrong_count, total, callback.from_user.id)
            await callback.message.answer(result)
            await state.clear()
            await callback.answer()
            return
        await state.update_data(correct_count=correct_count, wrong_count=wrong_count)

    await state.update_data(index=index + 1)
    await callback.answer()
    await send_question(callback.message, index + 1, state)

@router.message(F.text == "/start")
async def start_handler(message: Message):
    save_user(message.from_user)
    await message.answer(
        get_text(message.from_user.id, uz="Assalomu alaykum! Qanday yordam bera olaman?", ru="Здравствуйте! Чем могу помочь?", en="Hello! How can I help you?"),
        reply_markup=get_main_menu(message.from_user.id)
    )

@router.message(F.text == "/help")
async def help_handler(message: Message):
    lang = user_languages[message.from_user.id]
    if lang == "ru":
        text = (
            "В этом боте вы можете проходить тесты по разным предметам❗️.\n\n"
            "🟢 Всегда новые тесты: Администратор может добавлять новые тесты, так что каждый раз вас ждут новые вопросы!\n"
            "📊 Статистика: Ваши результаты сохраняются в боте — следите за своим прогрессом.\n"
            "🌐 Мультиязычность: Используйте бота на узбекском, русском или английском — язык можно сменить в любой момент.\n"
            "🧠 Психологические тесты: Не только предметы — есть и психологические тесты!\n"
            "👤 Связь с админом: Есть отдельная кнопка для связи с администратором, если возникнут вопросы или предложения."
        )
    elif lang == "en":
        text = (
            "In this bot, you can solve quizzes on various subjects❗️.\n\n"
            "🟢 Always new quizzes: The admin can add new quizzes, so there are always fresh questions waiting for you!\n"
            "📊 Statistics: Your results are saved — track your progress and improve yourself.\n"
            "🌐 Multilingual: Use the bot in Uzbek, Russian, or English — change the language anytime.\n"
            "🧠 Psychological tests: Not just academic subjects, but fun psychological quizzes too!\n"
            "👤 Admin contact: Got a question or suggestion? Contact the admin directly via the special button."
        )
    else:
        text = (
            "Ushbu botda turli fanlardan testlar yechishingiz mumkin❗️.\n\n"
            "🟢 Har doim yangi testlar: Botga yangi testlarni admin qo‘sha oladi, shuning uchun har safar yangi savollar kutib turadi!\n"
            "📊 Statistika: Sizning natijalaringiz botda saqlanadi va o‘zingizni doim rivojlantira olasiz.\n"
            "🌐 Ko‘p tillilik: Botdan o‘zbek, rus yoki ingliz tilida foydalanishingiz mumkin — tilni istalgan vaqtda almashtiring.\n"
            "🧠 Psixologik testlar: Faqat fanlar emas, psixologik testlar ham mavjud!\n"
            "👤 Admin bilan aloqa: Savol yoki takliflaringiz bo‘lsa, admin bilan bevosita bog‘lanish tugmasi orqali yozishingiz mumkin."
        )
    await message.answer(text)

@router.message(F.text.in_(["Test yechish", "Пройти тест", "Take a test"]))
async def test_category_menu(message: Message):
    save_user(message.from_user)
    await message.answer(
        get_text(message.from_user.id, uz="Fanni tanlang:", ru="Выберите предмет:", en="Choose a subject:"),
        reply_markup=get_category_menu(message.from_user.id)
    )

@router.message(F.text.in_(["🖐 Ortga", "🖐 Назад", "🖐 Back"]))
async def back_to_main(message: Message):
    save_user(message.from_user)
    await message.answer(
        get_text(message.from_user.id, uz="Bosh menyuga qaytdingiz.", ru="Вы вернулись в главное меню.", en="Returned to main menu."),
        reply_markup=get_main_menu(message.from_user.id)
    )

@router.message(lambda msg: msg.text in subject_mapping and subject_mapping[msg.text] != "back")
async def universal_subject_handler(message: Message, state: FSMContext):
    save_user(message.from_user)
    subject_key = subject_mapping[message.text]
    await load_and_start_test(subject_key, message, state)

@router.message(F.text.in_(["Test qo‘shish (admin uchun)", "Добавить тест (для админа)", "Add test (for admin)"]))
async def ask_admin_test(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Siz admin emassiz yoki sizda bu amalni bajarishga ruxsat yo‘q!")
        return
    await message.answer(get_text(message.from_user.id,
        uz="Test savolini quyidagi formatda yuboring:\n\nSavol: 2 + 2 nechiga teng?\nA) 3\nB) 4\nC) 5\nTo‘g‘ri javob: B",
        ru="Вышлите вопрос в следующем формате:\n\nВопрос: 2 + 2 = ?\nA) 3\nB) 4\nC) 5\nПравильный ответ: B",
        en="Send the test question in the following format:\n\nQuestion: 2 + 2 = ?\nA) 3\nB) 4\nC) 5\nCorrect answer: B"
    ))

@router.message(F.text.startswith("Savol:"))
async def receive_test_question(message: Message):
    save_user(message.from_user)
    if message.from_user.id != ADMIN_ID:
        await message.answer("Siz admin emassiz yoki sizda bu amalni bajarishga ruxsat yo‘q!")
        return

    subject = "matematika"
    lang = user_languages[message.from_user.id]
    file_name = SAVOLLAR_FILE

    if os.path.exists(file_name):
        with open(file_name, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = {}
    else:
        data = {}

    lines = message.text.strip().split("\n")
    if len(lines) < 5:
        await message.answer("Format noto‘g‘ri. To‘liq kiriting.")
        return

    savol = lines[0][7:].strip()
    A = lines[1][3:].strip()
    B = lines[2][3:].strip()
    C = lines[3][3:].strip()
    correct = lines[4].replace("To‘g‘ri javob:", "").strip().upper()

    correct_option = {
        "A": f"A) {A}",
        "B": f"B) {B}",
        "C": f"C) {C}"
    }.get(correct)

    if not correct_option:
        await message.answer("❌ To‘g‘ri javob noto‘g‘ri formatda.")
        return

    new_question = {
        "question": savol,
        "options": [f"A) {A}", f"B) {B}", f"C) {C}"],
        "answer": correct_option
    }

    if subject in ["ingliz_tili", "ielts_reading"]:
        if subject not in data:
            data[subject] = []
        data[subject].append(new_question)
    else:
        if subject not in data:
            data[subject] = {}
        if lang not in data[subject]:
            data[subject][lang] = []
        data[subject][lang].append(new_question)

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await message.answer("✅ Test saqlandi.")

@router.message(F.text.in_(["Sozlamalar", "Настройки", "Settings"]))
async def settings_handler(message: Message):
    save_user(message.from_user)
    await message.answer(get_text(message.from_user.id, uz="Tilni tanlang:", ru="Выберите язык:", en="Choose a language:"), reply_markup=language_keyboard)

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    save_user(callback.from_user)
    lang_code = callback.data.split("_")[-1]
    user_languages[callback.from_user.id] = lang_code
    await callback.message.answer(get_language_changed_message(lang_code), reply_markup=get_main_menu(callback.from_user.id))
    await callback.answer()

@router.message(F.text.in_(["Admin bilan bogʻlanish", "Связаться с админом", "Contact admin"]))
async def contact_admin(message: Message):
    save_user(message.from_user)
    link = f"tg://user?id={5825453938}"
    await message.answer(f"📩 Admin bilan bogʻlanish uchun shu yerni bosing: [Bogʻlanish]({link})", parse_mode="Markdown")

@router.message(F.text == "/users")
async def show_users(message: Message):
    if message.from_user.id != 5825453938:
        await message.answer("Siz admin emassiz!")
        return
    if not os.path.exists(USERS_FILE):
        await message.answer("Hali foydalanuvchilar yo‘q.")
        return
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    text = "👥 Foydalanuvchilar ro‘yxati:\n\n"
    for user_id, info in data.items():
        username = info.get("username", "")
        name = (info.get("first_name", "") + " " + info.get("last_name", "")).strip()
        text += f"{user_id} | @{username if username else '-'} | {name}\n"
    text += f"\nJami foydalanuvchilar: {len(data)}"
    await message.answer(text)

async def main():
    logging.basicConfig(level=logging.INFO)
    await set_bot_commands(bot)
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
