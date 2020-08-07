import config
import feedparser
import logging
import json
import sqlite3
import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup
from telegram.ext import Updater, CommandHandler
from telegram import InputMediaPhoto

rss_dict = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# SQLITE
def sqlite_connect():
    global conn
    conn = sqlite3.connect("rss.db", check_same_thread=False)


def sqlite_load_all():
    sqlite_connect()
    c = conn.cursor()
    c.execute("SELECT * FROM rss")
    rows = c.fetchall()
    conn.close()
    return rows


def sqlite_write(name, link, last):
    sqlite_connect()
    c = conn.cursor()
    q = [(name), (link), (last)]
    c.execute("""INSERT INTO rss('name','link','last') VALUES(?,?,?)""", q)
    conn.commit()
    conn.close()


# RSS________________________________________
def rss_load():
    # if the dict is not empty, empty it.
    if bool(rss_dict):
        rss_dict.clear()

    for row in sqlite_load_all():
        rss_dict[row[0]] = (row[1], row[2])


def check_auth(update):
    return update.message.from_user.id in config.allowed_users


def cmd_rss_list(bot, update):
    if not check_auth(update):
        update.message.reply_text("RSS access denied.")
        return

    if bool(rss_dict) is False:
        update.message.reply_text("The database is empty")
    else:
        for title, url_list in rss_dict.items():
            update.message.reply_text(
                "Title: "
                + title
                + "\nrss url: "
                + url_list[0]
                + "\nlast checked article: "
                + url_list[1]
            )


def cmd_rss_add(bot, update, args):
    if not check_auth(update):
        update.message.reply_text("RSS access denied.")
        return
    # try if there are 2 arguments passed
    try:
        args[1]
    except IndexError:
        update.message.reply_text(
            "ERROR: The format needs to be: /add title http://www.URL.com"
        )
        raise
    # try if the url is a valid RSS feed
    try:
        rss_d = feedparser.parse(args[1])
        rss_d.entries[0]["title"]
    except IndexError:
        update.message.reply_text(
            "ERROR: The link does not seem to be a RSS feed or is not supported"
        )
        raise
    sqlite_write(args[0], args[1], str(rss_d.entries[0]["link"]))
    rss_load()
    update.message.reply_text("added \nTITLE: %s\nRSS: %s" % (args[0], args[1]))


def cmd_rss_remove(bot, update, args):
    if not check_auth(update):
        update.message.reply_text("RSS access denied.")
        return

    conn = sqlite3.connect("rss.db")
    c = conn.cursor()
    q = (args[0],)
    try:
        c.execute("DELETE FROM rss WHERE name = ?", q)
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print("Error %s:" % e.args[0])
    rss_load()
    update.message.reply_text("Removed: " + args[0])


def cmd_help(bot, update):
    if not check_auth(update):
        update.message.reply_text("RSS access denied.")
        return

    update.message.reply_text(
        "RSS to Telegram bot"
        + "\n\nAfter successfully adding a RSS link, the bot starts fetching the feed every "
        + str(config.delay)
        + " seconds. (This can be set) ⏰⏰⏰"
        + "\n\nTitles are used to easily manage RSS feeds and need to contain only one word 📝📝📝"
        + "\n\ncommands:"
        + "\n/help Posts this help message"
        + "\n/add title http://www(.)RSS-URL(.)com"
        + "\n/remove !Title! removes the RSS link"
        "\n/list Lists all the titles and the RSS links from the DB"
        "\n/test Inbuilt command that fetches a post from Reddits RSS."
    )


def translate(text, sourceLang="lv", targetLang="en"):
    g_url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={sourceLang}&tl={targetLang}&dt=t&q={urllib.parse.quote(text)}"

    page = urllib.request.urlopen(g_url)
    if page.getcode() == 200:
        result = json.loads(page.read())
        return result[0][0][0]


def parse_ss(url, min_price, max_price):
    page = urllib.request.urlopen(url)
    if page.getcode() == 200:
        page_html = BeautifulSoup(page.read(), "html.parser")

        # Static elements
        # You can implement your filters here

        try:
            # Price filter
            price = page_html.select(".ads_price")[0].string
            if (config.min_price is not None and config.max_price is not None) and (
                int(re.findall(r"[^ €]*", price)[0]) < config.min_price
                or int(re.findall(r"[^ €]*", price)[0]) > config.max_price
            ):
                return {"filter_ok": False}

            address_street = page_html.find("td", {"id": "tdo_11"}).b.string
            address_region = page_html.find("td", {"id": "tdo_856"}).b.string
            address_city = page_html.find("td", {"id": "tdo_20"}).b.string
            address_gps = re.match(r".*&c=(\d*\.\d*), (\d*\.\d*).*", page_html.find("a", {"id": "mnu_map"})['onclick']).groups()

            sq_meters = page_html.find("td", {"id": "tdo_3"}).string
            rooms = page_html.find("td", {"id": "tdo_1"}).string
            floors = page_html.find("td", {"id": "tdo_4"}).string
            series = page_html.find("td", {"id": "tdo_6"}).string
            building_type = page_html.find("td", {"id": "tdo_2"}).string

            # description = " ".join(
            #     page_html.find("div", {"id": "msg_div_msg"}).findAll(
            #         text=True, recursive=True
            #     )
            # ).strip()

            listing_images = []
            for image in page_html.find_all("img", attrs={"class": "isfoto"}):
                listing_images.append(
                    InputMediaPhoto(
                        media=image["src"].replace(".t.", ".800."), parse_mode="Markdown"
                    )
                )
        except Exception as e:
            print("Error while parsing: ", e)
            return {
                "filter_ok": True,
                "text": url,
                "media": [],
            }

        text_to_send = f"""🌐 {url}
📍 [{address_city}, {address_region}, {address_street}]({"http://maps.google.com/?ll=" + urllib.parse.quote(", ".join(address_gps))}
🏠 {sq_meters}
🧗‍♀️ {floors}
🚪 {rooms}
🏚 {series}
🧱 {building_type}
💵 {price}"""

        listing_images[0].caption = text_to_send

        return {
            "filter_ok": True,
            "text": text_to_send,
            "media": [] + listing_images[:10],
        }
    else:
        # if page didn't load, send just the URL
        return {
            "filter_ok": True,
            "text": text_to_send,
            "media": [],
        }


def rss_monitor(bot, job):
    for name, url_list in rss_dict.items():  # for every RSS feed
        rss_d = feedparser.parse(url_list[0])  # feedparser element
        entry_url = rss_d.entries[0]["link"]
        # if newest RSS entry is not the same as from last check
        if url_list[1] != entry_url:
            # Save latest element to DB
            conn = sqlite3.connect("rss.db")
            q = [(name), (url_list[0]), (str(entry_url))]
            c = conn.cursor()
            c.execute("""INSERT INTO rss('name','link','last') VALUES(?,?,?)""", q)
            conn.commit()
            conn.close()
            rss_load()  # not sure what this does, perhaps updates the variable representation of the SQLite DB?

            # ss.com parser integration
            print("Got new entry: ", entry_url)
            if "ss.com" in entry_url:
                result = parse_ss(entry_url, config.min_price, config.max_price)
                if result["filter_ok"] is False:
                    continue
                elif len(result["media"]) != 0:
                    bot.send_media_group(
                        chat_id=config.chatid, media=result["media"]
                    )
                else:
                    bot.send_message(
                        chat_id=config.chatid,
                        text=result["text"],
                        parse_mode="MarkdownV2",
                    )
            else:
                bot.send_message(chat_id=config.chatid, text=entry_url)


def cmd_test(bot, update, args):
    if not check_auth(update):
        update.message.reply_text("RSS access denied.")
        return

    url = "https://www.reddit.com/r/funny/.rss"
    rss_d = feedparser.parse(url)
    rss_d.entries[0]["link"]
    bot.send_message(chat_id=config.chatid, text=(rss_d.entries[0]["link"]))


def init_sqlite():
    conn = sqlite3.connect("rss.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE rss (name text, link text, last text)""")


def main():
    updater = Updater(token=config.Token)
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

    job_queue.run_repeating(rss_monitor, config.delay)

    updater.start_polling()
    updater.idle()
    conn.close()


if __name__ == "__main__":
    main()
