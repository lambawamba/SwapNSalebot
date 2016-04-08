import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime


USERNAME  = ""
#This is the bot's Username. In order to send mail, he must have some amount of Karma.
PASSWORD  = ""
#This is the bot's Password. 
USERAGENT = "/u/(USERNAME GOES HERE) - History bot for /r/gameswap and /r/GameSale V.1. Creator - Lambawamba"
#This is a short description of what the bot does. For example "/u/GoldenSights' Newsletter bot"
SUBREDDIT = "gameswap+GameSale"
#This is the sub or list of subs to scan for new posts. For a single sub, use "sub1". For multiple subreddits, use "sub1+sub2+sub3+..."
TITLESTRING = ["[H]", "[HAVE]", "(H)", "HAVE", "WTB", "WTS"]
#These are the words you are looking for in the titles.
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

COMMENT_TEMPLATE = """ 
Username | Join date | Link karma | Comment karma
:- | :-: | -: | -:
%s | %s / %s  | %d | %d

^^This ^^information ^^does ^^not ^^guarantee ^^a ^^successful ^^swap. ^^Creator ^^- ^^lambawamba
"""


WAITS = str(WAIT)

sql = sqlite3.connect('sql.db')
print('Loaded SQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
print('Loaded Completed table')

sql.commit()

print("Logging in")
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
    print('Searching '+ SUBREDDIT + '.')
    subreddit = r.get_subreddit(SUBREDDIT)
    posts = subreddit.get_new(limit=MAXPOSTS)
    for post in posts:
        pid = post.id
        cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
        if not cur.fetchone():
            cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
            pbody = "%s %s" % (post.selftext.lower(), post.title.lower())
            if any(key.lower() in pbody for key in TITLESTRING):
                author = post.author
                if author:
                    seconds_year = 60 * 60 * 24 * 365
                    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
                    difference = now - author.created_utc
                    years = difference // seconds_year
                    if years == 0:
                        years = "<1 year"
                    elif years == 1:
                        years = "1 year"
                    else:
                        years = "%d years" % years
                    author_created = datetime.datetime.utcfromtimestamp(author.created_utc)
                    author_created = datetime.datetime.strftime(author_created, "%d %B %Y")
                    # %d %B %Y = "06 February 2015"
                    print("Commenting user history")
                    comment = COMMENT_TEMPLATE % (author.name, author_created, years, author.link_karma, author.comment_karma)
                    post.add_comment(comment).distinguish()
            sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
