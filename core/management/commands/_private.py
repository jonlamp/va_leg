"""
Virginia Legislative Scraper
Devoloped by Jon Lamp, 2023

Gets updates using the CSV files supplied by the 
Department of Legislative Automated Systems at

https://lis.virginia.gov/SiteInformation/ftp.html

Big thanks to them for making this information easily available. 
"""

import requests
import csv
import codecs
from bs4 import BeautifulSoup as bs
import lxml.html
import re
from core.models import Legislator, Session, Bill
import time
from tqdm import tqdm
import datetime as dt
#after this session, I'll need a better way to get the current session
CONFIG = {
    'session':'231'
}


def get_csv_dicts(session:str,filename:str)->list:
    """
    Returns a list of dictionaries with output from
    requested file. Session is two digits representing
    the legislative year, followed by a single digit
    for session number. For example, the first session of 
    2023 would be "231"
    """
    url = f'https://lis.virginia.gov/SiteInformation/csv/{session}/{filename}.csv'
    response = requests.get(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    else:
        #apparently uses iso encoding
        decoded_response = codecs.iterdecode(response.iter_lines(),'iso-8859-1') 
        reader = csv.DictReader(decoded_response)
        l_reader = list(reader)
        for row in l_reader:
            for k,v in row.items():
                #each field sometimes has trailing spaces
                row[k] = v.strip()
        return l_reader


#legislators should be updated first, as many other records are related
def update_legislators(session:str)->dict:
    """
    Checks db for legislator, adds if not found. Returns dict with:
        -New legislators
        -list of csv legislators
    """
    def scrape_lis_legislator(session:str,lis_id:str)->dict:
        """
        Returns dictionary of legislator information from LIS page - as 
        the CSVs that DLAS provides do not provide certain desired information.
        """
        url = f"https://lis.virginia.gov/cgi-bin/legp604.exe?{session}+mbr+{lis_id}"
        class ScrapingError(Exception):
            pass
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)
        else:
            soup = bs(response.text,features='lxml')
            main = soup.find(id="mainC")
            if main is None:
                raise ScrapingError(response.text)
            else:
                font = main.font.contents[0]
                return {
                    'session':session,
                    'party':re.findall(".(?=\))",font)[0],
                    'district':re.findall("\d+", font)[0]
                }

    csv_legislators = get_csv_dicts(session,'members')
    #existing_legislators = Legislator.objects.values()
    new_legislators = 0
    pbar = tqdm(total=len(csv_legislators))
    pbar.set_description("Importing legislators...")
    for rep in csv_legislators:
        #matching_reps = [x for x in existing_legislators if x['lis_id']==rep['MBR_MBRID']]
        #if len(existing_legislators) == 0 or len(matching_reps)==0:
        pbar.update(1)

        if not Legislator.objects.filter(lis_id=rep['MBR_MBRID']).exists():
            time.sleep(1) #ideally keeps LIS from locking us out
            rep_details = scrape_lis_legislator(session,rep['MBR_MBRID'])
            rep.update(rep_details)
            record = Legislator(
                name=rep['MBR_NAME'],
                party=rep['party'],
                district=rep['district'],
                lis_id=rep['MBR_MBRID'],
                lis_no=rep['MBR_MBRNO']
            )
            record.save()
            new_legislators += 1
    pbar.close()

    return {
        'new_legislators':new_legislators,
        'csv_legislators':csv_legislators
    }

def update_bills(session:str)->dict:
    """
    Checks database for bill in session. If not found, bill is added from
    csv file. 
    """
    try:
        csv_bills = get_csv_dicts(session,'bills')
    except:
        raise
    else:
        existing_bills = Bill.objects.filter(session__lis_id=session)
        new_bills = 0
        pbar = tqdm(total = len(csv_bills))
        pbar.set_description("Importing bills...")
        for bill in csv_bills:
            if not existing_bills.filter(bill_number = bill['Bill_id']).exists():
                patron = Legislator.objects.get(lis_id=bill['Patron_id'])
                sesh = Session.objects.get(lis_id=session)
                d_introduced = dt.datetime.strptime(bill['Introduction_date'],"%m/%d/%y")
                record = Bill(
                    bill_number = bill['Bill_id'],
                    title = bill['Bill_description'],
                    d_introduced = d_introduced.strftime("%Y-%m-%d"),
                    emergency = bill['Emergency']=='Y',
                    passed = bill['Passed']=='Y',
                    patron = patron,
                    session = sesh
                )
                record.save()
                new_bills += 1
            pbar.update(1)
        pbar.close()
        return {
            "new_bills":new_bills
        }

def update_summaries(session:str)->dict:
    def clean_summary(summary:dict)->dict:
        """
        You give me a dictionary of a summary, I give you a dictionary of a summary.
        """
        bill = summary['SUM_BILNO'].strip()
        bill = bill[0] + str(int(bill[1:]))
        doc_id = summary['SUMMARY_DOCID'].strip()
        category = summary['SUMMARY_TYPE'].strip()
        content_dirty = summary['SUMMARY_TEXT'].strip()
        content_dirty = content_dirty.replace('\n','')
        html = lxml.html.document_fromstring(content_dirty)
        content = html.text_content()
        return {
            'bill_number':bill,
            'doc_id':doc_id,
            'category':category,
            'content':content
        }
