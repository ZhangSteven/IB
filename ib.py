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

class InvalidFileName(Exception):
	pass



def processCashPositionFile(file, outputDir=get_current_path()):
	"""
	[String] cash or position file => [String] output file

	Convert an IB cash or position file to cash or position file ready
	for Geneva reconciliation.
	"""
	if isCashFile(file):
		return processCashFile(file, outputDir)
	elif isPositionFile(file):
		return processPositionFile(file, outputDir)
	else:
		raise InvalidFileName(file)



def processPositionFile(file, outputDir):
	"""
	[String] file, [String] outputDir => [String] output csv file
	"""
	logger.info('processPositionFile(): {0}'.format(file))
	return writePositionFile(createPositionRecords(file), outputDir)



def processCashFile(file, outputDir):
	"""
	[String] file, [String] outputDir => [String] output csv file
	"""
	logger.info('processCashFile(): {0}'.format(file))
	return writeCashFile(createCashRecords(file), outputDir)



def isCashFile(file):
	"""
	[String] file => [Bool] yesno

	file is a full path file name.
	"""
	if 'cash' in fileNameWithoutPath(file).split('.')[0]:
		return True
	else:
		return False



def isPositionFile(file):
	"""
	[String] file => [Bool] yesno

	file is a full path file name.
	"""
	if 'position' in fileNameWithoutPath(file).split('.')[0]:
		return True
	else:
		return False



def fileNameWithoutPath(file):
	"""
	[String] file => [String] file

	C:\temp\file1.txt => file1.txt
	"""
	return file.split('\\')[-1]



def processTradeFile(file, outputDir=get_current_path()):
	"""
	[String] trade file, [String] outputDir => [List] output file names
	
	read the trade file, convert it to trade records and write it to
	a list of output csv files, to be uploaded by Bloomberg.
	"""
	logger.info('processTradeFile(): {0}'.format(file))
	return writeToFile(toRecordGroups(createTradeRecords(file)), outputDir)



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

	# Convert to integer if possible, sometimes if the quantity of a futures
	# contract is a float (like 15.0), BLoomberg may generate an error.
	if r['Quantity'].is_integer():
		r['Quantity'] = int(r['Quantity'])

	return r



def toPositionRecord(record):
	"""
	[Dictionary] record => [Dictionary] position record

	Create a new position record from the existing record, the record has 8
	fields:

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
		'VIX': ('VX', 'Index'),
		'HSI': ('HI', 'Index'),
		'MHI': ('HU', 'Index'), 	# mini Hang Seng index futures
		'DAX': ('GX', 'Index'),
		'ES' : ('ES', 'Index'),		# E-Mini S&P500 index futures
		'NQ' : ('NQ', 'Index'),		# E-Mini NASDAQ 100 index futures
		'CL' : ('CL', 'Comdty'),	# Light Sweet Crude Oil (WTI)
		'PL' : ('PL', 'Comdty'),	# Platinum futures
		'RB' : ('XB', 'Comdty'),	# Gasoline RBOB futures (NYMEX)
		'RBOB' : ('PG', 'Comdty'),	# Gasoline RBOB futures (ICE)
		'QG' : ('EO', 'Comdty'), 	# E-Mini Natural Gas futures
		'ZS' : ('S ', 'Comdty')		# Soybean
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
	if buySell == 'BUY' and ('O' in codes or 'D' in codes):
		return 'Buy'
	elif buySell == 'BUY' and 'C' in codes:
		return 'Cover'
	elif buySell == 'SELL' and 'O' in codes:
		return 'Short'
	elif buySell == 'SELL':
		return 'Sell'
	else:
		raise InvalidTradeSide('{0}, {1}'.format(buySell, code))



def stringToDate(dateString):
	"""
	[String] dateString => [datetime] date

	dateString is of format: yyyymmdd
	"""
	return datetime.datetime(int(dateString[0:4]), int(dateString[4:6]), 
								int(dateString[6:]))




# def getTradeFiles(files):
# 	"""
# 	[list] txt files => [list] trade files
# 	"""
# 	return list(filter(lambda fn: 'Trades_TradeConfirm' in fn.split('\\')[-1], files))



# def getCsvFiles(folder):
# 	"""
# 	[string] folder => [list] txt files in the folder
# 	"""
# 	from os import listdir
# 	from os.path import isfile

# 	logger.info('getCsvFiles(): folder {0}'.format(folder))

# 	def isCsvFile(file):
# 		"""
# 		[string] file name (without path) => [Bool] is it a csv file?
# 		"""
# 		return file.split('.')[-1] == 'csv'

# 	return [join(folder, f) for f in listdir(folder) \
# 			if isfile(join(folder, f)) and isCsvFile(f)]



def writeToFile(recordGroups, outputDir):
	"""
	[List] recordGroups => create output csv file(s) for each group

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
				'Price', 'TradeDate', 'SettlementDate', 'Commission Code 1',
				'Commission Amt 1']

	outputFiles = []
	for (index, group) in enumerate(recordGroups):
		file = toFileName(index, group, outputDir)
		writeCsv(file, [createCsvRow(fields, record) for record in group])
		outputFiles.append(file)

	return outputFiles



def writePositionFile(records, outputDir):
	"""
	[List] position records => [String] output csv file name

	The position file will be uploaded to Geneva for reconciliation, it 
	contains the below fields:

	Portfolio: account code in Geneva (e.g., 40006)
	Custodian: custodian bank ID
	Date: [String] yyyy-mm-dd
	Investment: identifier in Geneva
	Currency:
	Quantity:
	Date: same as Date above

	A header row is included.
	"""
	fields = ['Portfolio', 'Custodian', 'Date', 'Investment', 'Currency',
				'Quantity']

	file = toPositionFileName(outputDir, records[0]['Date'])
	writeCsv(file, createCsvRows(fields, records))

	return file



def writeCashFile(records, outputDir):
	"""
	[List] cash records => [String] output csv file name

	The cash file will be uploaded to Geneva for reconciliation, it 
	contains the below fields:

	Portfolio: account code in Geneva (e.g., 40006)
	Custodian: custodian bank ID
	Date: [String] yyyy-mm-dd
	Investment: identifier in Geneva
	Currency:
	Quantity:
	Date: same as Date above

	A header row is included.
	"""
	fields = ['Portfolio', 'Custodian', 'Date', 'Currency', 'Balance']

	file = toCashFileName(outputDir, records[0]['Date'])
	writeCsv(file, createCsvRows(fields, records))

	return file



def toFileName(index, group, outputDir):
	return join(outputDir, createTradeFileName(group[0]['TradeDate'], createSuffix(index)))



def toPositionFileName(outputDir, dt):
	"""
	[String] output dir, [datetime] dt => [String] position file name
	"""
	filename = 'IB_' + dateToString_yyyymmdd(dt) + '_position' + '.csv'
	return join(outputDir, filename)



def toCashFileName(outputDir, dt):
	"""
	[String] output dir, [datetime] dt => [String] position file name
	"""
	filename = 'IB_' + dateToString_yyyymmdd(dt) + '_cash' + '.csv'
	return join(outputDir, filename)



def createSuffix(i):
	if i == 0:
		return ''
	else:
		return '_part' + str(i+1)	# i = 1 => '_part2'



def createTradeFileName(dt, suffix=''):
	"""
	[datetime] dt => [String] full path file name of the trade file

	IB_trades_yyyy-mm-dd.csv
	"""
	return 'IB_trades_' + dateToString_yyyymmdd(dt) + suffix + '.csv'



def dateToString(dt):
	"""
	[datetime] dt => [String] mm/dd/yy

	This format is required by Bloomberg trade upload
	"""
	return str(dt.month) + '/' + str(dt.day) + '/' + str(dt.year)[2:]



def dateToString_yyyymmdd(dt):
	"""
	[datetime] dt => [String] yyyy-mm-dd

	This format is required by Geneva cash or position reconciliation
	"""
	return str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day)



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



def createCsvRows(fields, records):
	"""
	[List] fields, [List] position or cash records => [List] rows in csv
	
	The first row is the headers (fields)
	"""
	def fieldToColumn(field, record):
		if field == 'Portfolio':
			return 'TEST6'
		elif field == 'Custodian':
			return 'IB'

		elif field == 'Investment':	# for position record
			if record['BloombergTicker'].endswith(' Equity'):
				return record['BloombergTicker'][:-7]	# strip off ' Equity'
			else:
				return record['BloombergTicker']

		elif field == 'Balance':	# for cash record
			return record['Quantity']
		
		elif field == 'Date':
			return dateToString_yyyymmdd(record['Date'])
		else:
			return record[field]


	def recordToRow(record):
		return [fieldToColumn(field, record) for field in fields]


	rows = [fields]
	rows.extend([recordToRow(record) for record in records])
	return rows



def toRecordGroups(records):
	"""
	[List] records => [List] of [List] records

	If trades of opposite directions on the same futures contract appear, say 
	"buy 5 HIX8", followed by "sell 2 HIX8". It is legal but Bloomberg will 
	consider these two trades form a box position, if there is no long positions 
	on HIX8 before the buy trade.

	To avoid this problem, when the opening and closing trades for same futures
	contract appear, we split them into two files.

	For example, we have the following trades:

	Trade 			Type
	Buy 5 HIX8		Open
	Sell 5 HIX8		Close
	Short 10 HIX8	Open
	Cover 10 HIX8	Close

	Then it's divided into 4 groups of trades, each with consistent types within
	the group, open, close, open, close.

	Then we upload the 4 files one by one, we won't see the box position problem.
	"""
	recordGroups = []
	remaining = records
	
	while (remaining != []):
		group, remaining = splitTrades(remaining)
		recordGroups.append(group)

	return recordGroups



def splitTrades(records):
	"""
	[List] records => [List] group, [List] remaining
	
	Split the list of records into lists, where in list1 none of the trades
	form a box position (have same underlying but of different direction).
	"""
	group = []
	for i in range(len(records)):
		if formBoxPosition(records[i], group):
			break
		else:
			group.append(records[i])

	if formBoxPosition(records[i], group):
		return group, records[i:]
	else:	# must be i = len(records) - 1 and no box position
		return group, []



def formBoxPosition(record, group):
	"""
	[Dictionary] record, [List] group => [Bool] whether the record forms a 
		box position with any record in the group

	A box position means two trades of the same ticker, but of different
	directions. There are two possibilities:

	1. One trade is on the long side (Buy, Cover) and the other is on the
		short side (Sell, Short).

	2. Both trades are on the same side, but of different type. For example,
		Cover, then Buy.

	If case (1), then obviously it will form a box position by. If in case (2),
	say it is "Cover" then "Buy", Bloomberg will still complain. Because
	there is an existing "Short" position, the "Buy" will form a box position
	with that existing short positions.

	Therefore, when two trades on the same ticker appear, as long as they are
	of different trade type, a box postion will occur.
	"""
	for r in group:
		if record['BloombergTicker'] == r['BloombergTicker'] and record['Side'] != r['Side']:
			return True

	return False



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

		python ib.py <file_name> --type c (p for position file 
										  , c for cash file
										  , t for trade file
										  , default is 't')
	"""
	import sys
	if args.file == None:
		print('input file name is missing')
		sys.exit(1)
	elif args.type == 't':
		processTradeFile(join(get_current_path(), args.file))
	elif args.type == 'c':
		processCashFile(join(get_current_path(), args.file), get_current_path())
	elif args.type == 'p':
		processPositionFile(join(get_current_path(), args.file), get_current_path())