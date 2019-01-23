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
from IB.ib import processTradeFile
from datetime import datetime, timedelta
from os.path import join, getmtime
from itertools import chain
import logging
logger = logging.getLogger(__name__)



def main(mode):
	results = []
	results = chain(results, processIBFiles(getIBTradeFiles(mode)))
	# resultList.extend(convertHGNHTrades(getHGNHTradeFiles(getTradeFileDir())))
	
	if mode == 'production':
		results = list(results)	# we need to use it twice
		saveResultsToDB(getTradeFileDir(), results)
		closeConnection()
		sendNotification(results)



def processIBFiles(files):
	"""
	[Iterable] files => [Iterable] results

	where results is a list of tuple (file, result, source), where
	result: 0 for success, 1 for failure.
	source: 'IB'
	"""
	def result(file):
		try:
			processTradeFile(join(getTradeFileDir(), file), getTradeOutputDir())
			return (file, 0, 'IB')

		except:
			logger.exception('processIBFiles(): {0}'.format(file))
			return (file, 1, 'IB')


	return map(result, files)



def getIBTradeFiles(mode):
	"""
	[String] mode => [Iterable] IB trade files
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
		elif datetime.fromtimestamp(getmtime(join(getTradeFileDir(), file))) \
				- lastModified > timedelta(seconds=1):
			return True
		else:
			return False


	if mode == 'production':
		return filter(newerThanDB, 
						filter(tradeFile, 
							filter(csvFile, getFiles(getTradeFileDir()))))
	else:
		return filter(tradeFile, filter(csvFile, getFiles(getTradeFileDir())))
# end of getIBTradeFiles()



def sendNotification(results):
	"""
	input: [List] results
	output: send notification email to recipients about the results.
	"""
	if results == []:
		return

	sendMail( toMailMessage(results)
			, toSubject(results)
			, getMailSender()
			, getMailRecipients()
			, getMailServer()
			, getMailTimeout())



def toMailMessage(results):
	"""
	[Iterable] results => [String] message to be send as email body,
	"""
	def line(result):
		"""
		[Tuple] result => [String] line
		"""
		if result[1] == 0:
			return result[2] + ' : ' + result[0] + ', ' + 'success' 
		else:
			return result[2] + ' : ' + result[0] + ', ' + 'fail'


	return '\n\n'.join(map(line, results))
# end of toMailMessage()



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
		return 'Error occurred: ' + getMailSubject()
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