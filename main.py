# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import argparse
import requests
import logging
import trafilatura

if __name__ == '__main__':
    # Use a breakpoint in the code line below to debug your script.
    program_description = 'This is a test tool for extracting text from articles'
    parser = argparse.ArgumentParser(description=program_description)

"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(name)s:%(message)s"
    )
    """

    #parser.add_argument('--url')
    #args = parser.parse_args()
    #url = args.url
    url = 'https://apnews.com/article/hurricane-isaias-landfall-gulf-alabama-mississippi-919a46d4bd705726b4e57f18ce677ac5'
    url2 = 'https://www.theguardian.com/world/2026/oct/13/allies-did-not-warn-kyiv-of-russian-ballistic-missile-strikes-says-zelenskyy'
    #download = trafilatura.fetch_response(url, decode=True)
    #print(download)
    download = trafilatura.fetch_url(url2)
    extractedText = trafilatura.extract(download)
    print(extractedText)


