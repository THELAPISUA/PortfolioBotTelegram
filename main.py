import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from textwrap import wrap

TOKEN = os.getenv("TOKEN")
print(TOKEN)
PHOTO_MAIN = "assets/mainPhoto.jpg"

dp = Dispatcher()


class Portfolio(StatesGroup):
    FULLNAME = State()
    PHOTO = State()
    AFTER_ME = State()
    SKILLS = State()
    CONTACTS = State()


def create_portfolio(fullname, specialization, skills, contacts, photo_path, user_id):
    """Генерує PDF-файл з портфоліо"""
    folder = "assets/portfolios"
    os.makedirs(folder, exist_ok=True)
    pdf_path = os.path.join(folder, f"portfolio_{user_id}.pdf")

    pdfmetrics.registerFont(TTFont("DejaVuSans", "assets/DejaVuSans.ttf"))

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    # Заголовок
    c.setFont("DejaVuSans", 22)
    c.drawString(200-len(fullname)*2.4, height - 80, f"{fullname}")

    # Фото
    if photo_path and os.path.exists(photo_path):
        img = ImageReader(photo_path)
        c.drawImage(img, 20, height - 300, 160, 160, mask='auto')

    # Про себе
    c.setFont("DejaVuSans", 12)

    y = height - 120
    for line in wrap(f"{specialization}", 50):
        c.drawString(200, y, line)
        y -= 15

    # Скіли
    c.setFont("DejaVuSans", 13)
    c.drawString(20, height - 350, "Навички:")
    c.setFont("DejaVuSans", 12)
    text_object = c.beginText(40, height - 370)
    for line in skills.split(","):
        text_object.textLine(f"• {line.strip()}")
    c.drawText(text_object)

    #Контакти
    c.drawString(20, height - 650, "Контакти:")
    text_object = c.beginText(40, height - 670)
    for line in contacts.split(" "):
        text_object.textLine(f"• {line.strip()}")
    c.drawText(text_object)

    c.showPage()
    c.save()
    return pdf_path

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    photo = FSInputFile(PHOTO_MAIN)
    await message.answer_photo(
        photo=photo,
        caption=f"Привіт, {html.bold(message.from_user.full_name)}! 👋\n\n"
                "Я допоможу створити твоє портфоліо 📃\n\n"
                "Напиши /gen щоб почати.",
    )


@dp.message(Command("gen"))
async def start_generation(msg: Message, state: FSMContext) -> None:
    await msg.answer("Спершу напиши своє повне ім'я:")
    await state.set_state(Portfolio.FULLNAME)


@dp.message(Portfolio.FULLNAME)
async def process_fullname(msg: Message, state: FSMContext) -> None:
    await state.update_data(fullname=msg.text)
    await msg.answer("Тепер надішли своє фото (jpg або png):")
    await state.set_state(Portfolio.PHOTO)


@dp.message(Portfolio.PHOTO, F.photo)
async def process_photo(msg: Message, state: FSMContext, bot: Bot) -> None:
    photo_id = msg.photo[-1].file_id
    photo_file = await bot.get_file(photo_id)
    photo_path = f"assets/photos/{msg.from_user.id}.jpg"
    os.makedirs("assets/photos", exist_ok=True)
    await bot.download_file(photo_file.file_path, photo_path)

    await state.update_data(photo=photo_path)
    await msg.answer("Добре! Тепер розкажи про себе:")
    await state.set_state(Portfolio.AFTER_ME)


@dp.message(Portfolio.PHOTO)
async def process_photo_invalid(msg: Message) -> None:
    await msg.answer("❌ Будь ласка, надішли фото!")


@dp.message(Portfolio.AFTER_ME)
async def process_specialization(msg: Message, state: FSMContext) -> None:
    await state.update_data(specialization=msg.text)
    await msg.answer("Чудово! Тепер напиши свої навички (через кому):")
    await state.set_state(Portfolio.SKILLS)

@dp.message(Portfolio.SKILLS)
async def process_skills(msg: Message, state: FSMContext) -> None:
    await state.update_data(skills=msg.text)
    await msg.answer("Тепер щоб завершити напиши свої контакти(Телеграм,почта, і тд):")
    await state.set_state(Portfolio.CONTACTS)

@dp.message(Portfolio.CONTACTS)
async def process_contacts(msg: Message, state: FSMContext) -> None:
    await state.update_data(contacts=msg.text)
    data = await state.get_data()

    fullname = data.get("fullname")
    photo_path = data.get("photo")
    specialization = data.get("specialization")
    skills = data.get("skills")
    contacts = data.get("contacts")

    pdf_path = create_portfolio(fullname, specialization, skills, contacts, photo_path, msg.from_user.id)
    pdf_file = FSInputFile(pdf_path)

    await msg.answer_document(
        document=pdf_file,
        caption="✅ Твоє портфоліо готове!"
    )

    await state.clear()


@dp.message(Command("cancel"))
async def cancel_handler(msg: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await msg.answer("Нічого скасовувати ❌")
        return

    await state.clear()
    await msg.answer("❌ Створення портфоліо скасовано.")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
