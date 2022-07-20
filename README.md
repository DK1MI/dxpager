# DXPager

This script is a bot that sends you DAPNET messages if a DX station is spotted whose entity you have not
worked/confirmed before. To achieve this, it
  * parses the output of a specific dx cluster server
  * downloads your LotW QSL file
  * determines the DX station's country
  * determines the DX station's continent
  * determines if the DX station uses LotW
  * determines if the DX station's country has been confirmed via LotW
  * and finally - if it's a new DXCC - sends the information to your dapnet pager

# Limitations

The following limitations are present:

  * read-only: you can't send commands to the dx cluster server via this tool
  * no filters: you need to configure your filter on the server

# Installation

DXPager needs Python 3 and the following libraries:

 * requests

Furthermore, you need an account at LotW and hampager.de

In order to install dxpager, just clone the repo:

```
# git clone https://codeberg.org/mclemens/dxpager.git
```

# Usage

 * execute the application with "python3 dxpager"
 * DXPager creates a default config file and states its location (e.g. _~/.config/dxpager/dxpager.ini_)
 * adapt _~/.config/dxpager/dxpager.ini_ to your needs. Important setting are:
    * cluster/host and cluster/port: Change this if you want to use another cluster server
    * cluster/user: Enter here your call sign
    * lotw/user: Enter here your lotw user name (your call sign). Leave at "N0CALL" to disable this feature.
    * lotw/password: Enter here your lotw password
    * lotw/mode: Enter here the mode you would like to filter the QSL download from LotW
    * dapnet_user: Enter here the hampager.de user name (your call sign)
    * dapnet_pass: Enter here your hampager.de password
    * dapnet_callsigns: Enter here the call sign of the receiver
    * dapnet_txgroup: Adapt the tx group to your region
 * execute the application again with "dxpager"
 * the software now tries to download the following files and stores them into the configuration directory:
    * https://www.country-files.com/bigcty/download/bigcty.zip (will be extracted)
    * https://lotw.arrl.org/lotw-user-activity.csv
    * https://lotw.arrl.org/lotwuser/lotwreport.adi?login={}&password={}&qso_query=1&qso_qsl=yes&qso_mode={}&qso_qsldetail=yes&qso_qslsince=1970-01-01

# License

see ![LICENSE](LICENSE)
