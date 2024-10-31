

# RSS to Telegram bot
A self-hosted telegram python bot that dumps posts from RSS feeds to a telegram chat. This fork adds support for parsing ss.com advert pages.

## Quick setup for ss.com apartment feed:
1. Install Python 3 from python.org
2. Click green Code button → Download ZIP
3. Message @BotFather and get a token for a new bot
4. Message @get_id_bot to get your chat ID
5. In extracted zip, rename config.py.dist to config.py
6. Replace placeholders in config.py including bot token, chat ID and allowed users
7. Open cmd.exe and run:

```shell
cd ~/path/to/RSS-to-Telegram-Bot
pip install feedparser urllib3 bs4 python-telegram-bot
python3 "telegramRSSbot - gpu.py"
```

8. Go to ss.com and copy the "RSS" link at the bottom of the page for the category you want
9. Message the bot /add title http://example.com/rss.feed

### Docker
**Docker image is unchanged from the original!**

For the docker image go to: https://hub.docker.com/r/bokker/rss.to.telegram/

### Installation
Python 3.X
```sh 
pip install feedparser
pip install python-telegram-bot
```

A telegram bot is needed that the script will connect to. https://botsfortelegram.com/project/the-bot-father/
The chatid is required for the bot to know where to post the RSS feeds. https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id

1. Clone the script
2. Replace your chatID and Token on the top of the script.
3. Edit the delay. (seconds)
4. Save and run
5. Use the telegram commands to manage feeds 

# Usage
send /help to the bot to get this message: 

>RSS to Telegram bot

>After successfully adding a RSS link, the bot starts fetching the feed every 60 seconds. (This can be set) ⏰⏰⏰
>Titles are used to easily manage RSS feeds and need to contain only one word 📝📝📝

>commands:

>**/add** title http://www(.)URL(.)com

>**/help** Shows this text 

>**/remove** !Title! removes the RSS link

>**/list** Lists all the titles and the RSS links from the DB

>**/test** Inbuilt command that fetches a post from Reddits RSS.


# Known issues
 If the bot is set to for example 5 minutes and one feed manages to get 2 new posts before the bot can check. Only the newest post will show up on telegram.
