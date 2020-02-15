import telebot
import pymysql
import pymysql.cursors
from telebot import types
import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL, sslmode='require')

start,title,location,location_text,photo,stop,vivod= range(7)
from collections import defaultdict
user_state = defaultdict(lambda :start)
text_state = defaultdict(lambda :start)
data = {'users':{}}
con = pymysql.connect('localhost', 'root',
                      'roman', 'bot',cursorclass=pymysql.cursors.DictCursor)
token = '1065495049:AAEcREziu5RwO94qtk46kb-kgeaKWA2LrJ4'
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'],content_types=['text'],func = lambda message:get_state(message) == start)
def handler_message(message):
    bot.send_message(message.chat.id,'Начнем! Выберите одну из комманд.')


@bot.message_handler(commands=['add'],content_types=['text'],func = lambda message:get_state(message) == start)
def handler_message(message):
    data['users'][str(message.chat.id)] = {}
    update_state(message, title)
    bot.send_message(message.chat.id,'Укажите название места.')
    bot.send_message(message.chat.id, 'Напишите в любой момент "Отмена", если хотите отменить добавление.')

@bot.message_handler(content_types=['text','photo','location'],func = lambda message:get_state(message) == title)
def handler_pribav(message):
    print('Это' , message.chat.id)
    if message.photo or message.location:
        bot.send_message(message.chat.id, 'Я вас не понимаю. Укажите название места.')
    else:
        if 'отмена' in message.text.lower():
            update_state(message, start)
            bot.send_message(message.chat.id, 'Добавление отменено.')
        else:
            data['users'][str(message.chat.id)]['title'] = message.text
            bot.send_message(message.chat.id,'Укажите адрес (Геопозиция).')
            update_state(message, location)

@bot.message_handler(content_types=['location'],func = lambda message:get_state(message) == location)
def handler_location(message):
    data['users'][str(message.chat.id)]['longitude'] = message.location.longitude
    data['users'][str(message.chat.id)]['latitude'] = message.location.latitude
    bot.send_message(message.chat.id,'Хотите прикрепить фотографию?')
    update_state(message,location_text)

@bot.message_handler(content_types=['text','photo'],func = lambda message:get_state(message) == location)
def handler_location(message):
    if message.photo:
        bot.send_message(message.chat.id, 'Я вас не понимаю. Укажите адрес (Геопозиция).')
    else:
        if 'отмена' in message.text.lower():
            update_state(message, start)
            bot.send_message(message.chat.id, 'Добавление отменено.')
        else:
            bot.send_message(message.chat.id, 'Я вас не понимаю. Укажите адрес (Геопозиция).')
@bot.message_handler(content_types=['text','photo','location'],func = lambda message:get_state(message) == location_text)
def handler_consent(message):
    if message.photo or message.location:
        bot.send_message(message.chat.id, 'Я вас не понимаю. Хотите прикрепить фотографию?')
    else:
        if 'отмена' == message.text.lower():
            update_state(message, start)
            bot.send_message(message.chat.id, 'Добавление отменено.')
        else:
            if 'да' in message.text.lower():
                bot.send_message(message.chat.id,'Прикрепите фотографию.')
                update_state(message, photo)
            elif 'нет' in message.text.lower() or 'не' in message.text.lower():
                with con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO address(title,latitude,longitude,users) VALUES ('%s','%s','%s','%s')"%(data['users'][str(message.chat.id)]['title'],data['users'][str(message.chat.id)]['latitude'],data['users'][str(message.chat.id)]['longitude'],int(message.chat.id)))
                bot.send_message(message.chat.id, 'Место сохранено!')
                update_state(message, start)
            else:
                bot.send_message(message.chat.id, 'Я вас не понимаю. Хотите прикрепить фотографию?')

@bot.message_handler(content_types=['photo'],func = lambda message:get_state(message) == photo)
def handler_consent(message):
    data['users'][str(message.chat.id)]['img']=message.photo[0].file_id
    bot.send_message(message.chat.id, 'Место сохранено!')
    with con:
        cur = con.cursor()
        cur.execute("INSERT INTO address(title,latitude,longitude,img,users) VALUES ('%s','%s','%s','%s','%s')"%(data['users'][str(message.chat.id)]['title'],data['users'][str(message.chat.id)]['latitude'],data['users'][str(message.chat.id)]['longitude'],data['users'][str(message.chat.id)]['img'],int(message.chat.id)))
    update_state(message, start)

@bot.message_handler(content_types=['text','location'],func = lambda message:get_state(message) == photo)
def handler_consent(message):
    if message.location:
        bot.send_message(message.chat.id,text='Я вас не понимаю. Прикрепите фотографию.')
    else:
        if 'отмена' in message.text.lower():
            update_state(message, start)
            bot.send_message(message.chat.id, 'Добавление отменено.')
        else:
            bot.send_message(message.chat.id, 'Я вас не понимаю. Прикрепите фотографию.')
@bot.message_handler(commands=['list'],content_types=['text'],func = lambda message:get_state(message) == start)
def handler_list(message):
    with con:
        cur = con.cursor()
        cur.execute('SELECT title, latitude, longitude, img from address where users = %s LIMIT 10'%(message.chat.id))
        re = cur.fetchall()
        if re:
            for index,elem in enumerate(re):
                name = elem['title']
                lat = elem['latitude']
                lon = elem['longitude']
                img = elem['img']
                if img:
                    bot.send_message(message.chat.id,text=f'{str(index+1)}. {name}')
                    bot.send_location(message.chat.id,latitude=lat,longitude=lon)
                    bot.send_photo(message.chat.id,photo=img)
                else:
                    bot.send_message(message.chat.id, text=f'{str(index + 1)}. {name}')
                    bot.send_location(message.chat.id, latitude=lat, longitude=lon)

        else:
            bot.send_message(message.chat.id, text="У вас нет сохранённых мест.")


@bot.message_handler(commands=['reset'],content_types=['text'],func = lambda message:get_state(message) == start)
def handler_list(message):
    with con:
        cur = con.cursor()
        cur.execute('SELECT title, latitude, longitude, img from address where users = %s LIMIT 10'%(message.chat.id))
        re = cur.fetchall()
    if re:
        bot.send_message(message.chat.id, text='Удалить сохранённые места?')
        update_text(message,stop)
    else:
        bot.send_message(message.chat.id, text="У вас нет сохранённых мест.")

@bot.message_handler(content_types=['text'],func = lambda message:get_text_state(message) == stop)
def handler_reset_sogl(message):
    if 'да' in message.text.lower():
        bot.send_message(message.chat.id, text='Места удалены.')
        update_text(message, start)
        with con:
            cur = con.cursor()
            cur.execute(
                'DELETE FROM address WHERE users = %s' % (message.chat.id))
    elif 'нет' in message.text.lower():
        bot.send_message(message.chat.id, text='Удаление отменено.')
    else:
        bot.send_message(message.chat.id, text='Я вас не понимаю. Удалить сохранённые места?')

@bot.message_handler(commands=['search'],content_types=['text'],func = lambda message:get_state(message) == start)
def handler_message(message):
    bot.send_message(message.chat.id, 'Введите название места.')
    update_text(message,vivod)

@bot.message_handler(content_types=['text'],func = lambda message:get_text_state(message) == vivod)
def handler_message(message):
    with con:
        cur = con.cursor()
        cur.execute(
            f"select * FROM address WHERE title = '{message.text}' and users = {message.chat.id};")
        re = cur.fetchall()
        if re:
            for index, elem in enumerate(re):
                name = elem['title']
                lat = elem['latitude']
                lon = elem['longitude']
                img = elem['img']
                update_text(message, start)
                if img:
                    bot.send_message(message.chat.id, text=f'{str(index + 1)}. {name}')
                    bot.send_location(message.chat.id, latitude=lat, longitude=lon)
                    bot.send_photo(message.chat.id, photo=img)
                else:
                    bot.send_message(message.chat.id, text=f'{str(index + 1)}. {name}')
                    bot.send_location(message.chat.id, latitude=lat, longitude=lon)

        else:
            update_text(message, start)
            bot.send_message(message.chat.id, text="У вас нет сохранённых мест с данным названием.")



@bot.message_handler(content_types=['text','photo','location'],func = lambda message:get_state(message) == start)
def handler_message(message):
    bot.send_message(message.chat.id,'Я вас не понимаю. Выберите одну из комманд.')





def get_text_state(message):
    return text_state[message.chat.id]

def get_state(message):
    return user_state[message.chat.id]

def update_text(message,state):
    text_state[message.chat.id] = state

def update_state(message,state):
    user_state[message.chat.id] = state

bot.polling(none_stop=True)


