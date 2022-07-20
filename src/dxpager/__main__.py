#!/usr/bin/env python3

# pylint: disable=W1401,C0303
# pylint: disable=consider-using-f-string


"""
+---------------------------------------------------------------------+
|                                                                     |
|               ____ _  __ ____                                       |
|              / __ \ |/ // __ \____ _____ ____  _____                |
|             / / / /   // /_/ / __ `/ __ `/ _ \/ ___/                |
|            / /_/ /   |/ ____/ /_/ / /_/ /  __/ /                    |
|           /_____/_/|_/_/    \__,_/\__, /\___/_/                     |
|               -= DK1MI =-        /____/                             |
|                                                                     |
|                                                                     |
| A DAPNET bot that alerts you when stations pop up on a DX cluster   |
| that are new ones                                                   |
|                                                                     |
| Author:           Michael Clemens, DK1MI (dxpager@qrz.is)           |
|                                                                     |
| Documentation:    Please see the README.md file                     |
| License:          Please see the LICENSE file                       |
| Repository:       https://codeberg.org/mclemens/dxpager             |
|                                                                     |
+---------------------------------------------------------------------+
"""

import sys
import csv
import re
#import random
import os
from os.path import exists
import configparser
import zipfile
from telnetlib import Telnet
from pathlib import Path
import json
import requests
from requests.auth import HTTPBasicAuth


class DXPager():
    """DXPager class"""

    def __init__(self):
        """initialize things"""

        self.print_banner()

        self.config = configparser.ConfigParser()
        self.home_dir = str(Path.home())
        self.config_dir = self.home_dir + "/.config/dxpager/"
        # Check if config directory exists and else create it
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)
        self.config_file = os.path.expanduser(self.config_dir + 'dxpager.ini')
        self.read_config(self.config, self.config_file)

        self.check_files()

        if self.config['lotw']['user'] != "N0CALL" and self.check_lotw_confirmed:
            self.confirmed_entities = self.get_confirmed_entities()

        if self.check_cty:
            with open(self.config_dir + self.config['files']['cty'], encoding='us-ascii') as csvfile:
                self.cty = list(csv.reader(csvfile, delimiter=','))

        if self.check_lotw_activity:
            with open(self.config_dir + self.config['files']['lotw_activity'], encoding='us-ascii') as csvfile:
                self.lotw_activity = list(csv.reader(csvfile, delimiter=','))


    @staticmethod
    def print_banner():
        """print an awesome banner"""
        print("     ____ _  __ ____                        ") 
        print("    / __ \ |/ // __ \____ _____ ____  _____ ")
        print("   / / / /   // /_/ / __ `/ __ `/ _ \/ ___/ ") 
        print("  / /_/ /   |/ ____/ /_/ / /_/ /  __/ /     ")
        print(" /_____/_/|_/_/    \__,_/\__, /\___/_/      ")
        print("     -= DK1MI =-        /____/              ")
        print("")


    @staticmethod
    def read_config(config, file_name):
        """reads the configuration from the config file or
        creates a default config file if none could be found"""
        if os.path.isfile(file_name):
            config.read(file_name)
        else:
            config = configparser.ConfigParser()
            config['cluster'] = {
                'host': 'dxc.nc7j.com',
                'port': '7373',
                'user': 'N0CALL',
                'timeout': '100'}
            config['dapnet'] = {
                'dapnet_user': 'N0CALL',
                'dapnet_pass': 'xxxxxxxxxxxxxxxxxxxx',
                'dapnet_url': 'http://www.hampager.de:8080/calls',
                'dapnet_callsigns': 'N0CALL',
                'dapnet_txgroup': 'dl-all'}
            config['files'] = {
                'cty': 'cty.csv',
                'cty_url': 'https://www.country-files.com/bigcty/download/bigcty.zip',
                'lotw_confirmed': 'lotw.adi',
                'lotw_activity': 'lotw-user-activity.csv',
                'lotw_activity_url': 'https://lotw.arrl.org/lotw-user-activity.csv'}
            config['lotw'] = {
                'user': 'N0CALL',
                'password': 'CHANGEME',
                'mode': 'ssb'}

            with open(file_name, 'w', encoding='us-ascii') as configfile:
                config.write(configfile)
            print("\nNo configuration file found. A new configuration file has been created.")
            print("\nPlease edit the file " + file_name + " and restart the application.\n" )
            sys.exit()
        return config

    @staticmethod
    def download_file(url, local_filename):
        """downloads a file via HTTP and saves it to a defined file"""
        with requests.get(url, stream=True) as request:
            request.raise_for_status()
            with open(local_filename, 'wb') as file:
                for chunk in request.iter_content(chunk_size=8192):
                    file.write(chunk)
        return local_filename


    def check_files(self):
        """Checks if all necessary files are in the file system.
        Downloads all files and unzips them (if necessary)"""

        # check for lotw qsl information file
        if self.config['lotw']['user'] != "N0CALL":
            self.check_lotw_confirmed = exists(self.config_dir + self.config['files']['lotw_confirmed'])
            if not self.check_lotw_confirmed:
                print("The file " + self.config_dir + self.config['files']['lotw_confirmed'] + " is missing.")
                user = self.config['lotw']['user']
                password = self.config['lotw']['password']
                mode = self.config['lotw']['mode']
                url = "https://lotw.arrl.org/lotwuser/lotwreport.adi?login={}&password={}"\
                    "&qso_query=1&qso_qsl=yes&qso_mode={}&qso_qsldetail=yes&"\
                    "qso_qslsince=1970-01-01".format(user, password, mode)
                print("Trying to download " + url)
                self.download_file(url, self.config_dir + self.config['files']['lotw_confirmed'])
                self.check_lotw_confirmed = exists(self.config_dir + self.config['files']['lotw_confirmed'])
                if self.check_lotw_confirmed:
                    print("File successfully downloaded")
                else:
                    print("something went wrong while downloading " + url)
        else:
            self.check_lotw_confirmed = False

        # check for cty.csv file
        self.check_cty = exists(self.config_dir + self.config['files']['cty'])
        if not self.check_cty:
            url = self.config['files']['cty_url']
            print("The file " + self.config_dir + self.config['files']['cty'] + " is missing.")
            print("Trying to download " + url)
            zip_name = self.download_file(url, self.config_dir + "bigcty.zip" )
            with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                zip_ref.extract("cty.csv", path=self.config_dir)
            os.remove(zip_name)
            self.check_cty = exists(self.config_dir + self.config['files']['cty'])
            if self.check_cty:
                print("File successfully downloaded and extracted.")
            else:
                print("something went wrong while downloading " + url)

        # check for lotw user activity file
        self.check_lotw_activity = exists(self.config_dir + self.config['files']['lotw_activity'])
        if not self.check_lotw_activity:
            url = self.config['files']['lotw_activity_url']
            print("The file " + self.config_dir + self.config['files']['lotw_activity'] + " is missing.")
            print("Trying to download " + url)
            self.download_file(url, self.config_dir + self.config['files']['lotw_activity'])
            self.check_lotw_activity = exists(self.config_dir + self.config['files']['lotw_activity'])
            if self.check_lotw_activity:
                print("File successfully downloaded")
            else:
                print("something went wrong while downloading " + url)


    def get_confirmed_entities(self):
        """Reads the file downloaded from LotW with all confirmed QSOs,
        extracts all confirmed DXCCs and puts them into a list"""
        ret = []
        with open(self.config_dir + self.config['files']['lotw_confirmed'], \
                encoding='us-ascii') as file:
            for row in file:
                if re.search("<DXCC:", row):
                    dxcc = row.partition(">")[2].lower().rstrip()
                    if dxcc not in ret:
                        ret.append(dxcc)
        return ret


    def check_lotw(self, call):
        """Reads the LotW user activity file and returns the date
        of the last upload date if a specific call sign"""
        ret = ""
        for row in self.lotw_activity:
            if call == row[0]:
                ret = row[1]
                return ret
        return ret


    def get_cty_row(self, call):
        """Parses all CTY records, tries to find the DXCC entity of a
        specific call sign and returns the line as a list of strings"""
        done = False
        while not done:
            for row in self.cty:
                entities = row[9].replace(";", "").replace("=", "").split(" ")
                # TODO: Check if it is a speciall call (=) and mark it in the list
                for prefix in entities:
                    if call == prefix:
                        return row
            call = call[:-1]
            if call == "":
                return ["-", "-", "-", "-", "-", "-", "-"]
        return None


    def get_spots(self):
        """Connects to the specified telnet dx cluster, performs a login, grabs the
        output row by row, enriches it with data"""
        with Telnet(self.config['cluster']['host'], int(self.config['cluster']['port']), \
                int(self.config['cluster']['timeout'])) as telnet:
            while True:
                line_enc = telnet.read_until(b"\n")  # Read one line
                try:
                    #line = line_enc.decode('ascii')
                    line = line_enc.decode('utf-8')
                except:
                    print("Error while encoding the following line:") 
                    print(line_enc)
                # Enters the call sign if requested
                if "enter your call" in line:
                    b_user = str.encode(self.config['cluster']['user']+"\n")
                    telnet.write(b_user)
                # Detects the beginning of the stream
                elif " Hello " in line:
                    print(line)
                # This is true for every line representing a spot
                elif "DX de" in line or "Dx de" in line:
                    try:
                        # Extract all necessary fields from the line and store them
                        # into different variables.
                        #print(line)
                        call_de = re.search('D(X|x) de (.+?): ', line).group(2)
                        freq = re.search(': +(.+?)  ', line).group(1)
                        call_dx = re.search(freq + ' +(.+?) ', line).group(1)
                        #time = re.search('[^ ]*$', line).group(0)[0:4]
                        time = re.search(' (\d{4})Z', line).group(1)
                        comment = re.search(call_dx + ' +(.+?) +' + time, line).group(1)

                        # If the CTY file is available, further information will be
                        # gathered from it, e.g. continent, country, dxcc ID
                        if self.check_cty:
                            cty_details = self.get_cty_row(call_dx)
                        else:
                            cty_details = ["-","-","-","-","-","-","-","-","-","-"]

                        areaname = cty_details[1]
                        continent = cty_details[3]

                        # If the LotW user activity file is available and the call
                        # sign in question is actually a LotW user, we'll add a (L)
                        # to the message
                        if self.check_lotw_activity and self.check_lotw(call_dx):
                            lotw = " (L) "
                        else:
                            lotw = " "
                        
                        # Removes the trailing .0 from a frequency for better readability
                        freq = freq.replace('.0', '')

                        msg = "{}: {} de {} {} {}({}){}{}"\
                            .format(time, call_dx, call_de, freq, areaname, continent, lotw, comment)
                        dapnet_json = json.dumps({"text": msg, "callSignNames": \
                            [self.config['dapnet']['dapnet_callsigns']], \
                            "transmitterGroupNames": [self.config['dapnet']['dapnet_txgroup']], \
                            "emergency": False})
                        # If the DX station's entity hasn't been worked/confirmed via
                        # LotW yet, the message will be sent to the dapnet API
                        if self.check_lotw_confirmed and self.config['lotw']['user'] != "N0CALL" \
                                and cty_details[2] not in self.confirmed_entities:
                            response = requests.post(self.config['dapnet']['dapnet_url'], \
                                data=dapnet_json, auth=HTTPBasicAuth(\
                                self.config['dapnet']['dapnet_user'],\
                                self.config['dapnet']['dapnet_pass']))
                            print("!!! Sent to DAPNET: {} Response: {}".format(msg, response))
                        else:
                            print("    Not sent to DAPNET: {}".format(msg))

                    except AttributeError:
                        print(line)

def main():
    """main routine"""
    try:
        dx_pager = DXPager()
        dx_pager.get_spots()
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except EOFError:
        pass
