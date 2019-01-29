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



# def processCashPositionFile(file, outputDir=get_current_path()):
#     """
#     [String] cash or position file => [String] output file

#     Convert an GuangFa cash or position file to cash or position file ready
#     for Geneva reconciliation.
#     """
#     if isCashFile(file):
#         return processCashFile(file, outputDir)
#     elif isPositionFile(file):
#         return processPositionFile(file, outputDir)
#     else:
#         raise InvalidFileName(file)



# def isCashFile(fn):
# 	"""
# 	[String] file name => [Bool] is this a cash file
# 	"""
# 	if 'cusfund_' in fn.split('\\')[-1]:
# 		return True 

# 	return False



# def isPositionFile(fn):
# 	"""
# 	[String] file name => [Bool] is this a position file
# 	"""
# 	if 'holddata_' in fn.split('\\')[-1]:
# 		return True 

# 	return False
	


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
				, '40006-D'
				, 'GF-QUANT'
                , getDateFromFilename(file)
			)



def createTradeRecords(file):
	"""
	[String] file => [Iterable] trade records
	"""
	return toSortedRecords(map(tradeRecord, fileToRecords(file)))



def tradeRecord(fileRecord):
	"""
	[Dict] fileRecord => [Dict] trade record

	Create a new trade record from the existing record, the below fields are
	necessary to create Bloomberg upload file.

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

	r['Datetime'] = createDatetime(fileRecord['TradeDate'], fileRecord['Time'])

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

	Sort the records by 'Datetime' field. If two records have the same 
	'Datetime', then their order in the original list is preserved,i.e., 
	whichever comes first in the original list comes first in  the softed list.
	"""
	def byDateTime(recordWithOrder):
		order, record = recordWithOrder
		return (record['Datetime'], order)


	return map(lambda x: x[1], sorted(enumerate(records), key=byDateTime))




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
		('HSI', 'HKFE'):('HI', 'Index'),	# Hang Seng Index
		('MHU', 'HKFE'):('HU', 'Index'),	# mini Hang Seng Index
		('SM', 'CBOT'): ('SM', 'Comdty'),	# Soybean Meal
		('WH', 'CBOT'): ('W ', 'Comdty'), 	# Wheat
		('SO', 'CBOT'): ('S ', 'Comdty'),	# Soybean
		('HO', 'NYMEX'):('HO', 'Comdty'), 	# Ultra-low Sulfur Diesel Fuel
		('RB', 'NYMEX'):('XB', 'Comdty'), 	# RBOB Gasoline
		('CL', 'NYMEX'):('CL', 'Comdty'),	# Light Weight Crude Oil (WTI)
		('BR', 'IPE') : ('CO', 'Comdty'),	# Brent Crude Oil
		('NG', 'CME') : ('NG', 'Comdty'),	# Natural Gas
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

	data is like: "1,440.45" or "96600.00" (there may be a comma)
	"""
	return float(''.join(filter(lambda x: x != ',', data)))



def stringToDate(dateString):
	"""
	[String] dateString => [datetime] date

	dateString is of format: yyyy-mm-dd
	"""
	return datetime.datetime.strptime(dateString, '%Y-%m-%d')



def createDatetime(dt, tm):
	"""
	[String] dt, [String] tm => [Datetime] datetime

	convert "yyyy-mm-dd", "HH:mm:ss" to datetime object
	"""
	return datetime.datetime.strptime(dt + ' ' + tm, '%Y-%m-%d %H:%M:%S')



def getDateFromFilename(file):
    """
    [String] file (full path) => [Datetime] date

    The Guangfa file name has a pattern: 8888802200trddata_f20140131.txt
    Date is of format "yyyymmdd".
    """
    return datetime.datetime.strptime(file[-12:-4], '%Y%m%d')




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
		pass
	# 	processCashPositionFile(join(get_current_path(), args.file), get_current_path())