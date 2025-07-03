import mcrcon #RCON (Команды)
import socket #Socket (RCON)
import telebot #Telegram API (Бот)
import paramiko #SFTP (Логи)
import os #os (ENV переменные)
import time #time (Задержка)
import threading #threading (Параллельные процессы)
import random #random (Рандом коды)
import mysql.connector #MySQL (База данных)



#Инициализация бота
bottoken = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(bottoken) 

adminid1 = os.getenv("ADMIN_ID_1")
admins = [adminid1] #Телеграм ID админов
#print(admins)

vips = ["mc_roma_c","LASTR0T"] #Майнкрафт ники VIP игроков
cmdbanlist = [] #Список игроков которые не могут использовать кастомные команды

tgbotname = "EB2tgbot" #Имя бота в чате сервера

#Кастомные команды
prefix = "!"
customcommands = [
    f"{prefix}test",
    f"{prefix}tglogin",
    f"{prefix}grandopen",
    f"{prefix}showdb",
    f"{prefix}help",
    f"{prefix}vipmsg",
    f"{prefix}vipparticles",
    f"{prefix}glowme",
    #f"{prefix}passlogin",
    f"{prefix}rcon"
    
]

mapurl = "https://eb2.dynmap.xyz/" #URL карты
clickerurl = "https://mcromac-alt.github.io/eb2clicker/" #URL кликера

def tgprint(chatid, text,markup): 
  return bot.send_message(chatid, text, reply_markup=markup)

# RCON
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((os.environ['RCON_HOST'], int(os.environ['RCON_PORT'])))

#SFTP
transport = paramiko.Transport((os.environ['SFTP_HOST'], int(os.environ['SFTP_PORT'])))
transport.connect(username=os.environ['SFTP_USER'], password=os.environ['SFTP_PASS'])

#MySQL
conn = mysql.connector.connect(
    host= os.environ['MYSQL_HOST'],
    user= os.environ['MYSQL_USER'],
    password= os.environ['MYSQL_PASS'],
    database= os.environ['MYSQL_DB']
)

global_log = None # Переменная для хранения лога

try:
     # ================Log in=================
    sftp = paramiko.SFTPClient.from_transport(transport) #SFTP логин
    if sftp:
        print("Connected to SFTP server")
    else:
        print("Failed to connect to SFTP server")
    
    result = mcrcon.login(sock, os.environ['RCON_PASS']) #RCON логин 
    if result:
        print("Connected to RCON server")
    else:
        print("Failed to connect to RCON server")

    cursor = conn.cursor() #MySQL логин
    if cursor:
        print("Connected to MySQL server")
        #delete table
        cursor.execute('''DROP TABLE IF EXISTS users''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
          (id INTEGER PRIMARY KEY AUTO_INCREMENT, tgid TEXT, minecraftusername TEXT, password TEXT)''')
    else:
        print("Failed to connect to MySQL server")
    
    print("Started") # Финал стартапа
    
    def get_minecraft_log_sftp(): # Получение лога с сервера через SFTP
        with sftp.file("logs/latest.log", 'r') as remote_file:
            log = remote_file.read().decode('utf-8').splitlines()
            return log
            
                
    def command(text):
        return mcrcon.command(sock, text)
# ===================== Логика команд ===============================
    def recievecommand(cmd): 
        if cmd[-9::] == "<--[HERE]": #Если команда отправлена из консоли
            cmd = cmd[:-9:]
            print("Console entered:")
            sender = "Console"
        else: #Если команда отправлена из чата
            cmd = cmd.split("[Not Secure]")[1]
            prefixpos = cmd.find(prefix)
            if prefixpos != -1:
                sender = cmd[:prefixpos:].strip()[1:-1]
                cmd = cmd[prefixpos::]
            
        print(cmd)
        if sender not in cmdbanlist:
            parts = cmd.split()
            cmd = parts[0]
            args = parts[1:]
        else:
            command(f'tellraw {sender} "[{tgbotname}] Вы не можете использовать кастомные команды!"')
            return

        def clearbuffer(): #Очистка после команды
            print("Clearing buffer...")
            print(command("scoreboard players enable @a secret_log"))
            print(command('execute as @a run trigger secret_log'))
            
        match cmd[1:]:
            case "test": #====TEST====
                print("Test command")
                print(command(f'tellraw {sender} "[{tgbotname}] Test message for test custom commands. args: {args}"'))
                clearbuffer()
            case "passlogin": #PASSLOGIN/Проблемы с конфиденциальностью
                if cursor.execute(f"SELECT password FROM users WHERE minecraftusername = '{sender}'").fetchone()[0] == args[0]:
                    command(f'tellraw {sender} "[{tgbotname}] Login {sender}"')
            case "tglogin": #====TGLOGIN====
                command(f'tellraw {sender} "[{tgbotname}] Проверьте телеграм, чтобы подтвердить вход."')
                tgid = cursor.execute(f"SELECT tgid FROM users WHERE minecraftusername = '{sender}'").fetchone()
                if tgid:
                    keypad = telebot.types.InlineKeyboardMarkup()
                    loginbtn = telebot.types.InlineKeyboardButton(text='Подтвердить',callback_data=f"login {sender}")
                    tgprint(tgid[0],f"Подтвердите логин",keypad)
                    clearbuffer()

                    @bot.callback_query_handler(func=lambda call: True)
                    def callback_inline(call):
                        if call.data.startswith("login"):
                            username = call.data.split()[1]
                            command(f'tellraw @a [{{"text":"[{tgbotname}] {username} авторизовался","color":"yellow"}}]')
                            command(f"tellraw {username} [{{'text':'Вход подтвержден, приятной игры!','color':'green'}}]")
                            command(f'tag {username} add authed')
                            clearbuffer()
                clearbuffer()
            case "grandopen": #====GRANDOPEN==== (ADMIN)
                if sender == "mc_roma_c":
                    print("Grand opening!")
                    command('title @a title {"text":"Grand opening!","color":"gold"}')
                    time.sleep(3)
                    command('title @a subtitle {"text":"Welcome!","color":"yellow"}')
                    time.sleep(2)
                    command('worldborder set 1000 10')
                    clearbuffer()
            case "vipmsg": #====VIPMSG==== (VIP)
                if sender in vips:
                    msg = " ".join(args[1:])
                    command(f'tellraw @a ["",{{"text":"<{sender}> ","color":{args[0]}}},{{"text":"{msg}","color":"{args[0]}"}}]')
                    clearbuffer()
            case "vipparticles": #====VIPPARTICLES==== (VIP)
                if sender in vips:
                    command(f'particle {args[0]} ~ ~ ~ 1 1 1 1 100 {sender}')
                else:
                    command(f'tellraw {sender} "[{tgbotname}] Эта команда доступна только при донате (на общую сумму >99р за текущий месяц)!"')
                clearbuffer()
            case "glowme": #====GLOWME==== (VIP)
                if sender in vips:
                    if int(args[0]) <= 60:
                        print(command(f'effect give {sender} minecraft:glowing {args[0]} 1 true'))
                    else:
                        command(f'tellraw {sender} "[{tgbotname}] Время не может быть больше 60 секунд!"')
                        
                else:
                    command(f'tellraw {sender} "[{tgbotname}] Эта команда доступна только при донате (на общую сумму >99р за текущий месяц)!"')
                clearbuffer()
            case "showdb": #====SHOWDB====
                if sender == "mc_roma_c":
                    cursor.execute("SELECT * FROM users")
                    rows = cursor.fetchall()
                    print(command(f'tellraw {sender} "[{tgbotname}] Database data:"'))
                    for row in rows:
                        print(command(f'tellraw {sender} "[{tgbotname}] {row}"'))
                    clearbuffer()
            case "help": #====HELP====
                print(command(f'tellraw {sender} "[{tgbotname}] Help:"'))
                commandslist = "\n".join(customcommands)
                print(command(f'tellraw {sender} "[{tgbotname}] {commandslist}"'))
                clearbuffer()
            case "rcon": #====RCON==== (ADMIN)
                if sender == "mc_roma_c":
                    output = (command(" ".join(args)))
                    if output != "": 
                        command(f'tellraw {sender} "[{tgbotname}] {output}"')
                    clearbuffer()
# ======================== Функции =================================
    def Rconsole(message,keypad): #RCON для тг
        chatid = message.chat.id
        if message.text[0] == "/" and str(chatid) in admins:
            command(message.text)

    def logchecker(): #Кастомные команды
        while True:
            global global_log
            global_log = get_minecraft_log_sftp()
            if global_log:
                effects_time=6
                not_authed_restrictions = [
                    f"effect give @a[tag=!authed] minecraft:blindness {effects_time} 255 true",
                    f"effect give @a[tag=!authed] minecraft:slowness {effects_time} 255 true",
                    f"effect give @a[tag=!authed] minecraft:weakness {effects_time} 255 true",
                    f"effect give @a[tag=!authed] minecraft:mining_fatigue {effects_time} 255 true",
                    "gamemode adventure @a[tag=!authed]"
                ]
                #for cmd in not_authed_restrictions:
                #    command(cmd)#Проверка авторизации
                print(global_log[-1]) #LOG ============================================
                if any(customcommand in global_log[-1] for customcommand in customcommands):
                    recievecommand(global_log[-1].split("]: ")[1])
            else:
                print("Не удалось получить лог.")
            time.sleep(1)

    # Запуск подпроцесса для кастомных команд
    checker_thread = threading.Thread(
        target=logchecker,
        daemon=True # Завершить поток, когда основной поток завершится
    )
    checker_thread.start()

    # ======Привязка аккаунтов (Шаг 2)========
    def connectaccounts(message,username,mainkeyboard):
        chatid = message.chat.id
        if message.text == "Назад":
            tgprint(chatid,"Выбирайте.",mainkeyboard)
            return
        print(f"Connecting {username} to {chatid}")
        cursor.execute(f"INSERT INTO users (tgid, minecraftusername) VALUES ('{chatid}', '{username}')")
        print(command(f'tellraw {username} "[{tgbotname}] Вы успешно связали Minecraft аккаунт {username} с Телеграм аккаунтом {chatid}"'))
        tgprint(chatid,f"Вы успешно связали Телеграм аккаунт {chatid} c Minecraft аккаунтом {username}",mainkeyboard)
    # ======Привязка аккаунтов (Шаг 1)========
    def authwithminecraft(message, mainkeyboard,keypad):
        chatid = message.chat.id
        if message.text == "Назад":
            tgprint(chatid,"Выбирайте.",mainkeyboard)
            return
        username = message.text
        authcode = random.randint(100000,999999)
        command(f'tellraw {username} "[{tgbotname}] Ваш код: {authcode}"')
        tgprint(chatid,"Введите код из игры.",keypad)
        bot.register_next_step_handler(message,connectaccounts,username,mainkeyboard)
    # ======Консоль для тг========
    def consoleupdater(logmsg,chatid):
        while True:
            global global_log
            if global_log:
                newtext = telebot.formatting.mcode("\n".join(global_log[-15::]))
                if 1==1:
                    try:
                        bot.edit_message_text(newtext,chatid,logmsg.message_id ,parse_mode="MarkdownV2")
                    except Exception as e:
                        if str(e) == "Message is not modified: specified new message content is the same as a current content!":
                            pass
            time.sleep(1)
    # tgconsole # bot.edit_message_text(telebot.formatting.mcode("\n".join(log[-15::])),chatid,logmsg.message_id,parse_mode='MarkdownV2')

    #=======================Основной Handler сообщений=======================
    @bot.message_handler(content_types=['text'])
    def get_text_messages(message):
        chatid = message.chat.id #ID чата
        #Создание кнопок для главной клавиатуры
        mainkeyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        mapWebApp = telebot.types.WebAppInfo(url=mapurl)
        mapbtn = telebot.types.KeyboardButton(text='🗺Карта🗺', web_app=mapWebApp)
        clicker = telebot.types.WebAppInfo(url=clickerurl)
        clickerbtn = telebot.types.KeyboardButton(text='🎯Кликер🎯', web_app=clicker)
        startbtn = telebot.types.KeyboardButton(text='/start')
        donatebtn = telebot.types.KeyboardButton(text='💰Донат💰')
        connectbtn = telebot.types.KeyboardButton(text='Связать аккаунты')
        #Создание главной клавиатуры
        mainkeyboard.row(startbtn,donatebtn,clickerbtn)
        secondrow = [connectbtn,mapbtn]
        if str(chatid) in admins:
            consolebtn = telebot.types.KeyboardButton(text='Консоль')
            secondrow.append(consolebtn)
        mainkeyboard.row(*secondrow)
            
        #===/start===
        if message.text == "/start":
            tgprint(chatid,"Выбирайте.",mainkeyboard)
        #====Связать аккаунты====
        elif message.text == 'Связать аккаунты':
            keypad = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            backbtn = telebot.types.KeyboardButton(text='Назад')
            keypad.row(backbtn)
            tgprint(chatid,"Введите ваш ник в игре. Вы должны быть на сервере.",keypad)
            bot.register_next_step_handler(message,authwithminecraft,mainkeyboard,keypad)
        #====Донат====
        elif message.text == "💰Донат💰":
            keypad = telebot.types.InlineKeyboardMarkup()
            donatebtn = telebot.types.InlineKeyboardButton(text='💰Задонатить💰',url="https://tbank.ru/cf/36DOj2lf6XP")
            keypad.row(donatebtn)
            donatead = """
Донат - это способ поддержать проект и получить доступ к привилегиям.

- Вы получите доступ к VIP-командам, если укажете свой ник в сообщении. (При общей сумме донатов 100р и более за текущий месяц)
Список VIP-команд:
•!vipmsg {цвет} {сообщение} - отправить сообщение в чат цветом который вы укажете
•!vipparticles {variant} - Отображать вокруг партиклы (Доступные варианты: heart, fire, smoke, note, enchantment, crit, magic,flame,lava,water, crit_magic)[в разработке]
•!glowme {время в сек. (не более 60)} - Сделать себя светящимся
•Будет добавлено больше команд в будущем

- Вы получите x2 буст в кликере, если укажете свой ник в сообщении. (При общей сумме донатов 50р и более за текущий месяц)

- Поддержка проекта: в сообщении вы можете указать на что пойдет ваш донат. 
Варианты:
•Оплата хостинга сервера
•Апгрейд железа сервера
•Оплата хостинга бота
•Средства на развитие бота
•Средства на развитие кастомных команд
•Средства на развитие кликера (Я за бесплатно его делаю с 0-ля😢)    
•Всё сразу или несколько пунктов сразу
            """
            tgprint(chatid,donatead,keypad)
        #====ТГ Консоль====
        elif message.text == "Консоль" and str(chatid) in admins:
            tgprint(chatid,"Консоль:",mainkeyboard)
            keypad = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
            backbtn = telebot.types.KeyboardButton(text='Назад')
            keypad.row(backbtn)
            logmsg = bot.send_message(chatid,"<Если тут не логи, то произошла ошибка>")
            console_thread = threading.Thread(
                    target=consoleupdater,
                    daemon=True,
                    args=(logmsg,chatid)
                )
            console_thread.start()
            print("Console thread started")
            bot.register_next_step_handler(message,Rconsole,keypad)
        #=====Некорректные команды=====
        else:
            tgprint(chatid,f"Не понял, неправильная команда: {message.text}","") 
            print(f"Введена неправильная команда: {message.text}")
                
    bot.polling(none_stop=True, interval=1) #Бесконечный цикл бота
    
    
finally: # Закрытие всех соединений при выходе
    sock.close() # Close RCON connection
    transport.close() # Close SFTP connection
    conn.close() # Close MySQL connection
    print("Disconnected from RCON and SFTP")




    






