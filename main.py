import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from models import create_tables, UserWord, User

DSN = 'postgresql://postgres:admin@localhost:5432/telegram_bd'
engine = sqlalchemy.create_engine(DSN)
create_tables(engine)

Session = sessionmaker(bind=engine)
session = Session()

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = '6806888400:AAGQvyvk9YR3v4o-OvHecU3L_qIpC4MqwYM'
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []

class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

def show_hint(*lines):
    return '\n'.join(lines)

def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0

def fill_database():
    common_words = ['Red', 'Blue', 'Green', 'Yellow', 'Orange', 'Purple', 'Black', 'White', 'Dog', 'Cat']
    for word in common_words:
        new_word = UserWord(word=word, user=None)
        session.add(new_word)
    session.commit()


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        userStep[cid] = 0
        bot.send_message(cid, "Привет, давай изучим английский язык")

    user = session.query(User).filter_by(chat_id=cid).first()
    if user:
        words = [user_word.word for user_word in user.words]
    else:
        user = User(chat_id=cid)
        session.add(user)
        session.commit()
        words = [user_word.word for user_word in user.words]

    # Set target word and translate from database
    if words:
        target_word = random.choice(words)
        translate = "Translate of " + target_word  # Temporary translation for demonstration
        target_word_btn = types.KeyboardButton(target_word)
        others = [random.choice(words) for _ in range(3)]
        while target_word in others:
            others = [random.choice(words) for _ in range(3)]

        buttons = [target_word_btn]
        for word in others:
            buttons.append(types.KeyboardButton(word))

        markup = types.ReplyKeyboardMarkup()
        markup.add(*buttons)

        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['correct_answer'] = target_word

        bot.send_message(cid, translate, reply_markup=markup)
    else:
        bot.send_message(cid, "Список слов пустой. Пожалуйста, добавьте слова для изучения.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        correct_answer = data['correct_answer']

        if text == correct_answer:
            bot.send_message(message.chat.id, "Правильно! 🎉")
        else:
            bot.send_message(message.chat.id, "Неправильно, попробуй ещё раз!")

        create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    user = session.query(User).filter_by(chat_id=cid).first()
    word = message.text
    word_to_delete = session.query(UserWord).filter_by(user=user, word=word).first()
    session.delete(word_to_delete)
    session.commit()

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    word = message.text
    user = session.query(User).filter_by(chat_id=cid).first()
    new_word = UserWord(word=word, user=user)
    session.add(new_word)
    session.commit()

@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if 'target_word' not in data:
            create_cards(message)
            return

        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤️", hint]
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")

    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))

fill_database()
bot.infinity_polling(skip_pending=True)