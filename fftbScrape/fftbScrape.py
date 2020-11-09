import requests
from bs4 import BeautifulSoup
import datetime
import os
import json
import datetime

#fftb2020Week
#   Take a date, and give the NFL 2020 week number for that date.
#
#   Input:
#       date: The date to run against, as a datetime module date.
#             Default = current date
def fftb2020Week(date = datetime.date.today()):
    # I could do a lot of this in a big statment but for code clarity, lets separate it out
    # First lets find today.
    curDate = date
    
    # Now for logic time.
    # NFL week one is 9-8 (Tuesday) through 9-14 (Monday).  This is iso week 37-38
    
    # If we are before 9-8, we want 'preseason'
    if curDate < datetime.date(2020, 9, 8):
        return('preseason')
    
    # I thought we were going to have to do something fancy for week 17 since it is Jan 3 (Sun)
    # Looks like we luck out and this is the last isoweek (53) and it will work as is. 
    # I don't get why iso week 53 is legit, but apparently it is.
    
    # We are not before the first week... now to compute NFL week
    nflWeek1 = 36    
    
    # Now let's find our ISO week.
    isoWeek = curDate.isocalendar()[1]

    retWeek = isoWeek - nflWeek1
    
    # Mondays are the NFL week before.
    if curDate.weekday() == 0:
        # take the iso week and subtract 37
        retWeek -= 1
    
    return retWeek


#fftbWebScrape
#   This function abstracts away the actual requests call and beautiful soup
#   from everything else we might want to do.  This is where the hacky process
#   of figuring out the best way to identify the HTML table and then pulling the
#   data out.
#
#   Input:
#       ppr:     True or False.  
#                Default True
#       pos:     'qb', 'rb', 'wr', 'te', 'k', 'def'.  
#                Default 'qb'
#       week:    Integer representing the NFL week.  I'm not sure how this handles
#                projections not being made yet.  I think no results.  
#                preseason is 'preseason'
#                Default = week of current date.
#       fftbURL: url to scrape, best to leave default.
#                Default = 'https://fftoolbox.scoutfantasysports.com/football/rankings/index.php'
#   Output:
#       List of Lists
#
def fftbWebScrape(ppr=True, pos='qb', week=fftb2020Week(),
                  fftbURL='https://fftoolbox.scoutfantasysports.com/football/rankings/index.php'):

    # This has a high chance of changing if they redesign their site.  Saving up here since it
    # is a pseudo magic number
    cssMagicRes  = '#results > table tr[class="fantasy-ranking-row"]'

    retList = []
    payload = {'pos': pos,
               'week': week}

    # Abstracting away the fact that this true false is a string
    if ppr:
        payload['noppr'] = 'false'
    else:
        payload['noppr'] = 'true'

    # Verify is False here because this is for personal use and I don't really care
    fftoolbox = requests.get(fftbURL, params=payload, verify=False)
    soup = BeautifulSoup(fftoolbox.text, 'html.parser')

    for row in soup.select(cssMagicRes):
        rankrow = []
        
        #For the header
        cells = row.find_all('th')

        if len(cells) > 0:
            for cell in cells:
                for string in cell.stripped_strings:
                    rankrow.append(string)
            retList.append(rankrow)

        cells = row.find_all('td')

        if len(cells) > 0:
            for cell in range(len(cells)):
                if(cell == 3): #The teams are buried in link titles
                    subDiv = cells[cell].select('.team-logo')
                    if(len(subDiv) > 0):
                        rankrow.append(cells[cell].select('.team-logo')[0]['title'])
                    else:
                        rankrow.append('')
                else:
                    rankrow.append(' '.join(cells[cell].stripped_strings))

            retList.append(rankrow)

    return retList

#fftbScrape
#   This function wraps fftbWebScrape, in order to reduce calls to the webserver.
#   Signature is the same between the two functions, so I ended up just renaming
#   this one, so that calling scripts would be uneffected.
#
#   Input:
#       ppr:  True or False.  Default True
#       pos:  'qb', 'rb', 'wr', 'te', 'k', 'def'.  Default 'qb'
#       week: Integer representing the NFL week.  I'm not sure how this handles
#             projections not being made yet.  I think no results.  Default = 1.
#             preseason is 'preseason'
#   Output:
#       List of Lists
#
#   Usage Example
#       qbrankings = []
#       
#       qbrankings = fftbScrape(ppr = True, pos = 'QB', week = 'preseason') 
#       
#       print('PPR Week 1')
#       for row in qbrankings:
#           print(row)
#       
#       qbrankings = []
#       
#       qbrankings = fftbScrape(ppr = False, pos = 'QB', week = 'preseason') 
#       
#       print('NONPPR Week 1')
#       for row in qbrankings:
#           print(row)
#       
#       
#       qbrankings = fftbScrape(ppr = True, pos = 'QB', week = 3) 
#       
#       print('Week 3')
#       for row in qbrankings:
#            print(row) 
def fftbScrape(ppr=True, pos='qb', week=fftb2020Week(),
               fftbURL='https://fftoolbox.scoutfantasysports.com/football/rankings/index.php'):
    dataDir = './ffToolboxData'
    
    # First we want to build a string that represents something uniquey for the day and params.  This will be used
    # to determine if the file exists already and will stop the call.
    currentDate = datetime.datetime.now()
    
    fileName = currentDate.strftime('%d-%m-%Y_')
    
    if ppr:
        fileName += 'PPR_'
    else:
        fileName += 'NOPPR_'
    
    fileName += 'week_' + str(week) + '_'
    
    fileName += 'pos_' + pos
    
    fileName += '.dat'
    
    
    # Now we want to check for the directory.  Since I haven't made the decision yet, this should be a directory in the current
    # directory called ffToolboxData
    ## This can throw exceptions I'm not catching
    if not os.path.isdir(dataDir):
        os.mkdir(dataDir)
    
    # Now we know the directory exists... we can check if the file exists
    if os.path.isfile(dataDir + '/' + fileName):
        # The file exists, we can just read from it and send that data up.
        with open(dataDir + '/' + fileName, 'r') as file:
            dataList = json.loads(file.read())
            
        return dataList
    else:
        # The file doesn't exist.  We need to call the scrape, save the data into the file and then send the data up. 
        dataList = fftbWebScrape(ppr, pos, week, fftbURL)
        
        with open(dataDir + '/' + fileName, 'w') as file:
            file.write(json.dumps(dataList))
        
        return dataList
    