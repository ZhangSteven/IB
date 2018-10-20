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
	


	return r



def getTradeFiles(files):
	"""
	[list] txt files => [list] trade files
	"""
	return list(filter(lambda fn: 'Trades_Activity' in fn.split('\\')[-1], files))



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

	tradeFiles = getTradeFiles(getCsvFiles(join(get_current_path(), 'samples')))
	if len(tradeFiles) == 0:
		print('trade file not found')
	else:
		# print('trade file: {0}'.format(tradeFiles[0]))
		records = fileToRecords(tradeFiles[0])

		

