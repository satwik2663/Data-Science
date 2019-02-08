# -*- coding: utf-8 -*-
"""webscrapingJPMorgan.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/132KT569j1FNFFBhTXXBMfq1AbSz8E4wq
"""

import pandas as pd
from pandas import ExcelWriter
from bs4 import BeautifulSoup
import requests
import xlrd


def parseCareerPages():
    parsedpages = []
    for i in range(1,265):
        url = 'https://jobs.jpmorganchase.com/ListJobs/All/sortdesc-jobtitle/Page-' + str(i)
        req = requests.get(url)
        parser = BeautifulSoup(req.content, 'html.parser')
        parsedpages.append(parser)
    return parsedpages


def createJPMorganUSTotalJobList(parsedpages):
    job_ids_urls_titles = [['Job ID', 'Job URL', 'Job Title', 'Country', 'State', 'City', 'Date Posted']]
    for parsedpage in parsedpages:
        # regex = r'(\w+) '
        parsedjobtitles = parsedpage.select(".coloriginaljobtitle")
        parsedjobids = parsedpage.select(".coldisplayjobid")
        parsedjobcountries = parsedpage.select(".colcountry")
        parsedjobstates = parsedpage.select(".colstate")
        parsedjobcities = parsedpage.select(".colcity")
        parsedjobposted = parsedpage.select(".colpostedon")
        jobids = []
        for each in parsedjobids:
            jobids.append(each.select('a')[0].text)
        # print(jobids)
        job_urls = ["Job URL"]
        for each in parsedjobtitles:
            joburl = []
            for a in each.find_all('a', href=True):
                joburl.append(a['href'])
            job_urls.append("https://jobs.jpmorganchase.com" + joburl[0])
        job_titles = ["Job Title"]
        for each in parsedjobtitles:
            job_titles.append(each.select("a")[0].text)
        jobcountries = []
        for each in parsedjobcountries:
            jobcountries.append(each.text)
        jobstates = []
        for each in parsedjobstates:
            jobstates.append(each.text)
        jobcities = []
        for each in parsedjobcities:
            jobcities.append(each.text)
        jobpostedon = []
        for each in parsedjobposted:
            jobpostedon.append(each.text)
        for i in range(len(job_urls)):
            job_ids_urls_titles.append(
                [jobids[i], job_urls[i], job_titles[i], jobcountries[i], jobstates[i], jobcities[i], jobpostedon[i]])
    return job_ids_urls_titles

def parseJobUrlCategoryAndDescription(url):
    req = requests.get(url)
    parser = BeautifulSoup(req.content, 'html.parser')
    try:
        parsedjobcategory = parser.find("span", itemprop="occupationalCategory").text
    except AttributeError:
        parsedjobcategory = "AttributeError"
    try:
        parsedjobdescription = parser.select('.desc')[0].text
    except:
        parsedjobdescription = "AttributeError"
    # print(parsedjobdescription)
    return [parsedjobcategory, parsedjobdescription]

def jobDescWordCount(JobUrls):
    categorylist = []
    # keywordslist = keywords['word'].tolist()
    desclist = []
    wordcountlistdf = []  # pd.DataFrame(columns = keywordslist)
    i = 1
    for index, url in JobUrls.iterrows():
        i += 1
        print("======================================parsing ", i, "st/th/nd page============================")
        parser = parseJobUrlCategoryAndDescription(url['Job URL'])
        jobCategory = parser[0]
        categorylist.append(jobCategory)
        jobDescriptionString = parser[1].lower()
        remove_special_chars = jobDescriptionString.translate(
            {ord(c): '' for c in "\.•{2,}!@#$%^&*()[]\\{};:,./<>?\|`~-=_+\"\“\”"})
        word_list = remove_special_chars.split()
        desclist.append(word_list)
    return [categorylist, desclist]

def wordcountdictionaries(jobdescriptionwords):
    descdictionary = {}
    stopwords = open(r'..\Stop_words\long_stopwords.txt', 'r').read().split('\n')
    for word in jobdescriptionwords:
        if (word.isnumeric()) == False and (word not in stopwords):
            if word in descdictionary.keys():
                descdictionary[word] += 1
            else:
                descdictionary[word] = 1
    return descdictionary


if __name__=="__main__":
    parsedpages = parseCareerPages()
    JPMorganUSTotalJobList = createJPMorganUSTotalJobList(parsedpages)
    JPMorganJobListDF = pd.DataFrame(JPMorganUSTotalJobList[2:],
                                     columns=['Job ID', 'Job URL', 'Job Title', 'Country', 'State', 'City',
                                              'Date Posted'])
    boolarray = (JPMorganJobListDF['Country'] != '\nCountry\n')
    CleanJPMorganJobListDF = JPMorganJobListDF.loc[boolarray, :]
    #JPMorganUSTotalJobListCSV = CleanJPMorganJobListDF.to_csv('JPMorganUSTotalJobListCSV.csv')
    AllJobURLsDF = CleanJPMorganJobListDF.loc[:,
                   ['Job ID', 'Job URL', 'Job Title', 'Country', 'State', 'City', 'Date Posted']]
    webscrapedata = jobDescWordCount(AllJobURLsDF)
    jobcategories = webscrapedata[0]
    jobcategoriesdf = pd.DataFrame({'Job Category': jobcategories})
    CleanJPMorganJobListDF = CleanJPMorganJobListDF.join(jobcategoriesdf)
    jobdescriptions = webscrapedata[1]
    jobdescriptionstrings = []
    for jobdescription in jobdescriptions:
        jobdescriptionstrings.append(' '.join(jobdescription))
    jobdescriptionstringsdf = pd.DataFrame({'Job Description': jobdescriptionstrings})
    desclist = []
    for jobdescription in jobdescriptionstringsdf['Job Description']:
        jobDescriptionString = jobdescription.lower()
        remove_special_chars = jobDescriptionString.translate(
            {ord(c): '' for c in "\.•{2,}!@#$%^&*()[]\\{};:,./<>?\|`~-=_+\"\“\”"})
        word_list = remove_special_chars.split()
        desclist.append(word_list)
    listofdictionaries = []
    for jobdescription in desclist:
        listofdictionaries.append(wordcountdictionaries(jobdescription))
    wordcountfreqeachjobdf = pd.DataFrame(listofdictionaries)
    wordcountfreqeachjobdf = wordcountfreqeachjobdf.fillna(0)
    # wordcountfreqeachjobdf.to_csv("wordcountfreqeachjobdf.csv")
    columnnames = wordcountfreqeachjobdf.columns.values
    keywords = pd.read_csv(r'..\Documents_Top_100\100_text_rank.csv')
    requiredcolumns = []
    for word in keywords['keywords']:
        if word in columnnames:
            requiredcolumns.append(word)
    CleanJPMorganJobListDF = CleanJPMorganJobListDF.join(jobdescriptionstringsdf)
    CleanJPMorganJobListDF.fillna(0).to_csv('../Company_Job_Portal_Scraping_Generated_Files/JPMorganJobListDFDes.csv')
    listofdictionaries = []
    for jobdescription in jobdescriptions:
        listofdictionaries.append(wordcountdictionaries(jobdescription))
    wordcountfreqeachjobdf = pd.DataFrame(listofdictionaries)
    wordcountfreqeachjobdf = wordcountfreqeachjobdf.fillna(0)
    keywordcountineachurldf = wordcountfreqeachjobdf.loc[:, requiredcolumns]
    JPMorganUSTotalJobListWithKeywordCountdf = CleanJPMorganJobListDF.join(keywordcountineachurldf)
    JPMorganUSTotalJobListWithKeywordCountdf = JPMorganUSTotalJobListWithKeywordCountdf.fillna(0)
    JPMorganUSTotalJobListWithKeywordCountdf.to_csv('../Company_Job_Portal_Scraping_Generated_Files/JPMorganUSKeywordCount.csv')

