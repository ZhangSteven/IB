# coding=utf-8
# 
# Read all files from a folder, then convert the IB and HGNH trade files
# to the output, then notify the users via email.
#

from utils.file import getFiles
from utils.mail import sendMail
from IB.configure import getTradeFileDir, getTradeOutputDir, getMailSender, \
						getMailSubject, getMailRecipients, getMailServer, \
						getMailTimeout
from IB.mysql import lookupLastModifiedTime, closeConnection, saveResultsToDB
from IB.ib import processTradeFile as processIBTradeFile
from IB.henghua import processTradeFile as processHGNHTradeFile
from datetime import datetime, timedelta
from os.path import join, getmtime
from itertools import chain
import logging
logger = logging.getLogger(__name__)



def main(mode):
	results = []
	results = chain(results, processIBFiles(getIBTradeFiles(mode)))
	results = chain(results, processHGNHFiles(getHGNHTradeFiles(mode)))
	
	if mode == 'production':
		results = list(results)	# we need to use it twice
		saveResultsToDB(getTradeFileDir(), results)
		closeConnection()
		sendNotification(results)

	else:
		# This step is necessary, because of the laziness of the iterables,
		# e.g., filter or map objects, filtering and mapping won't happen
		# until they are iterated.
		print(resultsToString(results))



def processIBFiles(files):
	"""
	[Iterable] files => [Iterable] results

	where results is a list of tuple (file, result, source), where
	result: 0 for success, 1 for failure.
	source: 'IB'
	"""
	def result(file):
		try:
			output = processIBTradeFile(join(getTradeFileDir(), file)
										, getTradeOutputDir())
			return (file, 0, 'IB', output)
		except:
			logger.exception('processIBFiles(): {0}'.format(file))
			return (file, 1, 'IB', None)

	
	return map(result, files)



def getIBTradeFiles(mode):
	"""
	[String] mode => [Iterable] IB trade files
	"""
	def tradeFile(file):
		"""
		[String] file => [Bool] does the file name contains 'trade'
		"""
		return 'trade_steven' in file.split('.')


	if mode == 'production':
		return filter(newerThanDB, 
						filter(tradeFile, 
							filter(csvFile, getFiles(getTradeFileDir()))))
	else:
		return filter(tradeFile, filter(csvFile, getFiles(getTradeFileDir())))



def processHGNHFiles(files):
	"""
	[Iterable] files => [Iterable] results

	where results is a list of tuple (file, result, source), where
	result: 0 for success, 1 for failure.
	source: 'HGNH'
	"""
	def result(file):
		try:
			output = processHGNHTradeFile( join(getTradeFileDir(), file)
										 , getTradeOutputDir())
			return (file, 0, 'HGNH', output)

		except:
			logger.exception('processHGNHFiles(): {0}'.format(file))
			return (file, 1, 'HGNH', None)


	return map(result, files)



def getHGNHTradeFiles(mode):
	"""
	[String] mode => [Iterable] HGNH trade files
	"""
	def tradeFile(file):
		"""
		[String] file => [Bool] does the file name contains 'trade'
		"""
		return file.lower().startswith('trade file')


	if mode == 'production':
		return filter(newerThanDB, 
						filter(tradeFile, 
							filter(excelFile, getFiles(getTradeFileDir()))))
	else:
		return filter(tradeFile, filter(excelFile, getFiles(getTradeFileDir())))



def csvFile(file):
	"""
	[String] file => [Bool] is the file's extension '.csv'
	"""
	tokens = file.split('.')
	if len(tokens) > 1 and tokens[-1] == 'csv':
		return True
	else:
		return False



def excelFile(file):
	"""
	[String] file => [Bool] is the file's extension '.xls' or 'xlsx'
	"""
	tokens = file.split('.')
	if len(tokens) > 1 and tokens[-1] in ['xls', 'xlsx']:
		return True
	else:
		return False



def newerThanDB(file):
	"""
	[String] file => [Bool] is the file in database
	"""
	lastModified = lookupLastModifiedTime(file)
	if lastModified == None:
		return True
	elif datetime.fromtimestamp(getmtime(join(getTradeFileDir(), file))) \
			- lastModified > timedelta(seconds=1):
		return True
	else:
		return False



def sendNotification(results):
	"""
	input: [List] results
	output: send notification email to recipients about the results.
	"""
	if results == []:
		return

	sendMail( resultsToString(results)
			, toSubject(results)
			, getMailSender()
			, getMailRecipients()
			, getMailServer()
			, getMailTimeout())



def resultsToString(results):
	"""
	[Iterable] results => [String] message

	result is a tuple (file, success, broker, output file)
	"""
	def outputToString(output):
		"""
		[List] output => [String] output
		"""
		if output == []:
			return '\nNo trades'
		else:
			line = '\n'
			for f in output:
				line = line + f + '\n'

			return line


	def line(result):
		"""
		[Tuple] result => [String] line
		"""
		file, success, broker, output = result
		if result[1] == 0:
			return broker + ' : ' + file + ', ' + 'OK' + outputToString(output)
		else:
			return broker + ' : ' + file + ', ' + 'fail'


	return '\n\n'.join(map(line, results))
# end of resultsToString()



def toSubject(results):
	"""
	[Iterable] results => [String] subject

	If there is any failed result in the results, then return a subject line
	indicating there is failure. Otherwise return the default subject.
	"""
	def isFailure(result):
		if result[1] == 0:
			return False
		else:
			return True


	if any(map(isFailure, results)):
		return 'Error occurred during 40006 trade conversion'
	else:
		return getMailSubject()
	




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('--mode', metavar='running mode'
						, choices=['production', 'test']
						, default='test')
	args = parser.parse_args()

	main(args.mode)