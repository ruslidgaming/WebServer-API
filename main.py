import logging
from telegram.ext import Updater, MessageHandler, Filters
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram.ext import ConversationHandler
import sqlite3
import pandas as pd
import dataframe_image as dfi
import telebot
import schedule, time
import datetime

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

# Расписание занятий на неделю
SCHEDULE = [
    ['английский язык', 'математика', 'родной язык', 'физика'],
    ['математика', 'информатика', 'русский язык', 'история'],
    ['информатика', 'обж', 'физкультура'],
    ['история', 'физика', 'литература'],
    ['математика', 'английский язык'],
    ['математика', 'химия'],
]

logger = logging.getLogger(__name__)

# Токен
TOKEN = '5066165607:AAEU9ovd5Zs0En3bOmz5znA4KU3QytLL6Ww'

# Смайлики
SMILE = ['🧠', '💬', '👻', '🤗', '🥱',
         '💤', '🥴', '☠', '❤', '🤥', '⛹️']

bot = telebot.TeleBot(TOKEN)


reply_keyboard = [['/edit_text', '/conclusion'], ['/change_picture', '/delete_picture'],
                  ['/table'], ['/enable_notifications']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

reply_keyboard2 = [['/stop']]
markup2 = ReplyKeyboardMarkup(reply_keyboard2, one_time_keyboard=True)

con = sqlite3.connect("object_db.sqlite")
cur = con.cursor()
result = cur.execute(f'''SELECT object FROM object ''').fetchall()
object = []  # Сюда добавляем предметы из базы данных
homework = []  # Сюда добавляем домашнее задание из базы данных
for i in result:
    object.append(i[0])
result = cur.execute(f'''SELECT homework FROM object ''').fetchall()
for i in result:
    homework.append(i[0])
con.close()


# Здесь пользователь выбирает предмет
def choose(update, context):
    text = ''
    for i in range(len(object)):
        text += f'{object[i]} {SMILE[i]}\n'
    update.message.reply_text(f'Выберите предмет:\n{text}', reply_markup=markup2)
    return 1


# Ввод изменения домашнего задания для этого предмета
def object_inp(update, context):
    context.user_data['object'] = str(update.message.text)
    if context.user_data['object'] in object:
        update.message.reply_text(f'Вы выбрали предмет: {context.user_data["object"]}')
        update.message.reply_text('Введите своё изменение:')
        return 2
    else:
        update.message.reply_text('Такого предмета нет в списке',
                                  reply_markup=markup
                                  )
        update.message.reply_text('Возвращаюсь в начало')
        context.user_data.clear()
        return ConversationHandler.END


# Фиксация изменений
def object_change(update, context):
    context.user_data['change'] = update.message.text
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    cur.execute(f"""UPDATE object 
                    SET homework = '{context.user_data['change']}'
                    WHERE object = '{context.user_data['object']}'""").fetchall()
    result = cur.execute(f'''SELECT homework FROM object 
                    WHERE object = "{context.user_data["object"]}"''').fetchall()
    for elem in result:
        update.message.reply_text(f'Успешно\n{context.user_data["object"]}: {elem[0]}',
                                  reply_markup=markup
                                  )
    con.commit()
    con.close()
    context.user_data.clear()
    return ConversationHandler.END


# Вывод домашнего задания по данному предмету
def object_input(update, context):
    context.user_data['object'] = update.message.text
    if context.user_data['object'] in object:
        update.message.reply_text(f'Вы выбрали предмет: {context.user_data["object"]}')
        con = sqlite3.connect("object_db.sqlite")
        cur = con.cursor()
        result = cur.execute(f'''SELECT img FROM object 
                            WHERE object = "{context.user_data["object"]}"''').fetchall()
        text = cur.execute(f'''SELECT homework FROM object 
                            WHERE object = "{context.user_data["object"]}"''').fetchall()
        image = result[0][0]
        if image == None:
            update.message.reply_text(text[0][0], reply_markup=markup)
        else:
            update.message.reply_photo(photo=image, reply_markup=markup, caption=text[0][0])
            con.close()
    else:
        update.message.reply_text(f'Такого предмета нет в списке',
                                  reply_markup=markup
                                  )
        update.message.reply_text('Возвращаюсь в начало')
        context.user_data.clear()
    return ConversationHandler.END


# Начало работы
def start(update, context):
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    user_id = update.message.from_user.id
    users = []
    for i in cur.execute(f'''SELECT chat_id FROM notifications ''').fetchall():
        users.append(i[0])
    if user_id in users:
        reply_keyboard[3] = ['/off_notifications']
    else:
        reply_keyboard[3] = ['/enable_notifications']
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        "Привет",
        reply_markup=markup
    )
    con.close()


# Помощь
def help(update, context):
    update.message.reply_text("Привет, это помощь по боту.\n"
                              "Этот бот предназначен для записи домашнего задания и впоследствии его вывода.\n"
                              "Можно считать его своеобразным дневниеом, которым могут пользоваться целые классы\n"
                              "Чтобы начать напишите /start\n"
                              "Чтобы записать, изменить домашнее задание напишите или нажмите: /edit_text\n"
                              "Чтобы добавить картинку к домашнему заданию напишите: /change_picture\n"
                              "Для удаления картинки: /delete_picture\n"
                              "Для вывода домашнего задания по тому или иному предмету: /conclusion\n"
                              "Также можно вывести таблицу со всем домашним заданием: /table\n"
                              "Для подписки на расылку: /enable_notifications\n"
                              "Для отписки на рассылку: /off_notifications")


# Остановка действия, возвращение в начало
def stop(update, context):
    update.message.reply_text("Возвращаюсь в начало",
                              reply_markup=markup)
    context.user_data.clear()
    return ConversationHandler.END


# Вывод таблицы домашнего задания
def img_input(update, context):
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    result = cur.execute(f'''SELECT object FROM object ''').fetchall()
    object = []
    homework = []
    for i in result:
        object.append(i[0])
    result = cur.execute(f'''SELECT homework FROM object ''').fetchall()
    for i in result:
        homework.append(i[0])
    df = pd.DataFrame({"Предметы": object, "Задания": homework})
    df_styled = df.style.background_gradient()
    dfi.export(df_styled, "mytable.png")
    update.message.reply_photo(open('mytable.png', 'rb'))


# Ввод картинки для данного предмета
def img_inp(update, context):
    context.user_data['object'] = update.message.text
    if context.user_data['object'] in object:
        update.message.reply_text(f'Вы выбрали предмет: {context.user_data["object"]}')
        update.message.reply_text('Отправьте картинку')
        return 2
    else:
        update.message.reply_text(f'Такого предмета нет в списке',
                                  reply_markup=markup
                                  )
        update.message.reply_text('Возвращаюсь в начало')
        context.user_data.clear()
        return ConversationHandler.END


# Сохранение картинки
def get_pic(update, context):
    if update.message.media_group_id:
        photo_id = update.message.photo[0].file_id
        print(photo_id)
    photo = update.message.photo[-1]
    update.message.reply_photo(photo=photo, caption=f'Успешно изменена фотография для предмета: '
                                                    f'{context.user_data["object"]}', reply_markup=markup)
    file_info = bot.get_file(update.message.photo[len(update.message.photo) - 1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    cur.execute(f"""UPDATE object 
                     SET img = ? 
                    WHERE object = ?""", (downloaded_file, context.user_data['object'])).fetchall()
    con.commit()
    con.close()
    return ConversationHandler.END


# Удаление картинки
def delete_picture(update, context):
    context.user_data['object'] = str(update.message.text)
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    cur.execute(f"""UPDATE object 
                    SET img = ? 
                    WHERE object = ?""", (None, context.user_data['object'])).fetchall()
    con.commit()
    con.close()
    update.message.reply_text(f'Успешно удалена фотография для предмета: {context.user_data["object"]}',
                              reply_markup=markup)


# Подписка на рассылку
def enable_notifications(update, context):
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    user_id = update.message.from_user.id
    users = []
    for i in cur.execute(f'''SELECT chat_id FROM notifications ''').fetchall():
        users.append(i[0])
    if user_id not in users:
        cur.execute(f"""INSERT INTO notifications(chat_id, name) 
                        VALUES({user_id}, '{update.message.from_user.first_name}')""").fetchall()
    reply_keyboard[3] = ['/off_notifications']
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Вы успешно подписались на рассылку', reply_markup=markup)
    con.commit()
    con.close()


# Отписка от рассылки
def off_notifications(update, context):
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    user_id = update.message.from_user.id
    users = []
    for i in cur.execute(f'''SELECT chat_id FROM notifications ''').fetchall():
        users.append(i[0])
    if user_id in users:
        cur.execute(f'''DELETE from notifications
                        where chat_id = {user_id}''').fetchall()
    reply_keyboard[3] = ['/enable_notifications']
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Вы успешно отписались от рассылки', reply_markup=markup)
    con.commit()
    con.close()


# Напоминание по рассылке
def send_messange():
    week = datetime.datetime.today().weekday()
    if week == 5:
        return
    con = sqlite3.connect("object_db.sqlite")
    cur = con.cursor()
    users = []
    for i in cur.execute(f'''SELECT chat_id FROM notifications ''').fetchall():
        users.append(i[0])
    inp = ''
    for i in SCHEDULE[week + 1]:
        inp += f'{i}\n'
    for i in users:
        bot.send_message(i, f'Напоминание.\n'
                            f'Сегодня нужно сделать:\n'
                            f'{inp}')
    con.close()


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("add", input))
    dp.add_handler(CommandHandler("table", img_input))
    dp.add_handler(CommandHandler("enable_notifications", enable_notifications))
    dp.add_handler(CommandHandler("off_notifications", off_notifications))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('edit_text', choose)],
        states={
            # Добавили user_data для сохранения ответа.
            1: [MessageHandler(Filters.text & ~Filters.command, object_inp, pass_user_data=True)],
            2: [MessageHandler(Filters.text & ~Filters.command, object_change, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler('conclusion', choose)],
        states={
            # Добавили user_data для сохранения ответа.
            1: [MessageHandler(Filters.text & ~Filters.command, object_input, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler3 = ConversationHandler(
        entry_points=[CommandHandler('change_picture', choose)],
        states={
            # Добавили user_data для сохранения ответа.
            1: [MessageHandler(Filters.text & ~Filters.command, img_inp, pass_user_data=True)],
            2: [MessageHandler(Filters.photo, get_pic, pass_user_data=True)],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    conv_handler4= ConversationHandler(
        entry_points=[CommandHandler('delete_picture', choose)],
        states={
            # Добавили user_data для сохранения ответа.
            1: [MessageHandler(Filters.text & ~Filters.command, delete_picture, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(conv_handler2)
    dp.add_handler(conv_handler3)
    dp.add_handler(conv_handler4)
    updater.start_polling()
    schedule.every().day.at("19:00").do(send_messange)
    while True:
        schedule.run_pending()
        time.sleep(1)
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()