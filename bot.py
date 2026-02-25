import asyncio
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_CHAT_IDS = os.getenv("OWNER_CHAT_IDS")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set in .env")
if not OWNER_CHAT_IDS:
    raise RuntimeError("OWNER_CHAT_IDS not set in .env")

OWNER_CHAT_IDS_LIST = [int(x.strip()) for x in OWNER_CHAT_IDS.split(",") if x.strip()]


# --- UI buttons ---
BTN_BACK = "⬅️ Назад"
BTN_RESTART = "🔄 В начало"
BTN_CANCEL = "❌ Отмена"

nav_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=BTN_BACK), KeyboardButton(text=BTN_RESTART)],
        [KeyboardButton(text=BTN_CANCEL)],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# --- States ---
class Brief(StatesGroup):
    name = State()
    phone = State()
    company = State()
    niche = State()
    geo = State()
    problem = State()
    services = State()
    budget = State()
    timeline = State()
    links = State()
    history = State()
    meeting_slots = State()


# Order of steps for Back navigation
STEP_ORDER = [
    Brief.name,
    Brief.phone,
    Brief.company,
    Brief.niche,
    Brief.geo,
    Brief.problem,
    Brief.services,
    Brief.budget,
    Brief.timeline,
    Brief.links,
    Brief.history,
    Brief.meeting_slots,
]

# Which data key each step writes to
STEP_KEY = {
    Brief.name: "name",
    Brief.phone: "phone",
    Brief.company: "company",
    Brief.niche: "niche",
    Brief.geo: "geo",
    Brief.problem: "problem",
    Brief.services: "services",
    Brief.budget: "budget",
    Brief.timeline: "timeline",
    Brief.links: "links",
    Brief.history: "history",
    Brief.meeting_slots: "meeting_slots",
}

# Prompts per step
PROMPT = {
    Brief.name: "Ваше имя:",
    Brief.phone: "Телефон:",
    Brief.company: "Название компании/проекта:",
    Brief.niche: "Ниша проекта:",
    Brief.geo: "Гео проекта (в какой стране/регионе продается ваш товар/услуга):",
    Brief.problem: "Какая проблема сейчас стоит перед вами?",
    Brief.services: (
        "Какие услуги вас интересуют?\n"
        "Если не знаете — опишите, что ждете от команды маркетологов."
    ),
    Brief.budget: "Какой у вас ориентировочный бюджет в месяц на продвижение?",
    Brief.timeline: "В какие сроки вы хотели бы начать работу?",
    Brief.links: (
        "Пришлите ссылки на ваш проект (сайт, соцсети).\n"
        "Если нет ничего — напишите «нет»."
    ),
    Brief.history: "Поделитесь, что уже пробовали раньше в продвижении проекта:",
    Brief.meeting_slots: "Напишите удобные для вас слоты для встречи с нами онлайн:",
}


def format_summary(data: dict, user: Message) -> str:
    lines = [
        "🧾 Новый бриф с сайта vmesteburo.ru",
        "",
        f"👤 Имя: {data.get('name')}",
        f"📞 Телефон: {data.get('phone')}",
        f"🏢 Компания/проект: {data.get('company')}",
        f"🏷 Ниша: {data.get('niche')}",
        f"🌍 Гео: {data.get('geo')}",
        "",
        f"🔥 Проблема: {data.get('problem')}",
        "",
        f"🧩 Услуги / ожидания: {data.get('services')}",
        f"💰 Бюджет/мес: {data.get('budget')}",
        f"⏳ Сроки старта: {data.get('timeline')}",
        "",
        f"🔗 Ссылки: {data.get('links')}",
        "",
        f"📊 Что пробовали: {data.get('history')}",
        "",
        f"🗓 Слоты для встречи: {data.get('meeting_slots')}",
        "",
        "—",
        f"Telegram: @{user.from_user.username}" if user.from_user.username else "Telegram: username нет",
        f"User ID: {user.from_user.id}",
    ]
    return "\n".join(lines)


async def go_to_step(message: Message, state: FSMContext, step: State):
    """Set state and ask the question for that step."""
    await state.set_state(step)
    await message.answer(PROMPT[step], reply_markup=nav_kb)


async def start_flow(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Добрый день! Вас приветствует бот от vmesteburo.ru 👋\n\n"
        "Эта краткая форма поможет нам лучше подготовиться к встрече с вами.\n\n"
        "Можно в любой момент нажать:\n"
        f"— {BTN_BACK} (предыдущий вопрос)\n"
        f"— {BTN_RESTART} (начать заново)\n"
        f"— {BTN_CANCEL} (остановить заполнение)\n",
        reply_markup=nav_kb,
    )
    await go_to_step(message, state, Brief.name)


bot = Bot(BOT_TOKEN)
dp = Dispatcher()


# --- Global commands/buttons ---
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await start_flow(message, state)


@dp.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext):
    await start_flow(message, state)


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, остановила заполнение. Если захотите начать заново — отправьте /start.")


@dp.message(F.text == BTN_CANCEL)
async def btn_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Ок, остановила заполнение. Если захотите начать заново — отправьте /start.")


@dp.message(F.text == BTN_RESTART)
async def btn_restart(message: Message, state: FSMContext):
    await start_flow(message, state)


@dp.message(Command("back"))
async def cmd_back(message: Message, state: FSMContext):
    await handle_back(message, state)


@dp.message(F.text == BTN_BACK)
async def btn_back(message: Message, state: FSMContext):
    await handle_back(message, state)


async def handle_back(message: Message, state: FSMContext):
    current = await state.get_state()
    if not current:
        await message.answer("Вы ещё не начали заполнение. Напишите /start.")
        return

    # Convert current state string to State object by matching
    # In aiogram, state.get_state() returns something like "Brief:name"
    # We'll find matching step by its state name suffix.
    current_suffix = current.split(":")[-1]

    idx = None
    for i, step in enumerate(STEP_ORDER):
        if step.state == current_suffix:
            idx = i
            break

    if idx is None:
        await message.answer("Не смогла определить текущий шаг. Напишите /start, чтобы начать заново.")
        return

    if idx == 0:
        await message.answer("Вы уже на первом вопросе.", reply_markup=nav_kb)
        await go_to_step(message, state, STEP_ORDER[0])
        return

    prev_step = STEP_ORDER[idx - 1]
    # Optional: wipe value of current step (so it doesn't remain partially wrong)
    data = await state.get_data()
    cur_step_obj = STEP_ORDER[idx]
    cur_key = STEP_KEY.get(cur_step_obj)
    if cur_key and cur_key in data:
        data.pop(cur_key, None)
        await state.set_data(data)

    await go_to_step(message, state, prev_step)


# --- Step handlers (save answer + move next) ---
async def save_and_next(message: Message, state: FSMContext, step: State):
    # Save answer
    key = STEP_KEY[step]
    await state.update_data(**{key: message.text.strip()})

    # Move to next step or finish
    current_suffix = step.state
    idx = next(i for i, s in enumerate(STEP_ORDER) if s.state == current_suffix)

    if idx == len(STEP_ORDER) - 1:
        data = await state.get_data()
        summary = format_summary(data, message)

        for chat_id in OWNER_CHAT_IDS_LIST:
            await bot.send_message(chat_id=chat_id, text=summary)

        await message.answer("Спасибо! Мы получили информацию и свяжемся с вами 🤝")
        await state.clear()
        return

    next_step = STEP_ORDER[idx + 1]
    await go_to_step(message, state, next_step)


@dp.message(Brief.name, F.text)
async def step_name(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.name)


@dp.message(Brief.phone, F.text)
async def step_phone(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.phone)


@dp.message(Brief.company, F.text)
async def step_company(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.company)


@dp.message(Brief.niche, F.text)
async def step_niche(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.niche)


@dp.message(Brief.geo, F.text)
async def step_geo(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.geo)


@dp.message(Brief.problem, F.text)
async def step_problem(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.problem)


@dp.message(Brief.services, F.text)
async def step_services(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.services)


@dp.message(Brief.budget, F.text)
async def step_budget(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.budget)


@dp.message(Brief.timeline, F.text)
async def step_timeline(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.timeline)


@dp.message(Brief.links, F.text)
async def step_links(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.links)


@dp.message(Brief.history, F.text)
async def step_history(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.history)


@dp.message(Brief.meeting_slots, F.text)
async def step_meeting_slots(message: Message, state: FSMContext):
    await save_and_next(message, state, Brief.meeting_slots)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())