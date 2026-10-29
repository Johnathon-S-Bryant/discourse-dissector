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
from tavily import TavilyClient
import os
import random

class Statement(BaseModel):
    text: str

class StatementList(BaseModel):
    statements: list[str]

def SearchAndArgue(client, statement, searchPrompt, maxNumTexts, argueTrue):
    searchResults = client.search(searchPrompt)
    urls = []
    texts = ""
    for r in searchResults['results']:
        urls.append(r['url'])

    numTexts = maxNumTexts
    for url in urls:
        downloaded = trafilatura.fetch_url(url)
        extracted = trafilatura.extract(downloaded)
        if extracted is not None:
            texts += extracted + "+++++"

    tf = ""
    if argueTrue:
        tf = "true"
    else:
        tf = "false"

    promptForward = (f"I am going to feed you 1 evaluation statement and {maxNumTexts} texts. Argue that the evaluation statement "
                     f"is {tf} based solely on those {maxNumTexts} texts")
    argument = ollamaClient.chat(
        model=modelName,
        messages=[
            {
                'role': 'user',
                'content': f"{promptForward} | Evaluation statement: {statement} | Texts: {texts}"
            }
        ]
    )
    if argueTrue:
        print("Here is the argument for truth:")
    else:
        print("Here is the argument for falsehood:")
    print(argument.message.content)

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
    #startListToken = '+++++'
    delimiter = '$$$'
    howToFormatOutputSubPrompt = (f"Delimit statements by putting {delimiter} at the end of each individual statement")
    # (f"In your output for this prompt, output '{startListToken}' to show the beginning of statements."
    howToExtractSubPrompt = ("I am going to feed you a news article. Extract from the following text statements that may be true or false, but do not make a"
                             " decision if those statements are true or false:")
    extractedText = trafilatura.extract(download)
    print(extractedText)
    print("++++++++++")
    print("++++++++++")
    modelName="llama3.2:3b"
    ollamaClient = Client(host='http://localhost:11434')
    #client = instructor.from_provider("ollama/llama3.2")
    extractedStatementsText = ollamaClient.chat(
        model=modelName,
        messages=[
            {
                'role': 'user',
                'content': f"{howToFormatOutputSubPrompt} {howToExtractSubPrompt} {extractedText}"
            }
        ]
    )
    statementsText = extractedStatementsText.message.content
    print(statementsText)
    tokens = statementsText.split(delimiter)
    for z in tokens:
        print(z)



    #Grab a statement at random --> for now
    chosenStatement = random.choice(tokens)
    print("Chosen statement:")
    print(chosenStatement)

    numSources = 3
    defenseSearchPrompt = (f"Here is a statement. Find me {numSources} resources defending this statement: {chosenStatement}") #what do we do when there just aren't enough good sources?
    offenseSearchPrompt = (f"Here is a statement. Find me {numSources} resources countering this statement: {chosenStatement}")
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

    #Find and Build offense report
    SearchAndArgue(client, chosenStatement, defenseSearchPrompt, numSources, True)
    #Find and Build defense report
    SearchAndArgue(client, chosenStatement, offenseSearchPrompt, numSources, False)