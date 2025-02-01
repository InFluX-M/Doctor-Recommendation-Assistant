from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    ConversationHandler, filters, CallbackContext
)
import requests
import json
import aiohttp

TOKEN = ""
URL = "http://fastapi:8000/"

# Define states for the conversation
SELECT_ACTION, REQUEST_TEXT, REQUEST_VOICE, SELECT_SPECIALTY, SELECT_CITY = range(5)

specialties = [
    "استخوان و مفاصل", "زنان، زایمان و نازایی", "چشم پزشکی", "گوارش و معده", "کلیه و مجاری ادراری",
    "غدد و متابولیسم", "قلب و عروق", "داخلی", "دهان و دندان", "پوست و مو", "جراحی", "اطفال، کودکان و نوزادان",
    "روانپزشکی", "ریه و دستگاه تنفسی", "گوش، حلق و بینی", "پزشک عمومی", "کرونا ویروس", "توانبخشی",
    "بیهوشی و مراقبت های ویژه", "تغذیه", "آزمایشگاه و تصویربرداری", "مغز و اعصاب", "خون، سرطان و آنکولوژی",
    "عفونی", "روانشناسی", "زیبایی", "طب تسکینی و درد", "دیابت", "طب سنتی", "داروسازی", "ژنتیک", "آلرژی",
    "سلامت جنسی", "طب اورژانس"
]

cities = [
    "اراک", "اردبیل", "ارومیه", "اصفهان", "اهواز", "ایلام", 
    "بجنورد", "بندرعباس", "بوشهر", "بیرجند", "تبریز", "تهران", 
    "خرم‌آباد", "رشت", "زاهدان", "زنجان", "ساری", "سمنان", 
    "سنندج", "شهرکرد", "شیراز", "قزوین", "قم", "کرج", 
    "کرمان", "کرمانشاه", "گرگان", "مشهد", "همدان", "یاسوج", "یزد"
]

async def send_req(params, update: Update):
    user_id = update.message.from_user.id
    if "text" in params:
        response = requests.post(f"{URL}requests/text/{user_id}", json={'request': params['text']})
    elif "file" in params:
        response = requests.post(f"{URL}requests/voice/{user_id}", files=params['file'])
    elif "specialty" in params and "city" in params:
        response = requests.get(f"{URL}specialties/{params['specialty']}/{params['city']}")
    elif update.message.text == 'Show':
        response = requests.get(f"{URL}users/{user_id}")
    elif update.message.text == 'Clear':
        response = requests.put(f"{URL}users/{user_id}")
    
    response_text = json.dumps(response.json(), ensure_ascii=False, indent=2)
    await update.message.reply_markdown(f"```\n{response_text}\n```")

async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        ['Request', 'Specialties'],
        ['History']
    ]
    user = update.message.from_user
    await update.message.reply_text(
        f"Hello {user.first_name}! Welcome to the Doctor Recommender System! :)))", 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SELECT_ACTION

async def show_specialties(update: Update, context: CallbackContext) -> int:
    specialty_keyboard = [specialties[i:i+2] for i in range(0, len(specialties), 2)]
    await update.message.reply_text(
        'Please select your specialty:',
        reply_markup=ReplyKeyboardMarkup(specialty_keyboard, resize_keyboard=True)
    )
    return SELECT_SPECIALTY

async def select_city(update: Update, context: CallbackContext) -> int:
    context.user_data['specialty'] = update.message.text
    city_keyboard = [cities[i:i+2] for i in range(0, len(cities), 2)]
    await update.message.reply_text(
        'Please select your city:',
        reply_markup=ReplyKeyboardMarkup(city_keyboard, resize_keyboard=True)
    )
    return SELECT_CITY

async def handle_city_selection(update: Update, context: CallbackContext) -> int:
    specialty = context.user_data['specialty']
    city = update.message.text
    params = {'specialty': specialty, 'city': city}
    await send_req(params, update)
    
    await update.message.reply_text(
        "Your request has been sent. What would you like to do next?",
        reply_markup=ReplyKeyboardMarkup([['Back']], resize_keyboard=True)
    )
    return SELECT_ACTION

async def back_to_main_menu(update: Update, context: CallbackContext) -> int:
    keyboard = [
        ['Request', 'Specialties'],
        ['History']
    ]
    await update.message.reply_text(
        'Back to main menu:',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SELECT_ACTION

async def show_history_menu(update: Update, context: CallbackContext) -> None:
    request_keyboard = [
        ['Show', 'Clear'],
        ['Back']
    ]
    await update.message.reply_text(
        'Please choose how you would like to make your request:',
        reply_markup=ReplyKeyboardMarkup(request_keyboard, resize_keyboard=True)
    )

async def clear_history(update: Update, context: CallbackContext) -> None:
    await send_req({}, update)
    
async def get_history(update: Update, context: CallbackContext) -> None:
    await send_req({}, update)

async def show_request_menu(update: Update, context: CallbackContext) -> int:
    request_keyboard = [
        ['Voice', 'Text'],
        ['Back']
    ]
    await update.message.reply_text(
        'Please choose how you would like to make your request:',
        reply_markup=ReplyKeyboardMarkup(request_keyboard, resize_keyboard=True)
    )
    return SELECT_ACTION

async def handle_text_selection(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        'Please enter the text you would like to send:',
        reply_markup=ReplyKeyboardRemove()
    )
    return REQUEST_TEXT

async def handle_text_input(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    params = {'text': text}
    await send_req(params, update)
    
    await update.message.reply_text(
        "Your text has been sent. What would you like to do next?",
        reply_markup=ReplyKeyboardMarkup([['Back']], resize_keyboard=True)
    )
    return SELECT_ACTION

async def handle_voice_selection(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        'Please send your voice message:'
    )
    return REQUEST_VOICE

async def handle_voice_input(update: Update, context: CallbackContext) -> int:
    voice_file = await update.message.voice.get_file()
    voice_file_path = await voice_file.download_as_bytearray()
    
    files = {
        'file': ('voice.ogg', voice_file_path, 'audio/ogg')
    }
    
    params = {'file': files}
    await send_req(params, update)
    
    await update.message.reply_text(
        "Your voice message has been sent. What would you like to do next?",
        reply_markup=ReplyKeyboardMarkup([['Back']], resize_keyboard=True)
    )
    return SELECT_ACTION


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text(
        'Goodbye!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        SELECT_ACTION: [
            MessageHandler(filters.Regex('^(Request)$'), show_request_menu),
            MessageHandler(filters.Regex('^(Specialties)$'), show_specialties),
            MessageHandler(filters.Regex('^(Back)$'), back_to_main_menu),
            MessageHandler(filters.Regex('^(History)$'), show_history_menu),
            MessageHandler(filters.Regex('^(Show)$'), get_history),
            MessageHandler(filters.Regex('^(Clear)$'), clear_history),
            MessageHandler(filters.Regex('^(Voice)$'), handle_voice_selection),
            MessageHandler(filters.Regex('^(Text)$'), handle_text_selection) 
        ],
        SELECT_SPECIALTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, select_city)
        ],
        SELECT_CITY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_selection)
        ],
        REQUEST_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
        REQUEST_VOICE: [MessageHandler(filters.VOICE, handle_voice_input)]
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

app.add_handler(conv_handler)

app.run_polling()
