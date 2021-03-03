import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import datetime

TITLESTRING = ["[H]", "[HAVE]", "(H)", "HAVE", "WTB", "WTS"]
#These are the words you are looking for in the titles.
MAXPOSTS = 30
#This is how many posts you want to retrieve all at once. PRAW can download 100 at a time.
WAIT = 20
#This is how many seconds you will wait between cycles. The bot is completely inactive during this time.

COMMENT_TEMPLATE = """
**It's dangerous to go alone! Take this.**

[Avoiding Scams] (https://www.reddit.com/r/GameSale/wiki/avoidscams) | [Universal Scammer List](https://universalscammerlist.com/search.php)

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

r = praw.Reddit(client_id='',
                     client_secret='',
                     password='',
                     user_agent='History info for /r/gameswap and /r/GameSale V.1.02 Creator - Lambawamba',
                     username='')

subreddit = r.subreddit('')

def scanSub():
    print('Searching...')
    posts = subreddit.new(limit=MAXPOSTS)
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
                    comment = COMMENT_TEMPLATE % (("/u/"+ author.name), author_created, years, author.link_karma, author.comment_karma)
                    post.reply(comment).mod.distinguish(sticky=True)
            sql.commit()


while True:
    try:
        scanSub()
    except Exception as e:
        traceback.print_exc()
    print('Running again in ' + WAITS + ' seconds \n')
    sql.commit()
    time.sleep(WAIT)
