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
from core.models import Legislator, Session, Bill, BillSummaries,Action,Patron
import time 
from io import StringIO
from tqdm import tqdm
import datetime as dt
import pandas as pd
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
        try:
            file = StringIO(response.content.decode('utf-8'))
            reader = csv.DictReader(file)
            l_reader = list(reader)
            file.close()
        except UnicodeDecodeError: #only go to iterdecode if there's an error reading the file
            try:
                #apparently uses iso encoding
                decoded_response = codecs.iterdecode(response.iter_lines(),'iso-8859-1')
                reader = csv.DictReader(decoded_response)
                l_reader = list(reader)
            except:
                raise

        for row in l_reader:
            for k,v in row.items():
                #each field sometimes has trailing spaces
                row[k] = v.strip()
        return l_reader

def bill_number_to_id(bill_number:str)->str:
    """
    Translates "XB0000" bill number format to "XB0" format
    """
    return bill_number[:2] + str(int(bill_number[2:]))


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

def find_individual_legislator(session:str,lis_id:str,leg_name:str,lookback=5)->Legislator:
    """
    Finds legislator by lis_id in previous sessions. Default number of years to look 
    back through is 5.
    """
    for i in range[1:lookback+1]:
        print(
            f"""
            Cannot find legislator {lis_id}, {leg_name}
            """
        )
        session_base = int(session[:2])
        searching = str(session_base - (i))+"1"
        print(f"\nSearching session {searching}")
        try:
            lis_output = scrape_lis_legislator(
                session=searching,
                lis_id = lis_id
            )
            new_rep = Legislator(
                name = leg_name,
                party = lis_output['session'],
                district = lis_output['district'],
                lis_id = lis_id,
                lis_no = lis_id[:1] + str(int(lis_id[1:])).zfill(4)
            )
            new_rep.save()
            patron = new_rep
            return patron
        except SystemExit:
            if i >= 5:
                print("Could not find legislator in previous 5 sessions.")
                raise
            else:
                time.sleep(1)
                pass
#legislators should be updated first, as many other records are related
#plus, legislators are not bound by time and session in quite the same way
#that other fields are.

#ahh, to not be bound by time... or session?
def update_legislators(session:str)->dict:
    """
    Checks db for legislator, adds if not found. Returns dict with:
        -Count of new legislators
        -list of csv legislators
    """

    csv_legislators = get_csv_dicts(session,'members')
    new_legislators = 0
    pbar = tqdm(total=len(csv_legislators))
    pbar.set_description("Importing legislators...")
    for rep in csv_legislators:
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
        'count':new_legislators,
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
        sesh = Session.objects.get(lis_id=session)
        new_bills = 0
        pbar = tqdm(total = len(csv_bills))
        pbar.set_description("Importing bills...")
        for bill in csv_bills:
            #check to make sure bill does not already exist or if it exists in 
            #other sessions
            d_introduced = dt.datetime.strptime(bill['Introduction_date'],"%m/%d/%y")
            try:
                matching_bill = Bill.objects.get(
                    bill_number=bill['Bill_id'],
                    d_introduced = d_introduced
                )
                if not matching_bill.sessions.filter(pk = sesh.pk).exists():
                    matching_bill.sessions.add(sesh)
            except Bill.MultipleObjectsReturned:
                print(f"""Multiple bills match these parameters:
                -Bill: {bill['Bill_id']}
                -Introduced: {bill['Introduction_date']}
                """)
                raise
            except Bill.DoesNotExist:
                #legislators are sometimes deleted. Need to add info from 
                #previous session(s) if so. #check a maximum of 5 sessions
                if not Legislator.objects.filter(lis_id=bill['Patron_id']).exists():
                    patron_id = bill['Patron_id']
                    #add default information for now
                    patron = Legislator(
                        name=bill['Patron_name'],
                        lis_id = patron_id,
                        lis_no = str(patron_id[0]) + str(int(patron_id[1:])).zfill(4)
                    )
                    patron.save()
                    #patron = find_individual_legislator(
                    #    session=session,
                    #    lis_id = patron_id,
                    #    leg_name = bill['Patron_name']
                    #)
                else:
                    patron = Legislator.objects.get(lis_id=bill['Patron_id'])
                record = Bill(
                    bill_number = bill['Bill_id'],
                    title = bill['Bill_description'],
                    d_introduced = d_introduced.strftime("%Y-%m-%d"),
                    emergency = bill['Emergency']=='Y',
                    passed = bill['Passed']=='Y',
                    introduced_by = patron,
                )
                record.save()
                record.sessions.add(sesh)
                new_bills += 1
            except:
                raise
            pbar.update(1)
        pbar.close()
        return {
            "count":new_bills
        }

def update_summaries(session:str)->dict:
    """
    Collects summaries and updates of summaries from LIS and adds them to the database
    """
    def clean_summary(summary:dict)->dict:
        """
        You give me a dictionary of a summary, I give you a dictionary of a summary.
        Returns 
        -bill_number
        -doc_id
        -category
        -content
        """

        bill = summary['SUM_BILNO'].strip()
        bill = bill_number_to_id(bill) #csv uses bill ID
        doc_id = summary['SUMMARY_DOCID'].strip()
        category = summary['SUMMARY_TYPE'].strip()
        content_dirty = summary['SUMMARY_TEXT'].strip()
        content_dirty = content_dirty.replace('\n',' ')
        content_dirty = content_dirty.replace('  ',' ')
        #the bolded part of the summary is just the title again
        #so we'll remove the bold part
        content_dirty = re.sub(r"(<b>.*</b>)"," ",content_dirty)
        html = lxml.html.document_fromstring(content_dirty)
        content = html.text_content()
        return {
            'bill_number':bill,
            'doc_id':doc_id,
            'category':category,
            'content':content
        }
    try:
        csv_summaries = get_csv_dicts(session,'Summaries')
        csv_summaries = [clean_summary(x) for x in csv_summaries]
    except:
        raise
    else:
        new_summaries = 0
        pbar = tqdm(total = len(csv_summaries))
        pbar.set_description("Importing summaries...")
        sesh = Session.objects.filter(lis_id = session)
        session_bills = Bill.objects.filter(sessions__in=sesh)
        db_summaries = BillSummaries.objects.filter(bill__sessions__in=sesh)
        for row in csv_summaries:
            if not db_summaries.filter(doc_id = row['doc_id']).exists():
                try:
                    bill = session_bills.get(bill_number = row['bill_number'])
                except Bill.DoesNotExist:
                    print(f"Cannot find bill {row['bill_number']}")
                else:
                    summary = BillSummaries(
                        doc_id = row['doc_id'],
                        category = row['category'],
                        content=row['content'],
                        bill = bill
                    )
                    summary.save()
                    new_summaries +=1
            pbar.update(1)
        pbar.close()
        return {
            'count':new_summaries
        }
def update_actions(session:str)->dict:
    """
    Collects list actions found in the 'history.csv' file on LIS
    """
    csv_actions = get_csv_dicts(session,'History')
    pbar = tqdm(total = len(csv_actions))
    pbar.set_description("Importing actions...")
    sesh = Session.objects.filter(lis_id = session)
    session_bills = Bill.objects.filter(sessions__in=sesh)
    new_actions = 0
    for row in csv_actions:
        d_action = dt.datetime.strptime(row['History_date'],"%m/%d/%y")
        description = row['History_description']
        try:
            bill = session_bills.get(bill_number=row['Bill_id'])
        except Bill.DoesNotExist:
            print(f"Cannot find bill {row['Bill_id']}")
        except:
            raise
        
        if not bill.actions.filter(
            d_action = d_action,
            description=description
        ).exists():
            new_action = Action(
                d_action = d_action,
                description = description,
                bill = bill
            )
            if len(row['History_refid']) !=0:
                new_action.refid = row['History_refid']
            new_action.save()
            new_actions += 1
        pbar.update(1)
    pbar.close()
    return {
        'count':new_actions
    }  

def update_patrons(session:str)->dict:
    """
    Collects patrons found in 'sponsors.csv'
    """
    #we need to manually handle the csv reader here, as there are unlabeled columns.
    #everything after the "-" in the csv should be joined by a space (cell 6 and after)
    url = f'https://lis.virginia.gov/SiteInformation/csv/{session}/sponsors.csv'
    response = requests.get(url)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except:
        raise 
    else:
        file = StringIO(response.content.decode('utf-8'))
        reader = csv.reader(file)
        l_reader = list(reader)
        file.close()

    csv_info = []
    for row in l_reader[1:]: #exclude header row
        row[3] = row[3][6:]
        
        results = {
            'member_name':row[0].strip(),
            'member_id':row[1].strip(),
            'bill_id':row[2].strip(),
            'patron_type': row[3].strip()
        }
        csv_info.append(results)

    pbar = tqdm(total = len(csv_info))
    pbar.set_description("Importing patrons...")
    sesh = Session.objects.filter(lis_id = session)
    session_bills = Bill.objects.filter(sessions__in=sesh)
    new_patrons = 0
    for row in csv_info:
        try:
            bill = session_bills.get(bill_number=bill_number_to_id(row['bill_id']))
        except Bill.DoesNotExist:
            print(f"Bill {row['bill_id']} cannot be found.")
        else:
            try:
                legislator = Legislator.objects.get(lis_no = row['member_id'])
            except Legislator.DoesNotExist:
                print(f"\nCould not add {row['member_id']} as a patron of {row['bill_id']}")
            else:
                patron_type = row['patron_type']
                if not Patron.objects.filter(bill=bill,legislator=legislator).exists():
                    new_patron = Patron(
                        patron_type = patron_type,
                        bill=bill,
                        legislator = legislator
                    )
                    new_patron.save()
                    new_patrons += 1
        pbar.update(1)
    pbar.close()
    return {
        'count':new_patrons
    }
