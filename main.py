# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


import argparse
import requests
import logging
import trafilatura
from pydantic import BaseModel
import instructor
from ollama import Client

class Statement(BaseModel):
    text: str

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
    #url = 'https://apnews.com/article/hurricane-isaias-landfall-gulf-alabama-mississippi-919a46d4bd705726b4e57f18ce677ac5'
    url2 = 'https://www.theguardian.com/world/2026/oct/13/allies-did-not-warn-kyiv-of-russian-ballistic-missile-strikes-says-zelenskyy'
    #download = trafilatura.fetch_response(url, decode=True)
    #print(download)
    download = trafilatura.fetch_url(url2)
    howToExtractSubPrompt = ("I am going to feed you a news article. Extract from the following text statements that may be true or false, but do not make a"
                             " decision if those statements are true or false:")
    extractedText = trafilatura.extract(download)
    print(extractedText)
    print("++++++++++")
    print("++++++++++")
    ollamaClient = Client(host='http://localhost:11434')
    #client = instructor.from_provider("ollama/llama3.2")
    extractedStatementsText = ollamaClient.chat(
        model="llama3.2:3b",
        messages=[
            {
                'role': 'user',
                'content': f"{howToExtractSubPrompt} {extractedText}"
            }
        ]
    )
    statementsText = extractedStatementsText.message.content
    print(statementsText)

    """
    sourceSearchSubPrompt = ('Here are a bunch of statements that are either true or false.'
                             'Find me some sources to help me prove them true or false:')

    sourceSearchClient = Client(host='https://ollama.com')
    sourceSearchMessages = [
        {
            'role': 'user',
            'content': f'{sourceSearchSubPrompt} {statementsText}'
        }
    ]
    """
