# coding=utf-8
# 
# Convert files from InteractiveBrokers to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from utils.utility import writeCsv
from IB.utility import get_current_path, writeTradeFiles, writeCashFile, \
						writePositionFile, toOpenCloseGroup, fileNameWithoutPath
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class UnhandledTradeType(Exception):
	pass

class InvalidSymbol(Exception):
	pass

class InvalidTradeSide(Exception):
	pass



def processCashPositionFile(file, outputDir=get_current_path()):
    """
    [String] cash or position file => [String] output file

    Convert an IB cash or position file to cash or position file ready
    for Geneva reconciliation.

    The rule is: cash file name always starts with 'cash', position file
    name always starts with 'position'.
    """
    logger.info('processCashPositionFile(): {0}'.format(file))
    if isCashFile(file):
        return writeCashFile('40006-B', createCashRecords(file), 
        							outputDir, getDateFromFilename(file))
    elif isPositionFile(file):
        return writePositionFile('40006-B', createPositionRecords(file), 
        							outputDir, getDateFromFilename(file))
    else:
        logger.debug('processCashPositionFile(): not a cash or position file: \
                        {0}'.format(file))
        return ''



def isCashOrPositionFile(file):
	"""
	[String] full path file name => [Bool] is this a cash or position file
	"""
	return isCashFile(file) or isPositionFile(file)



def isCashFile(file):
	"""
	[String] full path file name => [Bool] is this a cash file
	"""
	tokens = fileNameWithoutPath(file).split('.')
	if len(tokens) > 2 and tokens[2] == 'cash':
		return True 

	return False



def isPositionFile(file):
	"""
	[String] full path file name => [Bool] is this a position file
	"""
	tokens = fileNameWithoutPath(file).split('.')
	if len(tokens) > 2 and tokens[2] == 'position':
		return True 

	return False



def processTradeFile(file, outputDir=get_current_path()):
	"""
	[String] trade file, [String] outputDir => [List] output file names
	
	read the trade file, convert it to trade records and write it to
	a list of output csv files, to be uploaded by Bloomberg.
	"""
	logger.info('processTradeFile(): {0}'.format(file))

	return writeTradeFiles(
				toOpenCloseGroup(
					createTradeRecords(file)
				)
				, outputDir
				# , 'TEST6D'
				# , 'BB'
				, '40006-B'
				, 'IB-QUANT'
                , getDateFromFilename(file)
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
	[String] file => [Iterable] trade records
	"""
	return map(toNewTradePrice
			  , map(toTradeRecord, 
					toSortedRecords(
						filter(lambda r: r['AssetClass'] in ['FUT', 'STK']
							  , fileToRecords(file)
						))))



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
	[Iterable] records => [List] new records

	sorted the records by 'Date/Time' (execution time), from earliest to latest. 
	If two records have the same execution time, their order in the original list 
	is preserved,i.e., whichever comes first in the original list comes first in 
	the softed list.
	"""
	def takeRankDateTime(record):
		return record['RankDateTime']


	def toNewRecord(recordWithIndex):
		i, record = recordWithIndex
		r = duplicateRecord(record)
		r['RankDateTime'] = (toDateTime(record['Date/Time']), i)
		return r


	return sorted(
				map(toNewRecord, enumerate(records))
				, key=takeRankDateTime)



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



def toNewTradePrice(record):
	"""
	[Dict] record => [Dict] new record

	Sometimes, IB's multipler is different from Bloomberg's, therefore IB's price
	is different from the price to upload to Bloomberg AIM. For example, soybean
	futures, IB provides a price of 8.8543 with a multipler of 5000, however 
	Bloomberg has a multipler of 50, so the price to upload to AIM should be 
	times 100, which is 885.43.
	"""
	def recordType(ticker):
		"""
		Find out the type of the item in the trade record, for example, it is
		'S F9 Comdty', then return ('S ', 'Comdty'), so that we know it is
		Soybean commodity futures.
		"""
		tokens = ticker.split()
		sector = tokens[-1]
		return (ticker[0:2], sector)

	# The factor to multiply to IB price to become Bloomberg price
	f_map = {
		('XB', 'Comdty'): 100,	# IB multipler 42000, Bloomberg multipler 420
		('PG', 'Comdty'): 100,	# IB multipler 42000, Bloomberg multipler 420
		('S ', 'Comdty'): 100	# IB multipler 5000, Bloomberg multipler 50
	}

	r = duplicateRecord(record)
	try:
		factor = f_map[recordType(record['BloombergTicker'])]
		r['Price'] = factor * record['Price']
	except:
		pass 	# no adjustment

	return r



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
	r['SettlementDate'] = stringToDate(record['SettleDate'])

	# check Bloomberg 'CFTK' page for all possible commission codes
	# here we simply put the sum of all commissions, tax, exchange fees
	# under the name of 'Broker Commission'
	r['Commission Code 1'] = 'Broker Commission'
	r['Commission Amt 1'] = abs(float(record['Commission']))

	# in our AIM configuration, there must be a 'Strategy' tag for each trade,
	# so we just put TRADING as the default tag for all trades in IB.
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
		('RB' , 42000): ('XB', 'Comdty'),	# Gasoline RBOB futures (NYMEX)
		('RBOB',42000): ('PG', 'Comdty'),	# Gasoline RBOB futures (ICE)
		('QG' , 2500) : ('EO', 'Comdty'), 	# E-Mini Natural Gas futures
		('ZS' , 5000) : ('S ', 'Comdty'),	# Soybean
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



def getDateFromFilename(file):
    """
    [String] file (full path) => [Datetime] date

    The IB file name has a pattern: flex.<digits>.trade/cash/position.<date>.<date>.csv
    The two dates are usually the same, of the form "yyyymmdd", retrieve it and
    convert it to Datetime format.
    """
    # print(file)
    return stringToDate(file.split('\\')[-1].split('.')[3])




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