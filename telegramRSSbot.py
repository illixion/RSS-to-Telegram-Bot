import feedparser
import logging
import sqlite3
import urllib.request
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler
from telegram import InputMediaPhoto

Token = ""
chatid = ""
delay = 60

rss_dict = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

# SQLITE
def sqlite_connect():
    global conn
    conn = sqlite3.connect('rss.db', check_same_thread=False)


def sqlite_load_all():
    sqlite_connect()
    c = conn.cursor()
    c.execute('SELECT * FROM rss')
    rows = c.fetchall()
    conn.close()
    return rows


def sqlite_write(name, link, last):
    sqlite_connect()
    c = conn.cursor()
    q = [(name), (link), (last)]
    c.execute('''INSERT INTO rss('name','link','last') VALUES(?,?,?)''', q)
    conn.commit()
    conn.close()


# RSS________________________________________
def rss_load():
    # if the dict is not empty, empty it.
    if bool(rss_dict):
        rss_dict.clear()

    for row in sqlite_load_all():
        rss_dict[row[0]] = (row[1], row[2])


def cmd_rss_list(bot, update):
    if bool(rss_dict) is False:
        update.message.reply_text("The database is empty")
    else:
        for title, url_list in rss_dict.items():
            update.message.reply_text(
                "Title: " + title +
                "\nrss url: " + url_list[0] +
                "\nlast checked article: " + url_list[1])


def cmd_rss_add(bot, update, args):
    # try if there are 2 arguments passed
    try:
        args[1]
    except IndexError:
        update.message.reply_text(
            "ERROR: The format needs to be: /add title http://www.URL.com")
        raise
    # try if the url is a valid RSS feed
    try:
        rss_d = feedparser.parse(args[1])
        rss_d.entries[0]['title']
    except IndexError:
        update.message.reply_text(
            "ERROR: The link does not seem to be a RSS feed or is not supported")
        raise
    sqlite_write(args[0], args[1], str(rss_d.entries[0]['link']))
    rss_load()
    update.message.reply_text(
        "added \nTITLE: %s\nRSS: %s" % (args[0], args[1]))


def cmd_rss_remove(bot, update, args):
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    q = (args[0],)
    try:
        c.execute("DELETE FROM rss WHERE name = ?", q)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print('Error %s:' % e.args[0])
    rss_load()
    update.message.reply_text("Removed: " + args[0])


def cmd_help(bot, update):
    update.message.reply_text(
        "RSS to Telegram bot" +
        "\n\nAfter successfully adding a RSS link, the bot starts fetching the feed every "
         + str(delay) + " seconds. (This can be set) ⏰⏰⏰" +
        "\n\nTitles are used to easily manage RSS feeds and need to contain only one word 📝📝📝" +
        "\n\ncommands:" +
        "\n/help Posts this help message" +
        "\n/add title http://www(.)RSS-URL(.)com" +
        "\n/remove !Title! removes the RSS link"
        "\n/list Lists all the titles and the RSS links from the DB"
        "\n/test Inbuilt command that fetches a post from Reddits RSS.")


def rss_monitor(bot, job):
    for name, url_list in rss_dict.items():  # for every RSS feed
        rss_d = feedparser.parse(url_list[0])  # feedparser element
        entry_url = rss_d.entries[0]['link']
        if (url_list[1] != entry_url):  # if newest RSS entry is not the same as from last check
            # Save latest element to DB
            conn = sqlite3.connect('rss.db')
            q = [(name), (url_list[0]), (str(entry_url))]
            c = conn.cursor()
            c.execute('''INSERT INTO rss('name','link','last') VALUES(?,?,?)''', q)
            conn.commit()
            conn.close()
            rss_load()  # not sure what this does, perhaps updates the variable representation of the SQLite DB?

            # ss.com parser integration
            if "ss.com" in entry_url:
                page = urllib.request.urlopen(entry_url)
                if page.getcode() == 200:
                    page_html = BeautifulSoup(page.read(), 'html.parser')

                    # Static elements
                    # You can implement your filters here
                    price = page_html.select(".ads_price")[0].string
                    address = page_html.find("td", {"id": "tdo_11"}).b.string + ': ' + page_html.find("td", {"id": "tdo_856"}).b.string
                    sq_meters = page_html.find("td", {"id": "tdo_3"}).string
                    listing_images = []
                    for image in page_html.find_all("img", attrs={"class": "isfoto"}):
                        listing_images.append(InputMediaPhoto(media=image["src"].replace(".t.", ".800.")))

                    text_to_send = f"""🌐 {entry_url}
📍 {address}
🏠 {sq_meters}
💵 {price}"""
                    listing_images[0].caption = text_to_send

                    bot.send_media_group(chat_id=chatid, media=listing_images[:10])
                else:
                    # if page didn't load, send just the URL
                    bot.send_message(chat_id=chatid, text=entry_url)
                # bot.send_message(chat_id=chatid, text=entry_url)
            # if not an ss.com URL, skip parsing
            else:
                bot.send_message(chat_id=chatid, text=entry_url)


def cmd_test(bot, update, args):
    url = "https://www.reddit.com/r/funny/.rss"
    rss_d = feedparser.parse(url)
    rss_d.entries[0]['link']
    bot.send_message(chat_id=chatid, text=(rss_d.entries[0]['link']))


def init_sqlite():
    conn = sqlite3.connect('rss.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE rss (name text, link text, last text)''')


def main():
    updater = Updater(token=Token)
    job_queue = updater.job_queue
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("add", cmd_rss_add, pass_args=True))
    dp.add_handler(CommandHandler("help", cmd_help))
    dp.add_handler(CommandHandler("test", cmd_test, pass_args=True))
    dp.add_handler(CommandHandler("list", cmd_rss_list))
    dp.add_handler(CommandHandler("remove", cmd_rss_remove, pass_args=True))

    # try to create a database if missing
    try:
        init_sqlite()
    except sqlite3.OperationalError:
        pass
    rss_load()

    job_queue.run_repeating(rss_monitor, delay)

    updater.start_polling()
    updater.idle()
    conn.close()


if __name__ == '__main__':
    main()
