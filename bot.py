from telebot import types
import telebot
client = telebot.TeleBot('6160645296:AAEEJTLc1pHFftcMm0qf1ZFeC4B4_BdqgMc')
client.infinity_polling(timeout=10, long_polling_timeout=5)