import telebot
from GoogleNews import GoogleNews
import random
import os

TOKEN = "6200212269:AAEX1RjTuN_XLPTXj-Agxbl-LavYXWjVzPg"
googlenews = GoogleNews(lang='en', region='US', encode='utf-8')

bot = telebot.TeleBot(TOKEN)

def get_user_requests_file(user_id):
    return f"user_requests_{user_id}.txt"

def get_user_confirmations_file(user_id):
    return f"user_confirmations_{user_id}.txt"

def save_to_file(file_path, data):
    with open(file_path, "w") as file:
        file.write(data)

def read_from_file(file_path):
    try:
        with open(file_path, "r") as file:
            return file.read()
    except FileNotFoundError:
        return ""

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add('Add Request', 'Get News', 'Cancel')
    bot.reply_to(message, 'Welcome to the News Bot! I can send you the latest news according to your request. To get started, type /news or press the "Add Request" button.', reply_markup=markup)

@bot.message_handler(commands=['news'])
def news(message):
    bot.reply_to(message, 'Please enter your query for the news you want to get.')

@bot.message_handler(commands=['getnews'])
def get_news(message):
    user_id = message.chat.id
    requests_file = get_user_requests_file(user_id)
    if os.path.exists(requests_file):
        query_list = read_from_file(requests_file).split(',')
        query_list = [q.strip() for q in query_list if q.strip()]  # Remove empty queries
        random.shuffle(query_list)
        if query_list:
            for query in query_list:
                try:
                    googlenews.clear()
                    googlenews.get_news(query)
                    news_results = googlenews.results()[:5]
                    if news_results:
                        bot.send_message(user_id, f'Here are the latest news for "{query}":')
                        for article in news_results:
                            title = article['title']
                            media = article['media']
                            date = article['date']
                            link = article['link']
                            message_text = f"[{title}]({link}) ({media})\n{date}"
                            bot.send_message(user_id, message_text, parse_mode='Markdown')
                    else:
                        bot.reply_to(message, f'Sorry, I could not find any news for "{query}". Please try another query.')
                except Exception as e:
                    bot.reply_to(message, f'Sorry, something went wrong. Please try again later. Error: {e}')
        else:
            bot.reply_to(message, 'You have not added any valid requests yet. To add a request, type /news.')
    else:
        bot.reply_to(message, 'You have not added a request yet. To add a request, type /news.')

@bot.message_handler(func=lambda message: message.text.lower() == 'add request')
def add_request(message):
    news(message)

@bot.message_handler(func=lambda message: message.text.lower() == 'get news')
def get_news_request(message):
    get_news(message)

@bot.message_handler(func=lambda message: message.text.lower() == 'cancel')
def cancel_request(message):
    user_id = message.chat.id
    if os.path.exists(get_user_requests_file(user_id)):
        with open(get_user_requests_file(user_id), "r") as file:
            query_list = file.read().split(',')
        if query_list:
            bot.reply_to(message, f'You have the following queries:\n{", ".join(query_list)}\nIf you want to remove a specific query, please type it. For example, "Bitcoin".')
        else:
            bot.reply_to(message, 'You have no queries to cancel.')
    else:
        bot.reply_to(message, 'You have no queries to cancel.')

@bot.message_handler(func=lambda message: message.text.lower() not in ['add request', 'get news', 'cancel'])
def handle_text_input(message):
    user_id = message.chat.id
    text = message.text.strip()

    if os.path.exists(get_user_confirmations_file(user_id)):
        confirmation = read_from_file(get_user_confirmations_file(user_id))
        if text.lower() == 'yes':
            query_to_delete = confirmation
            requests_file = get_user_requests_file(user_id)
            if os.path.exists(requests_file):
                query_list = read_from_file(requests_file).split(',')
                if query_to_delete in query_list:
                    query_list.remove(query_to_delete)
                    save_to_file(requests_file, ','.join(query_list))
                    bot.reply_to(message, f'Your query "{query_to_delete}" has been deleted. To get news on your remaining queries, click "Get News".')
                else:
                    bot.reply_to(message, f'The query "{query_to_delete}" does not exist in your requests.')
            else:
                bot.reply_to(message, 'You have no queries to delete.')
        elif text.lower() == 'no':
            bot.reply_to(message, f'Your query "{confirmation}" has not been deleted. To get news on your queries, click "Get News".')
        else:
            bot.reply_to(message, f'Please answer "yes" or "no". Do you want to delete the query "{confirmation}"?')
        os.remove(get_user_confirmations_file(user_id))
    else:
        requests_file = get_user_requests_file(user_id)
        if os.path.exists(requests_file):
            query_list = read_from_file(requests_file).split(',')
            if text in query_list:
                save_to_file(get_user_confirmations_file(user_id), text)
                bot.reply_to(message, f'Do you want to delete the query "{text}"? Please answer "yes" or "no".')
            else:
                query_list.append(text)
                save_to_file(requests_file, ','.join(query_list))
                bot.reply_to(message, f'Your request "{text}" has been added. To get news on this topic, click "Get News".')
        else:
            save_to_file(requests_file, text)
            bot.reply_to(message, f'Your request "{text}" has been added. To get news on this topic, click "Get News".')

bot.polling()