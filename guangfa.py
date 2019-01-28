# coding=utf-8
# 
# Convert files from GuangFa broker to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from utils.utility import writeCsv
from IB.utility import get_current_path, writeTradeFiles, writeCashFile, \
						writePositionFile, toOpenCloseGroup
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)



class InvalidTradeSide(Exception):
	pass



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



def createTradeRecords(file):
	"""
	[String] file => [Iterable] trade records
	"""
	# return map(toNewTradePrice
	# 		  , map(toTradeRecord, 
	# 				toSortedRecords(
	# 					filter(lambda r: r['AssetClass'] in ['FUT', 'STK']
	# 						  , fileToRecords(file)
	# 					))))

	return map(tradeRecord, fileToRecords(file))



def tradeRecord(fileRecord):
	"""
	[Dict] fileRecord => [Dict] trade record

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
	r['BloombergTicker'] = createTicker(fileRecord)
	r['Side'] = createSide(fileRecord)
	r['Quantity'] = max(toFloat(fileRecord['BuyQuantity']), toFloat(fileRecord['SellQuantity']))
	r['Price'] = toFloat(fileRecord['Price'])
	r['TradeDate'] = stringToDate(fileRecord['TradeDate'])
	r['SettlementDate'] = stringToDate(fileRecord['SettlementDate'])
	r['Commission Code 1'] = 'Broker Commission'
	r['Commission Amt 1'] = toFloat(fileRecord['Commission'])
	r['Strategy'] = 'TRADING'

	# Convert to integer if possible, sometimes if the quantity of a futures
	# contract is a float (like 15.0), BLoomberg may generate an error.
	if r['Quantity'].is_integer():
		r['Quantity'] = int(r['Quantity'])

	return r



def fileToRecords(file):
	"""
	[String] file => [List] records

	Convert a csv file to a list of records, where each record is a dictionary,
	of type OrderedDict. The first row of the csv file is used as dictionary keys.
	"""
	headers = ['SettlementDate', 'TradeDate', 'MaturityDate', 'AccountNo', 
				'AccountOpeningNo', 'TradeSerialNo', 'Currency', 'Exchange',
				'Item', 'Contract', 'OpenClose', 'BuyQuantity', 'SellQuantity',
				'Price', 'Amount', 'Time', 'Commission', 'Premium', 'OptionType',
				'ExercisePrice', 'UpstreamCode', 'InlandAccountNo']
	with open(file, newline='') as csvfile:
		reader = csv.DictReader(csvfile, fieldnames=headers, delimiter='@')
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



def createTicker(fileRecord):
	"""
	[Dictionary] record => [String] ticker

	Create a Bloomberg ticker based on the record. It only works for certain
	futures type now.
	"""
	return createFuturesTicker(fileRecord)



def createFuturesTicker(fileRecord):
	"""
	[Dictionary] fileRecord => [String] ticker

	Create a Bloomberg ticker for a record from the file.
	"""
	bMap = {	# mapping underlying to Bloombert Ticker's first 2 letters,
				# and index or comdty
		('SM', 'CBOT'): ('SM', 'Comdty'),	# Soybean Meal
		('WH', 'CBOT'): ('W ', 'Comdty'), 	# Wheat
		('SO', 'CBOT'): ('S ', 'Comdty'),	# Soybean
		('HO', 'NYMEX'):('HO', 'Comdty'), 	# Ultra-low Sulfur Diesel Fuel
		('RB', 'NYMEX'):('XB', 'Comdty'), 	# RBOB Gasoline
		('CL', 'NYMEX'):('CL', 'Comdty'),	# Light Weight Crude Oil (WTI)
		('BR', 'IPE') : ('CO', 'Comdty'),	# Brent Crude Oil
		('NG', 'CME'):('NG', 'Comdty'),	# Natural Gas
		('GC', 'COMEX'):('GC', 'Comdty') 	# Gold
	}

	mMap = {	# mapping month to Bloomberg Ticker's 3rd letter
				# for futures contract
		1: 'F',
		2: 'G',
		3: 'H',
		4: 'J',
		5: 'K',
		6: 'M',
		7: 'N',
		8: 'Q',
		9: 'U',
		10: 'V',
		11: 'X',
		12: 'Z'
	}

	prefix, suffix = bMap[(fileRecord['Item'], fileRecord['Exchange'])]
	month = mMap[int(fileRecord['Contract'][-2:])]
	year = fileRecord['Contract'][-4:-2]
	
	if (prefix, suffix) == ('NG', 'Comdty'):	# use two digits for year
		return prefix + month + year + ' ' + suffix
	else:
		return prefix + month + year[1] + ' ' + suffix



def createSide(fileRecord):
	"""
	[Dict] fileRecord => [String] Buy/Cover/Sell/Short

	Mapping rules:

	buy quantity > 0, opening trade (O) => Buy
	sell quantity > 0, opening trade (O) => Short
	buy quantity > 0, closing trade (L) => Cover
	sell quantity > 0, closing trade (L) => Sell
	"""
	if fileRecord['OpenClose'] == 'O' and int(fileRecord['BuyQuantity']) > 0:
		return 'Buy'
	elif fileRecord['OpenClose'] == 'O' and int(fileRecord['SellQuantity']) > 0:
		return 'Short'
	elif fileRecord['OpenClose'] == 'L' and int(fileRecord['BuyQuantity']) > 0:
		return 'Cover'
	elif fileRecord['OpenClose'] == 'L' and int(fileRecord['SellQuantity']) > 0:
		return 'Sell'
	else:
		logger.error('createSide(): error: {0}, {1}, {2}, {3}'
						.format(fileRecord['Contract'], fileRecord['OpenClose'],
								fileRecord['BuyQuantity'], fileRecord['SellQuantity']))
		raise InvalidTradeSide()



def toFloat(data):
	"""
	[String] data => [Float] data

	data is like: 1,440.45 or 96600.00 (there may be a comma)
	"""
	return float(''.join(filter(lambda x: x != ',', data)))



def stringToDate(dateString):
	"""
	[String] dateString => [datetime] date

	dateString is of format: yyyy-mm-dd
	"""
	tokens = dateString.split('-')
	return datetime.datetime(int(tokens[0]), int(tokens[1]), int(tokens[2]))



def getDateFromFilename(file):
    """
    [String] file (full path) => [Datetime] date

    The Guangfa file name has a pattern: flex.<digits>.trade/cash/position.<date>.<date>.csv
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
		# processTradeFile(join(get_current_path(), args.file))
		print(list(createTradeRecords(join(get_current_path(), args.file))))
	else:
		pass
	# else:
	# 	processCashPositionFile(join(get_current_path(), args.file), get_current_path())