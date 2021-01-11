#!/usr/bin/env python3
#
# Download all images from a LINE Webtoon comic 
#

import sys
import argparse
import os
from bs4 import BeautifulSoup
from urllib import request
from urllib.request import Request, urlopen
import shutil
import re
import glob
import dominate
from dominate.tags import *


lastNum = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')

img_referer = 'http://www.webtoons.com'
FILENAME = sys.argv[0]

next_page = ""
chapter_heading = ""

"""Argparse override to print usage to stderr on argument error."""
class ArgumentParserUsage(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help(sys.stderr)
        sys.exit(2)

"""Print usage and exit depending on given exit code."""
def usage(exit_code):
    if exit_code == 0:
        pipe = sys.stdout
    else:
        # if argument was non-zero, print to STDERR instead
        pipe = sys.stderr

    parser.print_help(pipe)
    sys.exit(exit_code)

"""Log a message to a specific pipe (defaulting to stdout)."""
def log_message(message, pipe=sys.stdout):
    print("{}: {}".format(FILENAME, message), file=pipe)

"""If verbose, log an event."""
def log(message):
    if not args.verbose:
        return
    log_message(message)

"""Log an error. If given a 2nd argument, exit using that error code."""
def error(message, exit_code=None):
    log_message("error: " + message, sys.stderr)
    if exit_code:
        sys.exit(exit_code)

parser = ArgumentParserUsage(description="Download all images from a LINE Webtoon comic episode.")
parser.add_argument("-v", "--verbose", action="store_true", help="be verbose")
parser.add_argument("-d", "--dir", default=".",
                    help="directory to store downloaded images in (default: .)")
parser.add_argument("url", metavar="URL", help="Webtoon comic URL")
args = parser.parse_args()


# force verbosity for now
args.verbose = True




def get_image_urls(page):
    """Retrieve all image URLs to download."""
    img_dl_urls = []

    log("Downloading page {}".format(page))
    req = urlopen(Request(page, headers={'User-Agent': 'Mozilla/5.0'})).read()
    soup = BeautifulSoup(req, "lxml")
    imgs = soup.find_all("img", {"id": re.compile("(image)")})
    for img in imgs:
        # get image URL, remove the lower quality bit GET
        img_url = img["data-src"]
        img_dl_urls.append(img_url)
    return img_dl_urls

def get_next_page(page):

    req = urlopen(Request(page, headers={'User-Agent': 'Mozilla/5.0'})).read()
    soup = BeautifulSoup(req, "lxml")
    try:
        next_page = soup.find("a", {"class": "next_page"})["href"]
    except:
        next_page = ""
        
    return next_page

def get_chapter_heading(page):
    req = urlopen(Request(page, headers={'User-Agent': 'Mozilla/5.0'})).read()
    soup = BeautifulSoup(req, "lxml")
    try:
        chapter_heading = soup.find("h1", {"id": "chapter-heading"}).contents[0].strip()
    except:
        chapter_heading = ""
        
    return chapter_heading.replace('?','').replace('/','').replace('\\','').replace('|','').replace('\"','').replace(':','').replace('<','').replace('>','').replace('<','')

def download_images(urls, outdir, chapter_heading):
    """Download each image in urls to existing directory outdir."""
    referer_header = { "Referer": img_referer }
    count = 0
    image_urls = []
    for url in urls:
        count += 1
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        os.makedirs(os.path.dirname("{}/{}/".format(outdir, chapter_heading)), exist_ok=True)
        with request.urlopen(req) as response, open("{}/{}/{:03}.jpg".format(outdir, chapter_heading, count), "wb") as outfile:
            shutil.copyfileobj(response, outfile)

        image_urls.append("{}/{:03}.jpg".format(chapter_heading, count))
    return image_urls

def increment(s):
    """ look for the last sequence of number(s) in a string and increment """
    m = lastNum.search(s)
    if m:
        next = str(int(m.group(1))+1)
        start, end = m.span(1)
        s = s[:max(end-len(next), start)] + next + s[end:]
    return s

def create_page(chapter_heading, images):
    
    doc = dominate.document(title=chapter_heading)

    with doc.head:
        link(rel='stylesheet', href='../main.css')
        script(type='text/javascript', src='script.js')
    
    with doc.body:
        h1(chapter_heading)
        with button():
            a("next", href='%s.html' % increment(chapter_heading))
        with div():
            attr(cls='body')
            for path in images:
                img(src=path)

    with open(args.dir + "/" + chapter_heading + ".html", 'w') as f:
        f.write(doc.render())


if os.path.exists(args.dir):
    if not os.path.isdir(args.dir):
        error("not a directory: {}".format(args.dir), 1)
else:
    os.makedirs(args.dir, exist_ok=True)


img_urls = get_image_urls(args.url)
chapter_heading = get_chapter_heading(args.url)
images = download_images(img_urls, args.dir, chapter_heading)
next_page = get_next_page(args.url)
create_page(chapter_heading, images)

while next_page != "":
    img_urls = get_image_urls(next_page)
    chapter_heading = get_chapter_heading(next_page)
    images = download_images(img_urls, args.dir, chapter_heading)
    next_page = get_next_page(next_page)
    create_page(chapter_heading, images)
    log(next_page)
    
