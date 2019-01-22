# coding=utf-8
# 
# Store some records in MySQL database
#

import pymysql
from os.path import join, getmtime
from time import strftime, localtime
import logging
logger = logging.getLogger(__name__)



def lookupLastModifiedTime(file):
	"""
	[String] file => [Datetime] last modified time of file in DB.

	if lookup does not find any record in database, return None
	"""
	try:
		with getConnection().cursor() as cursor:
			sql = "SELECT last_modified FROM file WHERE file_name='{0}'".format(file)
			cursor.execute(sql)
			row = cursor.fetchone()
			if row == None:
				logger.debug('lookupLastModifiedTime(): {0} not found'.format(file))
				return None
			else:
				return row['last_modified']

	except:
		logger.exception('lookupLastModifiedTime(): ')



def saveResultsToDB(directory, resultList):
	"""
	input: [String] directory, [Iterable] resultList
	output: save the results into database

	where directory is the directory containing the files, and resultList
	is a list of tuple (file, status), status is either 0 or 1.
	"""
	# records = [('Trade File 20190117.xlsx', '2019-01-23 9:28:56', '0')
	# 		, ('Trade File 20190113.xlsx', '2019-01-14 23:15:32', '1')]
	def toDBRecord(result):
		"""
		([String] file, [Int] status) => 
			([String] file, [String] datetime, [String] status)
		"""
		file, status = result
		return (file
				, strftime('%Y-%m-%d %H:%M:%S', localtime(getmtime(join(directory, file))))
				, str(status))

	# we need to convert to list first and tell whether it's empty because
	# emtpy list will cause cursor.executemany() to fail
	records = list(map(toDBRecord, resultList))
	if records == []:
		logger.debug('saveResultsToDB(): no records to save')
		return


	try:
		with connection.cursor() as cursor:
			# sql = "REPLACE INTO `file` (`file_name`, `last_modified`, `status`) \
			# 		VALUES (%s, %s, %s)"
			sql = "REPLACE INTO file (file_name, last_modified, status) \
					VALUES (%s, %s, %s)"
			cursor.executemany(sql, records)

			# save changes
			connection.commit()

	except:
		logger.exception('saveResultsToDB(): ')



connection = None
def getConnection():
	global connection
	if connection == None:
		connection = pymysql.connect(host='192.168.16.232',
									user='steven',
									password='clamc123',
									db='blp_trade',
									cursorclass=pymysql.cursors.DictCursor)
	return connection



def closeConnection():
	global connection
	if connection != None:
		connection.close()



if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	# Works
	# try:
	# 	with connection.cursor() as cursor:
	# 		# create a new record
	# 		sql = "INSERT INTO `trade_file` (`file_name`, `last_modified`, `status`) \
	# 				VALUES (%s, %s, %s)"
	# 		cursor.execute(sql, ('Trade File 20190117.xlsx'
	# 							, '2019-01-20 10:05:22'
	# 							, '0')
	# 						)

	# 		# save changes
	# 		connection.commit()

	# finally:
	# 	connection.close()


	# Insert many records, also works
	# records = [('Trade File 20190115.xlsx', '2019-01-18 9:15:38', '0')
	# 			, ('Trade File 20190116.xlsx', '2019-01-19 15:01:55', '1')]
	# try:
	# 	with connection.cursor() as cursor:
	# 		# create a new record
	# 		sql = "INSERT INTO `file` (`file_name`, `last_modified`, `status`) \
	# 				VALUES (%s, %s, %s)"
	# 		cursor.executemany(sql, records)

	# 		# save changes
	# 		connection.commit()

	# finally:
	# 	connection.close()


	# insert or replace, many records


	# finally:
	# 	connection.close()

	print(lookupLastModifiedTime('Trade File 20190116.xlsx'))
	closeConnection()