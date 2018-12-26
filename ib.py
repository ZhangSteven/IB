# coding=utf-8
# 
# Convert files from InteractiveBrokers to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from utils.utility import writeCsv
from IB.utility import get_current_path, toRecordGroups, writeToFile, \
						writeCashFile, writePositionFile, toOpenCloseGroup
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class UnhandledTradeType(Exception):
	pass

class InvalidSymbol(Exception):
	pass

class InvalidTradeSide(Exception):
	pass

class InvalidFileName(Exception):
    pass



def processCashPositionFile(file, outputDir=get_current_path()):
    """
    [String] cash or position file => [String] output file

    Convert an IB cash or position file to cash or position file ready
    for Geneva reconciliation.

    The rule is: cash file name always starts with 'cash', position file
    name always starts with 'position'.
    """
    if isCashFile(file):
        return processCashFile(file, outputDir)
    elif isPositionFile(file):
        return processPositionFile(file, outputDir)
    else:
        raise InvalidFileName(file)



def isCashFile(fn):
	"""
	[String] file name => [Bool] is this a cash file
	"""
	tokens = fn.split('.')
	if len(tokens) > 2 and tokens[2] == 'cash':
		return True 

	return False



def isPositionFile(fn):
	"""
	[String] file name => [Bool] is this a position file
	"""
	tokens = fn.split('.')
	if len(tokens) > 2 and tokens[2] == 'position':
		return True 

	return False



def processPositionFile(file, outputDir):
	"""
	[String] file, [String] outputDir => [String] output csv file

	if there are no records, i.e., no content to write, no csv file
	is written and return value will be empty string.
	"""
	logger.info('processPositionFile(): {0}'.format(file))
	records = createPositionRecords(file)
	if len(records) > 0:
		return writePositionFile('40006-B', records, outputDir)
	else:
		return ''



def processCashFile(file, outputDir):
	"""
	[String] file, [String] outputDir => [String] output csv file
	"""
	logger.info('processCashFile(): {0}'.format(file))
	records = createCashRecords(file)
	if len(records) > 0:
		return writeCashFile('40006-B', records, outputDir)
	else:
		return ''



def processTradeFile(file, outputDir=get_current_path()):
	"""
	[String] trade file, [String] outputDir => [List] output file names
	
	read the trade file, convert it to trade records and write it to
	a list of output csv files, to be uploaded by Bloomberg.
	"""
	logger.info('processTradeFile(): {0}'.format(file))
	# return writeToFile(
	# 			toRecordGroups(
	# 				createTradeRecords(file)
	# 			)
	# 			, outputDir
	# 			, '40006-B'
	# 			, 'IB-QUANT'
	# 		)

	return writeToFile(
				toOpenCloseGroup(
					createTradeRecords(file)
				)
				, outputDir
				# , 'TEST6D'
				# , 'BB'
				, '40006-B'
				, 'IB-QUANT'
			)



def createPositionRecords(file):
	"""
	[String] file => [List] position records
	"""
	return list(map(toPositionRecord, fileToRecords(file)))



def createCashRecords(file):
	"""
	[String] file => [List] cash records
	"""
	return list(filter(lambda r: r != None, map(toCashRecord, fileToRecords(file))))



def createTradeRecords(file):
	"""
	[String] file => [List] trade records
	"""
	return list(map(toTradeRecord, toSortedRecords(fileToRecords(file))))



def fileToRecords(file):
	"""
	[String] file => [List] records

	Convert a csv file to a list of records, where each record is a dictionary,
	of type OrderedDict. The first row of the csv file is used as dictionary keys.
	"""
	with open(file, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		return [row for row in reader]



def toSortedRecords(records):
	"""
	[List] records => [List] new records

	Create a new list of records, the only difference is, the new list is sorted
	by 'Date/Time' (execution time), from earliest to latest. If two records
	have the same execution time, their order in the original list is preserved,
	i.e., whichever comes first in the original list comes first in the softed
	list.
	"""
	def takeRankDateTime(record):
		return record['RankDateTime']

	return sorted(toNewRecords(records), key=takeRankDateTime)



def toNewRecords(records):
	"""
	[List] records => [List] new records

	Map the record list to new reccord list, but for each record, the new record
	has an extra field 'RankDateTime', as a tuple (rank, datetime).
	"""
	newRecords = []
	for i in range(len(records)):
		newRecord = duplicateRecord(records[i])
		newRecord['RankDateTime'] = (toDateTime(newRecord['Date/Time']), i)
		newRecords.append(newRecord)

	return newRecords



def duplicateRecord(record):
	"""
	[Dictionary] record => [Dictionary] new record

	Duplicate the record to a new record.
	"""
	newRecord = {}
	for key in record:
		newRecord[key] = record[key]

	return newRecord



def toDateTime(dtString):
	"""
	[String] dtString => [datetime] datetime

	dtString is a string of format "yyyymmdd;hhmmss", convert it to a datetime
	object.
	"""
	dateString, hourString = dtString.split(';')
	return datetime.datetime(int(dateString[0:4]), int(dateString[4:6]), int(dateString[6:]),
							int(hourString[0:2]), int(hourString[2:4]), int(hourString[4:]))



def toTradeRecord(record):
	"""
	[Dictionary] record => [Dictionary] tradeRecord

	Create a new trade record from the existing record, the trade record has 8
	fields:

	1. BloombergTicker
	2. Side
	3. Quantity
	4. Price
	5. TradeDate: of type datetime
	6. SettlementDate: of type datetime
	7. Commission Code 1: fixed to 'Broker Commission'
	8. Commission Amt 1: total commission
	9. Strategy: strategy of the trade
	"""
	r = {}
	r['BloombergTicker'] = createTicker(record)
	r['Side'] = createSide(record['Buy/Sell'], record['Code'])
	r['Quantity'] = abs(float(record['Quantity']))
	r['Price'] = float(record['Price'])
	r['TradeDate'] = stringToDate(record['TradeDate'])
	if record['AssetClass'] == 'FUT':
		r['SettlementDate'] = r['TradeDate']
	elif record['AssetClass'] == 'STK':
		r['SettlementDate'] = stringToDate(record['SettleDate'])
	else:
		raise UnhandledTradeType('invalid type {0} in {1}'.format(record['AssetClass'], r))

	# check Bloomberg 'CFTK' page for all possible commission codes
	# here we simply put the sum of all commissions, tax, exchange fees
	# under the name of 'Broker Commission'
	r['Commission Code 1'] = 'Broker Commission'
	r['Commission Amt 1'] = abs(float(record['Commission']))
	r['Strategy'] = 'TRADING'

	# Convert to integer if possible, sometimes if the quantity of a futures
	# contract is a float (like 15.0), BLoomberg may generate an error.
	if r['Quantity'].is_integer():
		r['Quantity'] = int(r['Quantity'])

	return r



def toPositionRecord(record):
	"""
	[Dictionary] record => [Dictionary] position record

	Create a new position record from the existing record, the record has the
	below fields:

	1. BloombergTicker:
	2. Quantity: float number, use negative to indicate short position
	3. Currency
	4. Date: of type datetime
	"""
	r = {}
	r['BloombergTicker'] = createTicker(record)
	r['Quantity'] = float(record['Quantity'])
	r['Currency'] = record['CurrencyPrimary']
	r['Date'] = stringToDate(record['ReportDate'])
	return r



def toCashRecord(record):
	"""
	[Dictionary] record => [Dictionary] cash record

	Create a new cash record from the existing record, the record has 3
	fields:

	1. Currency:
	2. Quantity: must be positive
	3. Date: of type datetime
	"""
	if record['CurrencyPrimary'] == 'BASE_SUMMARY':
		return None

	r = {}
	r['Quantity'] = float(record['EndingSettledCash'])
	r['Currency'] = record['CurrencyPrimary']
	r['Date'] = stringToDate(record['ToDate'])
	return r



def createTicker(record):
	"""
	[Dictionary] record => [String] ticker

	Create a Bloomberg ticker based on the record. It only works for certain
	futures type now.
	"""
	if record['AssetClass'] == 'STK' and record['CurrencyPrimary'] == 'USD' and \
		record['Symbol'] == 'SPY':

		return 'SPY US Equity'
	elif record['AssetClass'] == 'FUT':
		return createFuturesTicker(record)
	else:
		raise UnhandledTradeType('record: {0}'.format(record))



def createFuturesTicker(record):
	"""
	[Dictionary] record => [String] ticker

	Create a Bloomberg ticker for record of futures type.
	"""
	bMap = {	# mapping underlying to Bloombert Ticker's first 2 letters,
				# and index or comdty
		('HSI', 50): ('HI', 'Index'),
		('MHI', 10): ('HU', 'Index'), 		# mini Hang Seng index futures
		('DAX', 25): ('GX', 'Index'),		# DAX index futures
		('DAX',  5): ('DFW', 'Index'),		# mini DAX index
		('ES' , 50): ('ES', 'Index'),		# E-Mini S&P500 index futures
		('NQ' , 20): ('NQ', 'Index'),		# E-Mini NASDAQ 100 index futures
		('CL' , 1000): ('CL', 'Comdty'),	# Light Sweet Crude Oil (WTI)
		('PL' , 50): ('PL', 'Comdty'),		# Platinum futures
		('RB' , 420): ('XB', 'Comdty'),		# Gasoline RBOB futures (NYMEX)
		('RBOB',420) : ('PG', 'Comdty'),	# Gasoline RBOB futures (ICE)
		('QG' , 2500) : ('EO', 'Comdty'), 	# E-Mini Natural Gas futures
		('ZS' , 50) : ('S ', 'Comdty'),		# Soybean
		('GC' , 100): ('GC', 'Comdty')		# Gold
	}

	mMap = {	# mapping month to Bloomberg Ticker's 3rd letter
				# for futures contract
		'JAN': 'F',
		'FEB': 'G',
		'MAR': 'H',
		'APR': 'J',
		'MAY': 'K',
		'JUN': 'M',
		'JUL': 'N',
		'AUG': 'Q',
		'SEP': 'U',
		'OCT': 'V',
		'NOV': 'X',
		'DEC': 'Z'
	}

	month, year = getMonthYear(record['Description'])
	prefix, suffix = bMap[(record['UnderlyingSymbol'], int(record['Multiplier']))]
	return prefix + mMap[month] + year[1] + ' ' + suffix

	

def getMonthYear(description):
	"""
	[String] description => [String] Month, [String] year (two digit)
	
	description string looks like: VIX 16JAN13 (16 is date, 13 is year), for
	such a description, we want to return 'JAN', '13'
	"""
	dateString = description.split()[1]
	return dateString[-5:-2], dateString[-2:]



def createSide(buySell, code):
	"""
	[String] buySell, [String] execution code => [String] Buy/Cover/Sell/Short

	Map IB buy sell trades with execution code to Bloomberg trade side.
	
	code is a ; separated list of execution types, for example "C;P" means
	closing trade, partial execution
	Mapping rules:

	buy, opening trade (O) => Buy
	buy, closing trade (C) => Cover
	sell,opening trade (O) => Short
	sell,closing trade (C) => Sell
	"""
	codes = code.split(';')
	# if buySell == 'BUY' and ('O' in codes or 'D' in codes):
	# 	return 'Buy'
	# elif buySell == 'BUY' and 'C' in codes:
	# 	return 'Cover'
	# elif buySell == 'SELL' and 'O' in codes:
	# 	return 'Short'
	# elif buySell == 'SELL':
	# 	return 'Sell'
	# else:
	# 	raise InvalidTradeSide('{0}, {1}'.format(buySell, code))

	c_map = {
		'BUY' : 'Buy',
		'SELL': 'Sell'
	}

	if buySell == 'BUY' and 'C' in codes:
		return 'Cover'
	elif buySell == 'SELL' and 'O' in codes:
		return 'Short'
	else:
		return c_map[buySell]



def stringToDate(dateString):
	"""
	[String] dateString => [datetime] date

	dateString is of format: yyyymmdd
	"""
	return datetime.datetime(int(dateString[0:4]), int(dateString[4:6]), 
								int(dateString[6:]))




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('file', metavar='input file', type=str)
	parser.add_argument('--type', metavar='file type', choices=['t', 'pc'], 
						default='pc')
	args = parser.parse_args()

	"""
	To run the program, put a trade/cash/position file in the local directory, 
	then do:

		python ib.py <file_name> --type c (t for trade file
                                          , pc for position or trade file
										  , default is 'pc')
	"""
	import sys
	if args.file == None:
		print('input file name is missing')
		sys.exit(1)
	elif args.type == 't':
		processTradeFile(join(get_current_path(), args.file))
	else:
		processCashPositionFile(join(get_current_path(), args.file), get_current_path())