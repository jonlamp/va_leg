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
import re
from core.models import Legislator, Session

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
    if response.status_code != 200:
        print(f'Failed to collect file. Error code:{response.status_code}')
        return None
    else:
        #apparently uses iso encoding
        decoded_response = codecs.iterdecode(response.iter_lines(),'iso-8859-1') 
        reader = csv.DictReader(decoded_response)
        return list(reader)

#legislators should be updated first, as many other records are related
def update_legislators(session:str)->int:
    """
    Checks db for legislator, adds if not found. Returns number of new legislators.
    """
    def scrape_lis_legislator(session:str,lis_id:str)->dict:
        """
        Returns dictionary of legislator information from LIS page - as 
        the CSVs that DLAS provides do not provide certain desired information.
        """
        url = f"https://lis.virginia.gov/cgi-bin/legp604.exe?{session}+mbr+{lis_id}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f'Failed to find legislator. Error code: {response.status_code}')
            return None
        else:
            soup = bs(response.text)
            main = soup.find(id="mainC")
            font = main.font.contents[0]
            return {
                'session':session,
                'party':re.findall(".(?=\))",font)[0],
                'district':re.findall("\d+", font)[0]
            }

    csv_legislators = get_csv_dicts(session,'members')
    existing_legislators = Legislator.objects.values()
    new_legislators = 0
    for rep in csv_legislators:
        matching_reps = [x for x in existing_legislators if x['lis_id']==rep['MBR_MBRID']]
        if len(matching_reps)==0:
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

    return new_legislators

#bills = get_csv_dicts(CONFIG['session'],'bills')
