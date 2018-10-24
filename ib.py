# coding=utf-8
# 
# Convert files from InteractiveBrokers to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from utils.utility import writeCsv
from IB.utility import get_current_path
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class UnhandledTradeType(Exception):
	pass

class InvalidSymbol(Exception):
	pass

class InvalidTradeSide(Exception):
	pass

class TradeFileNotFound(Exception):
	pass



def createTradeRecords(directory):
	"""
	[String] directory => [List] trade records
	"""
	tradeFiles = getTradeFiles(getCsvFiles(directory))
	if len(tradeFiles) == 0:
		raise TradeFileNotFound('in directory {0}'.format(directory))
	else:
		return list(map(toTradeRecord, fileToRecords(tradeFiles[0])))



def fileToRecords(file):
	"""
	[String] file => [List] records

	Convert a csv file to a list of records, where each record is a dictionary,
	of type OrderedDict. The first row of the csv file is used as dictionary keys.
	"""
	with open(file, newline='') as csvfile:
		reader = csv.DictReader(csvfile)
		return [row for row in reader]



def toTradeRecord(record):
	"""
	[Dictionary] record => [Dictionary] tradeRecord

	So far, this function works only if the trade type is futures.

	Create a new trade record from the existing record, the trade record has 6
	fields:

	1. BloombergTicker
	2. Side
	3. Quantity
	4. Price
	5. TradeDate: of type datetime
	6. SettlementDate: of type datetime
	"""
	r = {}
	r['BloombergTicker'] = createTicker(record)
	r['Side'] = createSide(record['Buy/Sell'], record['Code'])
	r['Quantity'] = abs(float(record['Quantity']))
	r['Price'] = float(record['Price'])
	r['TradeDate'] = stringToDate(record['TradeDate'])
	if record['AssetClass'] == 'FUT':
		r['SettlementDate'] = r['TradeDate']
	else:
		raise UnhandledTradeType('invalid type {0} in {1}'.format(record['AssetClass'], r))

	# Convert to integer if possible, sometimes if the quantity of a futures
	# contract is a float (like 15.0), BLoomberg may generate an error.
	if r['Quantity'].is_integer():
		r['Quantity'] = int(r['Quantity'])

	return r



def createTicker(record):
	"""
	[Dictionary] record => [String] ticker

	Create a Bloomberg ticker based on the record. It only works for certain
	futures type now.
	"""
	if record['AssetClass'] != 'FUT':
		raise UnhandledTradeType('invalid type {0} in {1}'.format(record['AssetClass'], r))
	
	bMap = {	# mapping underlying to Bloombert Ticker's first 2 letters,
				# and index or comdty
		'VIX': ('VX', 'Index'),
		'HSI': ('HI', 'Index'),
		'DAX': ('GX', 'Index'),
		'ES' : ('ES', 'Index'),		# E-Mini S&P500 index futures
		'CL' : ('CL', 'Comdty'),	# Light Sweet Crude Oil (WTI)
		'ZS' : ('S ', 'Comdty')		# Soybean
	}

	mMap = {	# mapping month to Bloomberg Ticker's 3rd letter
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
	prefix, suffix = bMap[record['UnderlyingSymbol']]
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
	if buySell == 'BUY' and 'O' in codes:
		return 'Buy'
	elif buySell == 'BUY' and 'C' in codes:
		return 'Cover'
	elif buySell == 'SELL' and 'O' in codes:
		return 'Short'
	elif buySell == 'SELL' and 'C' in codes:
		return 'Sell'
	else:
		raise InvalidTradeSide(buySell)



def stringToDate(dateString):
	"""
	[String] dateString => [datetime] date

	dateString is of format: yyyymmdd
	"""
	return datetime.datetime(int(dateString[0:4]), int(dateString[4:6]), 
								int(dateString[6:]))




def getTradeFiles(files):
	"""
	[list] txt files => [list] trade files
	"""
	return list(filter(lambda fn: 'Trades_TradeConfirm' in fn.split('\\')[-1], files))



def getCsvFiles(folder):
	"""
	[string] folder => [list] txt files in the folder
	"""
	from os import listdir
	from os.path import isfile

	logger.info('getCsvFiles(): folder {0}'.format(folder))

	def isCsvFile(file):
		"""
		[string] file name (without path) => [Bool] is it a csv file?
		"""
		return file.split('.')[-1] == 'csv'

	return [join(folder, f) for f in listdir(folder) \
			if isfile(join(folder, f)) and isCsvFile(f)]



def writeTradeRecords(records):
	"""
	[List] records => create a output csv file for trades

	The trade file will be uploaded to Bloomberg, it contains the below
	fields:

	Account: account code in AIM (e.g., 40006)
	Security: Bloomberg Ticker
	Broker: Broker code (e.g., IB-QUANT)
	Side: Buy/Cover, Sell/Short
	Quantity: 
	Price:
	Trade Date: [String] mm/dd/yy
	Settlement Date: same format as Trade Date

	No header row is required.
	"""
	fields = ['Account', 'BloombergTicker', 'Broker', 'Side', 'Quantity', 
				'Price', 'TradeDate', 'SettlementDate']
	file = join(get_current_path(), createTradeFileName(records[0]['TradeDate']))
	writeCsv(file, [createCsvRow(fields, record) for record in records])



def createTradeFileName(dt):
	"""
	[datetime] dt => [String] full path file name of the trade file

	IB_trades_yyyy-mm-dd.csv
	"""
	return 'IB_trades_' + str(dt.year) + '-' + str(dt.month) + '-' + \
			str(dt.day) +'.csv'



def dateToString(dt):
	"""
	[datetime] dt => [String] mm/dd/yy
	"""
	return str(dt.month) + '/' + str(dt.day) + '/' + str(dt.year)[2:]



def createCsvRow(fields, record):
	"""
	[List] fields, [Dictionary] trade record => [List] String items in a row
	"""
	def fieldToRow(field):
		if field == 'Account':
			return 'TEST6'
		elif field == 'Broker':
			return 'IB-QUANT'
		elif field in ['TradeDate', 'SettlementDate']:
			return dateToString(record[field])
		else:
			return record[field]

	return list(map(fieldToRow, fields))



def splitRecords(records):
	"""
	[List] records => [List] records1, [List] records2

	If records contains both opening and closing trades on the same futures
	contract, say "buy 5 HIX8", followed by "sell 2 HIX8". It is legal but
	Bloomberg will consider these two trades form a box position, if there is
	no long positions on HIX8 before the buy trade.

	To avoid this problem, when the opening and closing trades for same futures
	contract appear, we split them into two files.
	"""
	pass


if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	writeTradeRecords(createTradeRecords(join(get_current_path(), 'samples')))

	