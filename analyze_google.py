# Credentials
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''


from bs4 import BeautifulSoup
# from urllib.request import urlopen
import requests
import csv

# Imports the Google Cloud client library
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

import numpy as np
import matplotlib.pyplot as plt

# This is needed because Google protects the source code of their html, giving a 403: forbidden.
# In order to bypass this protection, the below makes Google think a human is accessing this data, not a computer
    # This step adapted from http://edmundmartin.com/scraping-google-with-python/

USER_AGENT = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'}

def fetch_results(search_term, number_results, option):
    # ensures proper arguments
    assert isinstance(search_term, str), 'Search term must be a string'
    assert isinstance(number_results, int), 'Number of results must be an integer'
    assert isinstance(option, int), 'Option must be 1 or 2'
    # replaces the spaces in the search term with a + for the url
    escaped_search_term = search_term.replace(' ', '+')
    google_url = ''
    if option == 1:
        google_url = 'https://www.google.com/search?q={}&num={}&tbm=nws&hl=en'.format(escaped_search_term, number_results)
    elif option == 2:
        google_url = 'https://www.google.com/search?q={}&num={}&hl=en'.format(escaped_search_term, number_results)
    response = requests.get(google_url, headers=USER_AGENT)
    # checks if request is successful
    response.raise_for_status()

    return response.text

def parse_results(html, option):
    soup = BeautifulSoup(html, "html.parser")

    found_results = []
    if option == 1:
        results = soup.find_all('div', attrs={'class': 'gG0TJc'})
    elif option == 2:
        results = soup.find_all('div', attrs={'class': 'g'})
    for result in results:
        #normal search or news?
        if option == 1:
            title = result.find("h3", attrs={'class': 'r dO0Ag'})
            description = result.find('div', attrs={'class': 'st'})
        elif option == 2:
            title = result.find("h3", attrs={'class': 'LC20lb' or 'r'})
            description = result.find('span', attrs={'class': 'st'})
        if title and description:
            title = title.get_text()
            description = description.get_text()
            found_results.append({'title': title, 'description': description})
            # replaces the spaces in the search term with a - for the file
            file_search_term = search_term.replace(' ', '-')
            # create filename with variable search and number of result
            filename = "{}{}.csv".format(file_search_term, number_results)
            # create and write into csv file (looked at my implementation of Pset 7)
            file = open(filename, "a")
            writer = csv.writer(file)
            writer.writerow((title, description))
            file.close()

    return found_results, filename

#Analyze sentiment with Google Cloud Language API
def analyze(text):
    """Run a sentiment analysis request on text within a passed filename."""
    client = language.LanguageServiceClient()
    score_list = []
    # for each line, append the sentiment score and magnitude to the list
    with open(text) as review:
        for cnt, line in enumerate(review):
            document = types.Document(
                content=line,
                type=enums.Document.Type.PLAIN_TEXT)
            annotations = client.analyze_sentiment(document=document)
            score = annotations.document_sentiment.score
            score_list.append(annotations.document_sentiment.score)
            magnitude = annotations.document_sentiment.magnitude


            print('Result {}: score of {} with magnitude of {}'.format(cnt + 1,
                score, magnitude))
        return score_list


if __name__ == '__main__':
    search_term = input("Search Term: ")
    number_results = int(input("Number of Results: "))
    option = int(input("'News'[1] or 'Search'[2], Enter Option number: "))
    html = fetch_results(f'{search_term}', number_results, option)
    search_results, file_name = parse_results(html, option)
    print(f"\n", end="")
    for x in search_results:
        print(x['title'])
        print(x['description'])
        print("\n", end="")

    score_a = analyze(file_name)
    print(f"\n", end="")
    # data to plot
    n_groups = number_results
    count = []
    number = 1
    for i in score_a:
        count.append(number)
        number += 1

    # Create plot with MatPlotLib
    fig, ax = plt.subplots()
    index = np.arange(n_groups)
    bar_width = 0.35
    opacity = 0.8

    rects1 = plt.bar(index, score_a, bar_width,
                     alpha=opacity,
                     color='m',
                     label='sentiment')

    if min(score_a) < 0:
        plt.axhspan(-1.00, 0, facecolor='0.2', alpha=0.15)
    plt.xlabel('Result')
    plt.ylabel('Scores')
    plt.ylim([-1.00, 1.00])
    plt.title('Sentiment Scores')
    plt.xticks(index, count)
    plt.legend()

    plt.tight_layout()
    # replaces the spaces in the search term with a - for the file
    file_search_term = search_term.replace(' ', '-')
    graphfile = "{}{}.png".format(file_search_term, number_results)
    plt.savefig(graphfile)
    print(f"Check out your graph in file: {graphfile}")
    print(f"File name for your results: {file_name}")
    print(f"\n", end="")
    compare = input("Would you like to compare these results with another result file? [yes/no]: ")
    if compare == 'yes':
        print(f"\n", end="")
        file2 = input("What is the name of the second file? (note that files must have the same number of results): ")
        score_b = analyze(file2)
        print(f"\n", end="")
        if len(score_b) == len(score_a):
            rects1 = plt.bar(index, score_a, bar_width,
                         alpha=opacity,
                         color='b',
                         label='File1')

            rects2 = plt.bar(index + bar_width, score_b, bar_width,
                         alpha=opacity,
                         color='g',
                         label='File2')
            plt.xlabel('Result')
            plt.ylabel('Scores')
            plt.title('Sentiment Scores')
            plt.xticks(index + bar_width, count)
            plt.legend()

            plt.tight_layout()
            plt.savefig(graphfile)
            print(f"Check out your graph in file: compare.png")
            plt.savefig('compare.png')
        else:
            print("Files must have the same number of results to compare")
