# coding=utf-8
# 
# Convert files from Heng Hua International to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from IB.utility import get_current_path, writeToFile, toRecordGroups
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class InvalidTradeType(Exception):
	pass



def processTradeFile(file, outputDir):
	return writeToFile(
				toRecordGroups(
					sortByTradeTime(
						list(
							map(toTradeRecord, linesToRecords(fileToLines(file)))
						)
					)
				)
				, outputDir
				, 'TEST6C'
				, 'HGNH-QUANT'
			)



def fileToLines(file):
	"""
	[String] file => [List] lines, each line is a list of columns
	"""
	wb = open_workbook(filename=file)
	ws = wb.sheet_by_index(0)
	lines = []
	row = 0
	while row < ws.nrows:
		thisRow = []
		column = 0
		while column < ws.ncols:
			cellValue = ws.cell_value(row, column)
			if isinstance(cellValue, str):
				cellValue = cellValue.strip()
			thisRow.append(cellValue)
			column = column + 1

		lines.append(thisRow)
		row = row + 1

	return lines



def linesToRecords(lines):
	"""
	[List] lines => [Iterable] records

	Using the first row as header, the function converts the remaining lines
	as records.
	"""
	def lineToRecord(line):
		r = {}
		for (field, value) in zip(headers, line):
			r[field] = value

		return r

	headers = lines[0]
	return map(lineToRecord, lines[1:])



def toTradeRecord(record):
	"""
	[Dictionary] record => [Dictionary] Bloomberg upload record

	Create a new trade record from the existing record, the trade record has 8
	necessary fields:

	1. BloombergTicker
	2. Side
	3. Quantity
	4. Price
	5. TradeDate: of type datetime
	6. SettlementDate: of type datetime
	7. Commission Code 1: fixed to 'Broker Commission'
	8. Commission Amt 1: total commission
	"""
	r = {}
	r['BloombergTicker'] = record['Contract']
	r['Side'] = getTradeSide(record)
	r['Quantity'] = record['Lots']
	r['Price'] = record['Trade Price']
	r['TradeDate'] = xldate_as_datetime(record['Trade Date'], 0)
	r['SettlementDate'] = xldate_as_datetime(record['Settlement Date'], 0)
	r['Commission Code 1'] = 'Broker Commission'
	r['Commission Amt 1'] = record['Commission']

	r['tradeTime'] = record['Trade Time']	# to be used for sorting

	# Convert to integer if possible, sometimes if the quantity of a futures
	# contract is a float (like 15.0), BLoomberg may generate an error.
	if r['Quantity'].is_integer():
		r['Quantity'] = int(r['Quantity'])

	return r



def getTradeSide(record):
	"""
	[Dictionary] record => [String] side
	"""
	tMap = {
		('B', 'O'): 'Buy',
		('B', 'C'): 'Cover',
		('S', 'O'): 'Short',
		('S', 'C'): 'Sell'
	}

	try:
		return tMap[(record['B/S'], record['O/C'])]
	except KeyError:
		raise InvalidTradeType('{0}'.format(record))



def sortByTradeTime(records):
	"""
	[List] records => [List] new records

	Sort the list of records by their trade date and time, the earlier trades 
	are put in front. Here we assume the trade date is always the same, therefore
	we just sort by trade time.
	"""
	def takeTradeTime(record):
		return record['tradeTime']

	return sorted(records, key=takeTradeTime)



def processCashFile(file):
	pass



def processPositionFile(file):
	pass



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('file', metavar='input file', type=str)
	parser.add_argument('--type', metavar='file type', choices=['t', 'c', 'p'], 
						default='t')
	args = parser.parse_args()

	"""
	To run the program, put a trade/cash/position file in the local directory, 
	then do:

		python henghua.py <file_name> --type <type> 

		for type, p for position file, c for cash file, t for trade file, 
		default is 't'.
	"""
	import sys
	if args.file == None:
		print('input file name is missing')
		sys.exit(1)
	elif args.type == 't':
		processTradeFile(join(get_current_path(), args.file), get_current_path())

	elif args.type == 'c':
		processCashFile(join(get_current_path(), args.file), get_current_path())
	elif args.type == 'p':
		processPositionFile(join(get_current_path(), args.file), get_current_path())