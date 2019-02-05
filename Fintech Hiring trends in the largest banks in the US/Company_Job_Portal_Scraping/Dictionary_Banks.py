#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib.request
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
import xlsxwriter
import requests
import re
from collections import Counter
import xlrd
import operator
import csv
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

browser = webdriver.Chrome(executable_path="D:\Program Files\ChromeGecko\chromedriver.exe")
browser.get('http://careers.bankofamerica.com/search-jobs.aspx?c=united-states&r=us')
PAGE_XPATH = '//*[@id="PlhContentWrapper_dglistview"]/tbody/tr[12]/td/a[2]'
PAGE1_XPATH = '//*[@id="PlhContentWrapper_dglistview"]/tbody/tr[12]/td/a'


# Read the CSV File - 100 Words for Text Rank/Text Count/ TFIDF
def read_csv():
    data = pd.read_csv(r'A:\2nd Semester\Data Science\Fintech-Hiring-trends-in-the-largest-banks-in-the-US\Data\Keywords\word_count.csv', skiprows=1,
                       names=["keyWords", "id", "freq"])
    keyWords = data["keyWords"].tolist()
    count = 0
    top100 = []
    for i in keyWords:
        if count < 100:
            top100.append(i)
        else:
            break
        count += 1
    return top100


# Bank Of America - getting href from each job in the page
def get_href():
    table_id = browser.find_element_by_id('search-result').find_element_by_tag_name('table')
    rows = table_id.find_elements_by_tag_name("tr")  # get all of the rows in the table
    href = []
    # This loop is to loop through the job postings
    for row in rows:
        for col in row.find_elements_by_tag_name("td"):
            for link in col.find_elements_by_tag_name("a"):  # getting the hRef
                href.append(link.get_attribute('href'))
    return href


# Bank Of America - getting Job Description for each href
def get_job_desc(url):
    page = urllib.request.urlopen(url)
    data = BeautifulSoup(page, "html.parser")
    job_desc = data.find('div', {"id": "job-detail-wrapper"}).find('div', {"id": "job-detail"})
    return job_desc


# Bank Of America - Final dictionary with job reference and word count
def boa_word_count(list_keywords, row):
    countPage = 1
    href_list = []
    dict = {}
    while countPage >= 1 and countPage < 800:
        link_count = 1
        for href in get_href():
            href_list.append(href)
            if link_count >= 10:
                break
            link_count += 1
        # this condition will be the last block to change the page after all the scrapping operations
        if countPage == 1:
            element = browser.find_element_by_xpath(PAGE1_XPATH)
            browser.execute_script("arguments[0].click();", element)
        else:
            element = browser.find_element_by_xpath(PAGE_XPATH)
            browser.execute_script("arguments[0].click();", element)
        countPage += 1
    # This is to scrape Job description from the list of URLs that is there in the list
    stop_words = set(stopwords.words('english'))
    filtered_sentence = []
    job_desc_word_freq = {}
    # Variable declaration ends
    for href in href_list:
        job_desc = ""
        job_desc_div = get_job_desc(href)
        job_number = href[44:52]
        for para in job_desc_div.findAll('p'):
            job_desc = job_desc + para.text
        # UnComment the next three lines to count freq of each word in a job_desc of BOA
        remove_special_chars = job_desc.translate(
            {ord(c): '' for c in "\.•{2,}!@#$%^&*()[]\\{};:,./<>?\|`~-=_+\"\“\”"})
        remove_special_chars = remove_special_chars.lower()
        avail_list = remove_special_chars.split()
        word_tokens = word_tokenize(remove_special_chars)

        for w in word_tokens:
            if w not in stop_words:
                filtered_sentence.append(w)
        for key, value in (Counter(filtered_sentence)).items():
            job_desc_word_freq.update({key: value})

        # iteration in keyword list to find the count of key_words in job description
        for keywords in list_keywords:
            if type(keywords) == str:
                freq = job_desc.count(keywords)
                dict.update({keywords: freq})
        row = company_word_count_to_excel('Bank of America', job_number, dict, href, row)
    # job_desc_word_freq = sorted(job_desc_word_freq.items(), key=lambda kv: kv[1])
    print(job_desc_word_freq)

    return row


# JP Morgan - Final dictionary with job reference and word count
def jp_morgan_word_count(list_keywords, row):
    df_list = []
    for pages in range(0, 7):
        pages = pages * 100 + 1
        for i in range(pages, pages + 99):  # Change the range for testing purpose
            url = 'https://jobs.jpmorganchase.com/ListJobs/All/sortdesc-jobtitle/Page-' + str(i)
            print('------------------######### PAGE : ' + str(i) + '##########---------------------')
            req = requests.get(url)
            soup = BeautifulSoup(req.content, 'html.parser')
            links_with_text = []
            for a in soup.find_all('a', href=True):
                if a.text:
                    links_with_text.append(a['href'])

            # print(links_with_text)
            r = re.compile('ShowJob.*')
            newlist = filter(r.search, links_with_text)
            a = []
            for i in newlist:
                a.append('https://jobs.jpmorganchase.com' + str(i))
            a = list(set(a))
            # print(len(a))
            for i in a:
                job_id_list = []
                url = i
                # print('------------------###################---------------------')
                req = requests.get(url)
                soup = BeautifulSoup(req.content, 'html.parser')
                # a = soup.findAll('div',{'class':'desc'})
                a = [el.get_text() for el in soup.find_all('div', attrs={"class": 'desc'})]
                b = soup.find_all('div', {'class': 'req'})
                for x in b:
                    text_jobid = x.get_text()
                    text_jobid = text_jobid[7:]
                    job_id_list.append(text_jobid)
                # print(a)
                list_word = list_keywords
                # print(list_word)
                str_list = ''.join(a)
                str_list = str_list.lower()
                remove_special_chars = str_list.translate(
                    {ord(c): '' for c in "\.•{2,}!@#$%^&*()[]\\{};:,./<>?\|`~-=_+\"\“\”"})
                f_list = remove_special_chars.split()
                wordfreq = {}
                dict_words = {}
                for i in list_word:
                    freq = remove_special_chars.count(i)
                    dict_words.update({i: freq})
                row = company_word_count_to_excel('J P Morgan', text_jobid, dict_words, url, row)


# Create the excel and write the headers in it
def write_excel(list_keywords):
    workbook = xlsxwriter.Workbook(r'A:\2nd Semester\Data Science\Fintech-Hiring-trends-in-the-largest-banks-in-the-US\Data\Scapped_files\wordCountScrape.xlsx', {'strings_to_urls': False})
    worksheet = workbook.add_worksheet()
    row = 0
    column = 4
    for item in list(list_keywords):
        worksheet.write(row, 0, "Job No")
        worksheet.write(row, 1, "Institution")
        worksheet.write(row, 2, "URL of Job Posting")
        worksheet.write(row, 3, "List Id")
        worksheet.write(row, column, item)
        column += 1
    return workbook, worksheet


# Word Count in Excel for both the companies
def company_word_count_to_excel(company, job_number, dicti, url, row):
    column = 4
    for item in list(dicti.values()):
        worksheet.write(row, 0, job_number)
        worksheet.write(row, 1, company)
        worksheet.write(row, 2, url)
        worksheet.write(row, column, item)
        column += 1
    row += 1
    return row


# Function to Convert Excel to CSV for both companies
def csv_from_excel():
    wb = xlrd.open_workbook(r'A:\2nd Semester\Data Science\Fintech-Hiring-trends-in-the-largest-banks-in-the-US\Data\Scapped_files\wordCountScrape.xlsx')
    sh = wb.sheet_by_name('Sheet1')
    your_csv_file = open(r'A:\2nd Semester\Data Science\Fintech-Hiring-trends-in-the-largest-banks-in-the-US\Data\Scapped_files\wordCountScrape_CSV.csv', 'w')
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in range(sh.nrows):
        wr.writerow(sh.row_values(rownum))

    your_csv_file.close()


# Main
if __name__ == '__main__':
    try:
        # Read the CSV file to get the list of keywords
        list_keywords = read_csv()
        # Calling the write excel method to prepare the excel
        workbook, worksheet = write_excel(list_keywords)

        print("Scrapping for BOA")
        row = boa_word_count(list_keywords, row=1)
        print("Scrapping for J.P Morgan")
        jp_morgan_word_count(list_keywords, row)
    except:
        print("Exception")
    finally:
        workbook.close()
        # Converting Excel to CSV
        csv_from_excel()
