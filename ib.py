# coding=utf-8
# 
# Convert files from InteractiveBrokers to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#


from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class UnhandledTradeType(Exception):
	pass

class InvalidSymbol(Exception):
	pass

class InvalidBuySell(Exception):
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
	r['Side'] = createSide(record['Buy/Sell'])
	r['Quantity'] = abs(float(record['Quantity']))
	r['Price'] = float(record['Price'])
	r['TradeDate'] = stringToDate(record['TradeDate'])
	if record['AssetClass'] == 'FUT':
		r['SettlementDate'] = r['TradeDate']
	else:
		raise UnhandledTradeType('invalid type {0} in {1}'.format(record['AssetClass'], r))

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



def createSide(buySell):
	"""
	[String] buySell => [String] longShort
	"""
	if buySell == 'BUY':
		return 'Buy'
	elif buySell == 'SELL':
		return 'Sell'
	else:
		raise InvalidBuySell(buySell)



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




if __name__ == '__main__':
	from IB.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)



	