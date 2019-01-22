# coding=utf-8
# 
# Read all files from a folder, then convert the IB and HGNH trade files
# to the output, then notify the users via email.
#

from utils.file import getFiles
from IB.configure import getTradeFileDir
from IB.mysql import lookupLastModifiedTime, closeConnection, saveResultsToDB
from datetime import datetime, timedelta
from os.path import join, getmtime
import logging
logger = logging.getLogger(__name__)



def convert(mode):
	resultList = []
	resultList.extend(convertIBTrades(getIBTradeFiles(getTradeFileDir(), mode)))
	# resultList.extend(convertHGNHTrades(getHGNHTradeFiles(getTradeFileDir())))
	
	if mode == 'production':
		saveResultsToDB(getTradeFileDir(), resultList)
		closeConnection()

	# sendMail(toMailMessage(resultList))



def convertIBTrades(files):
	"""
	[Iterable] files => [List] results

	where results is a list of tuple (file, result), result is 0 for success
	or 1 for failure.
	"""
	return [(f, 0) for f in files]



def getIBTradeFiles(directory, mode):
	"""
	[String] directory, [String] mode => [Iterable] IB trade files
	"""
	def csvFile(file):
		"""
		[String] file => [Bool] is the file's extension '.csv'
		"""
		tokens = file.split('.')
		if len(tokens) > 1 and tokens[-1] == 'csv':
			return True
		else:
			return False


	def tradeFile(file):
		"""
		[String] file => [Bool] does the file name contains 'trade'
		"""
		return 'trade_steven' in file.split('.')


	def newerThanDB(file):
		"""
		[String] file => [Bool] is the file in database
		"""
		lastModified = lookupLastModifiedTime(file)
		if lastModified == None:
			return True
		elif datetime.fromtimestamp(getmtime(join(directory, file))) \
				- lastModified > timedelta(seconds=1):
			return True
		else:
			return False


	if mode == 'production':
		return filter(newerThanDB, 
						filter(tradeFile, 
							filter(csvFile, getFiles(directory))))
	else:
		return filter(tradeFile, filter(csvFile, getFiles(directory)))
# end of getIBTradeFiles()



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--mode', metavar='running mode'
						, choices=['production', 'test']
						, default='test')
	args = parser.parse_args()

	convert(args.mode)