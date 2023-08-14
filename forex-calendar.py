from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
from datetime import datetime
import requests, re, pytz, time, os, sys
import pandas as pd


output_list = []
output_list.append("date_time,source,currency,impact,event_name\n")

def display_calendar():

    df = pd.read_csv('forex-calendar.txt')

    num_of_past_events = 10
    num_of_future_events = 27

    try:
        while True:
            os.system("cls")

            df['date_time'] = pd.to_datetime(df['date_time'])

            # sort the dataframe by date_time
            df.sort_values(by='date_time', ascending=True, inplace=True)

            # convert the date_time columns into GMT+8 timezone        
            df['date_time'] = df['date_time'].dt.tz_convert('Asia/Shanghai')

            # get the current time in GMT+8 and w/o msec
            gmt8_tz = pytz.timezone('Asia/Shanghai')
            current_time = pd.to_datetime(datetime.now()).replace(microsecond=0).replace(tzinfo=gmt8_tz)

            # get the time difference between current time and past/future time
            df['remaining_time'] = df['date_time'] - current_time

            # remove the CNY currency        
            df = df[df['currency'] != 'CNY']

            # reset the index column
            df.reset_index(drop=True, inplace=True)

            # get a number of past events
            past_time_df = df.query("remaining_time < '0 days'").tail(num_of_past_events)
            if len(past_time_df) > 0:
                # convert into more understandable format
                #past_time_df['remaining_time'] = (df['remaining_time'].dt.days.astype(str) + 'd-' + 
                #                        df['remaining_time'].dt.components.hours.astype(str) + 'h-' + 
                #                        df['remaining_time'].dt.components.minutes.astype(str) + 'm-' + 
                #                        df['remaining_time'].dt.components.seconds.astype(str) + 's')
                past_time_df['remaining_time'] = current_time - past_time_df['date_time']
                #print(past_time_df)
                past_time_df['remaining_time'] = past_time_df['remaining_time'].astype(str) + " ago"
                #print(past_time_df.to_string(index=False, header=False))
                #print("")

            # remove past events
            #df['remaining_time'] = pd.to_timedelta(df['remaining_time'])
            #df = df[df['remaining_time'] >= pd.Timedelta(0)]

            # get a number of future events
            future_time_df = df.query("remaining_time >= '0 days'").head(num_of_future_events)
            #print(future_time_df)
            #print(future_time_df.to_string(index=False, header=False))

            if len(past_time_df) == 0:
                concatenated_df = future_time_df
            else:
                concatenated_df = pd.concat([past_time_df, future_time_df], ignore_index=True)
            #print(concatenated_df)

            # remove duplicates
            concatenated_df = concatenated_df.drop_duplicates(subset=['date_time', 'currency', 'impact', 'event_name'])

            # re-order the column
            new_column_order = ['date_time', 'source', 'currency', 'impact', 'remaining_time', 'event_name']
            new_df = concatenated_df[new_column_order]
            print(new_df)

            time.sleep(5)

    except KeyboardInterrupt:
        print("Program terminated.")


def mql5com_calendar():
    site = 'https://www.forexfactory.com/calendar'
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site, headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    calendar_table = soup.find('table', class_='calendar__table')
    trows = calendar_table.find_all('tr', class_="calendar__row")

    last_date = ''
    last_time = ''
    for row in trows:
        all_td = row.find_all('td')

        if len(all_td)==11:

            if all_td[0].text.strip() != "":
                last_date = all_td[0].text.strip()
            if all_td[0].text.strip() == "":
                pass
            date = last_date
            date = re.sub(r'^[A-Za-z]{3}', '', date)
            date = re.sub(r' ', '', date)

            if all_td[1].text.strip() != "":
                last_time = all_td[1].text.strip()
            if all_td[1].text.strip() == "":
                pass
            time = last_time

            current_year = str(datetime.now().year)

            event_date_time = current_year + " " + date + " " + time
            date_time_valid = False
            pattern = r"\d{4} [A-Za-z]{3}\d{1,2} \d{1,2}:\d{2}[ap]m"
            match = re.match(pattern, event_date_time)
            if match:
                format_str = "%Y %b%d %I:%M%p"
                date_time = datetime.strptime(event_date_time, format_str)
                gmt8_tz = pytz.timezone('Asia/Shanghai')
                date_time = date_time.astimezone(gmt8_tz)
                date_time_valid = True

            currency = all_td[3].text.strip()

            impact = ""
            impact_td = all_td[4]
            impact_span = impact_td.find('span', { "title": re.compile(r'.+') })
            if impact_span != None:
                impact = impact_span['title']
                if (impact == "Low Impact Expected"):
                    impact = 'Low'
                elif (impact == "Medium Impact Expected"):
                    impact = 'Medium'
                elif (impact == "High Impact Expected"):
                    impact = 'High'
                else:
                    pass

            event_name = all_td[5].text.strip()
            event_name = re.sub(r',', '', event_name)

            if currency != "" and date_time_valid == True and (impact == "High" or impact == "Medium"):
                output_list.append("{},{},{},{},{}\n".format(date_time, 'mql5_com', currency, impact, event_name))


def babypips_calendar():
    site = 'https://www.babypips.com/economic-calendar'
    response = requests.get(site)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    section_pattern = re.compile(r'Section-module__container___[a-zA-Z0-9]+ Table-module__day___[a-zA-Z0-9]+')
    section_module_container = soup.find_all('div', class_=section_pattern)
    #print(len(section_module_container))

    for section in section_module_container:
        event_date = section.find('th', class_=re.compile(r'Table-module__date___[a-zA-Z0-9]+')).text
        trow_pattern = re.compile(r'Table-module__eventRow___[a-zA-Z0-9]+')
        trow = section.find_all('tr', class_=trow_pattern)
        for row in trow:
            date_time = ""
            date_time_valid = False        
            event_time = row.find('td', class_=re.compile(r'Table-module__time___[a-zA-Z0-9]+')).text
            current_year = str(datetime.now().year)
            event_date_time = current_year + " " + event_date + " " + event_time
            dt_pattern = r"\d{4} [A-Za-z]{3}\d{1,2} \d{1,2}:\d{2}"
            match = re.match(dt_pattern, event_date_time)
            if match:
                format_str = "%Y %b%d %H:%M"
                gmt0_tz = pytz.timezone('GMT')
                date_time = datetime.strptime(event_date_time, format_str).replace(tzinfo=gmt0_tz)
                gmt8_tz = pytz.timezone('Asia/Shanghai')
                date_time = date_time.astimezone(gmt8_tz)
                date_time_valid = True
                #print(date_time)
            else:
                date_time = event_date_time
            
            currency = row.find('td', class_=re.compile(r'Table-module__currency___[a-zA-Z0-9]+')).text

            impact = row.find('td', class_=re.compile(r'Table-module__impact___[a-zA-Z0-9]+')).text
            if impact == "high":
                impact = "High"
            elif impact == "med":
                impact = "Medium"
            elif impact == "low":
                impact = "Low"
            else:
                pass

            event_name = row.find('td', class_=re.compile(r'Table-module__name___[a-zA-Z0-9]+')).text
            event_name = re.sub(r'\,', ' ', event_name)

            if date_time_valid == True and (impact == "High" or impact == "Medium"):
                #print("{}, {}, {}, {}, {}".format(date_time, 'babypips', currency, impact, event_name))
                output_list.append("{},{},{},{},{}\n".format(date_time, 'babypips', currency, impact, event_name))


def forexfactory_calendar():
    site= "https://www.forexfactory.com/calendar"
    hdr = {'User-Agent': 'Mozilla/5.0'}
    req = Request(site, headers=hdr)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    calendar_table = soup.find('table', class_='calendar__table')
    calendar_rows = calendar_table.find_all('tr')
    last_date = ""
    last_time = ""

    for row in calendar_rows:
        if len(row) == 23:
            row_td = row.find_all('td')
            if len(row_td) == 11:
            
                event_date = row_td[0].text.strip()
                event_date = event_date[3:]
                if event_date != "":
                    last_date = event_date
                if event_date == "":
                    event_date = last_date

                event_time = row_td[1].text.strip()
                if event_time != "":
                    last_time = event_time
                if event_time == "":
                    event_time = last_time

                date_time = ""
                date_time_valid = False
                current_year = datetime.now().year
                event_date_time = str(current_year) + " " + event_date + " " + event_time
                #pattern = r"\d{4} ([A-Za-z]{3} \d{1,2} \d{1,2}:\d{2}[ap]m)"
                pattern = r"\d{4} [A-Za-z]{3} \d{1,2} \d{1,2}:\d{2}[ap]m"
                match = re.match(pattern, event_date_time)
                if match:
                    format_str = "%Y %b %d %I:%M%p"
                    date_time = datetime.strptime(event_date_time, format_str)
                    gmt8_tz = pytz.timezone('Asia/Shanghai')
                    date_time = date_time.astimezone(gmt8_tz)
                    date_time_valid = True
                    #print(date_time)
                else:
                    date_time = event_date_time

                currency = row_td[3].text.strip()

                impact = ""
                impact_span = row_td[4].find('span', class_='icon')
                match = re.search(r'title="([^"]*)"', str(impact_span))
                if match:
                    impact = re.sub(r' Impact Expected', '', match.group(1))
                
                event_name = row_td[5].text.strip()
                event_name = re.sub(r'\,', ' ', event_name)

                if impact != "Non-Economic" and date_time_valid == True and currency != "" and (impact == "High" or impact == "Medium"):
                    #print(("{} | {:<12} | {:<3} | {:<6} | {}").format(date_time, 'forexfactory', currency, impact, event_name))
                    output_list.append(("{},{},{},{},{}\n").format(date_time, 'ffactory', currency, impact, event_name))


def myfxbook_calendar():
    site = 'https://www.myfxbook.com/forex-economic-calendar'
    response = requests.get(site)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    calendar_rows = soup.find_all('tr', class_='economicCalendarRow')
    for row in calendar_rows:
        row_td = row.find_all('td')
        #event_date, time_left, currency, event_name, impact = row_td[0].text.strip(), row_td[1].text.strip(), row_td[3].text.strip(), row_td[4].text.strip(), row_td[5].text.strip()
        event_date, currency, event_name, impact = row_td[0].text.strip(), row_td[3].text.strip(), row_td[4].text.strip(), row_td[5].text.strip()

        ## Convert the date from GMT+0 into GMT+8
        # Current year
        current_year = datetime.now().year
        # Define the GMT+0 timezone
        gmt0_tz = pytz.timezone('GMT')
        # Convert the input string to a datetime object with the GMT+0 timezone
        date_time_gmt0 = datetime.strptime(f"{event_date}, {current_year}", "%b %d, %H:%M, %Y").replace(tzinfo=gmt0_tz)
        # Define the GMT+8 timezone
        gmt8_tz = pytz.timezone('Asia/Shanghai')
        # Convert the datetime object from GMT+0 to GMT+8
        date_time_gmt8 = date_time_gmt0.astimezone(gmt8_tz) 
        # Format the datetime object as a string in the desired output format
        event_gmt8 = date_time_gmt8.strftime('%b %d, %H:%M')

        # remove new line & comma in event name
        event_name = re.sub(r'\n', ' ', event_name)
        event_name = re.sub(r' \([A-Za-z]{3}\)', '', event_name)
        event_name = re.sub(r'\,', ' ', event_name)

        #if (impact == "High" or impact == "Medium") and time_left.find("min") >= 0:
        if (impact == "High" or impact == "Medium"):
            #print(("  {} | {:<9} | {} | {:<6} | {}").format(event_gmt8, time_left, currency, impact, new_event_name))
            #output_list.append(("  {} | {:<9} | {} | {:<6} | {}\n").format(event_gmt8, time_left, currency, impact, new_event_name))
            output_list.append(("{},{},{},{},{}\n").format(date_time_gmt8, 'myfxbook', currency, impact, event_name))


def main():
    myfxbook_calendar()
    forexfactory_calendar()
    babypips_calendar()
    mql5com_calendar()

    # Write to file
    with open('forex-calendar.txt', 'w') as file:
        for line in output_list:
            file.write(line)
    
    display_calendar()


if __name__ == "__main__":
    main()
