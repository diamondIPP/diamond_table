# Diamond Table Creator
creates html files to create a summary of the results of the PSI high rate beam tests

## required python packages
- termcolor
- numpy
- progressbar
- pytz

## Running

 - ./make_website.py (-tc) (-d) (-t)
    - optional arguments:
    - -tc: only updates for a certain tc
    - -d: only updates for a given diamond
    - -t: test mode
   
 - adding new beam test
    - ./make_website.py -> update()
    - update all regarding Diamonds/*/info.ini files
    - add types of new diamonds to conf.ini
