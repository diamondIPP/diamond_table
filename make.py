#!/usr/bin/env python
#cdorfer@ethz.ch

import os
import HTML
import ConfigParser
import json


def listDirs(path):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path,d))]

def makeLink(name,target):
	return "<a href=" + target + ">" + name + "</a>"

def folderExists(path):
	return os.path.isdir(path)

def createOverview(bt_dates, other_cols, data_dir, exclude):
	html_file = "index.html"
	f = open(html_file,'w')
	f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n')
	f.write('<html>\n<head>\n<meta content="text/html; charset=ISO-8859-1" http-equiv="content-type">\n')
	f.write('<title> ETH Diamonds Overview </title>\n')
	f.write('</head>\n<body>\n\n\n')
	f.write('<h2>ETH Diamonds Overview</h2>\n')

	#build table header
	header_row = ['Diamond']
	for date in bt_dates:
		header_row.append(date)
	for col in other_cols:
		header_row.append(col)

	#fill table with information
	table_data = []
	diamonds = listDirs(data_dir)
	for ex in exclude:
		diamonds.remove(ex)

	for dia in diamonds:
		row = []
		row.append(dia)

		#fill beam test stuff:
		for date in bt_dates:
			path = data_dir + dia + "/BeamTests/" + date
			if folderExists(path):
				row.append(makeLink("Results", path+"/index.php"))
			else:
				row.append("")

		#fill other stuff:
		for col in other_cols:
			path = data_dir + dia + "/" + col
			if folderExists(path):
				row.append(makeLink("Info", path+"/index.php"))
			else:
				row.append("")
		table_data.append(row)

	html_code = HTML.table(table_data, header_row=header_row)
	f.write(html_code)
	f.write('\n\n\n</body>\n</html>\n')
	f.close()



if __name__ == "__main__":

	#get general configuraton from 'conf.ini'
	conf = ConfigParser.ConfigParser()
	conf.read('conf.ini')
	data_dir = conf.get("General","data_directory")

	#get information that concerns making the table
	bt_dates = json.loads(conf.get("BeamTests","dates"))
	other_cols = json.loads(conf.get("Other","columns"))
	exclude = json.loads(conf.get("General", "exclude"))
	createOverview(bt_dates, other_cols, data_dir, exclude)