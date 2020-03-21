from bottle import route, request, response, run, template, Bottle, static_file, HTTPError
import requests
from bs4 import BeautifulSoup as bs
import jsonfeed as jf
# import datetime from datetime as dt

from datetime import datetime as dt, timedelta

BASE_URL = "https://www.itsnicethat.com"

ERROR_MESSAGES = {
    404: "This page could not be resolved."
}

# Tries to match e.g. '10 hours ago'; otherwise defaults to now.
def marshalItsNiceThatHoursAgo(string_date):
    date_published = dt.utcnow()
    try:
        hours_ago = int(string_date.split()[0])
        date_published -= timedelta(hours=hours_ago)
    except ValueError:
        print("Defauling to NOW:", string_date)
        pass
    # Messy: just make it UTC by adding the Zulu indicator.
    return date_published.isoformat() + "Z"

# Tries to match e.g. '16 October 2019'; otherwise defers to
# marshalItsNiceThatHoursAgo.
def marshalItsNiceThatDate(string_date):
    try:
        # Messy: just make it UTC by adding the Zulu indicator.
        return dt.strptime(string_date, "%d %B %Y").isoformat() + "Z"
    except ValueError:
        return marshalItsNiceThatHoursAgo(string_date)

def toItem(listing):
    # Images are lazy-loaded with JS on their site.
    # image_src = listing.find("img")["src"]
    url = listing.find('a')['href']
    title = listing.find(class_="listing-item-title").text
    raw_tags = listing.findAll(class_="tag")
    # Ignore the "more tags" ellipsis.
    tags = [tag.text for tag in raw_tags if tag.text != '...']
    date_published = marshalItsNiceThatDate(
        listing.find(class_="first-cap").text
    )
    return jf.Item(
        id=url,
        url=BASE_URL+url,
        title=title,
        tags=tags,
        content_html=listing.prettify(),
        date_published=date_published
    )

def getRecentItems(category=""):
    specific_url = BASE_URL + "/" + category
    page = requests.get(specific_url)
    soup = bs(page.text, 'html.parser')
    if not page.ok:
        raise HTTPError(
            status=page.status_code,
            body=ERROR_MESSAGES.get(page.status_code)
        )
    listings = soup.findAll(class_="listing-item")
    recent_listings = listings[:20]
    # Render the output feed.
    res = jf.Feed(
        title="It's Nice That" if len(category) == 0 else "It's Nice That: %s" % category,
        home_page_url=specific_url,
        feed_url="https://itsnicethat-feed-dot-arxiv-feeds.appspot.com",
        items=[toItem(l) for l in recent_listings]
    )
    response.content_type = 'application/json'
    return res.toJSON()

app = Bottle()

@app.route('/favicon.ico')
def favicon():
    return static_file('favicon.ico', root='./static', mimetype='image/x-icon')

# Serve index.
@app.route('/')
def entry():
    return getRecentItems()

# Serve Atlas of Places categories. Supported categories at this time:
#   academia, architecture, cartography, cinema, essays, painting, photography,
#   research
@app.route('/<category>')
def subset(category):
    return getRecentItems(category=category)
