# coding=utf-8
# 
# Store some records in MySQL database
#

import pymysql
from os.path import join
import csv, logging, datetime
logger = logging.getLogger(__name__)




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	connection = pymysql.connect(host='192.168.16.232',
								user='steven',
								password='clamc123',
								db='blp_trade',
								cursorclass=pymysql.cursors.DictCursor)

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
	# 		sql = "INSERT INTO `trade_file` (`file_name`, `last_modified`, `status`) \
	# 				VALUES (%s, %s, %s)"
	# 		cursor.executemany(sql, records)

	# 		# save changes
	# 		connection.commit()

	# finally:
	# 	connection.close()


	# insert or replace, many records
	records = [('Trade File 20190117.xlsx', '2019-01-23 9:28:56', '0')
			, ('Trade File 20190113.xlsx', '2019-01-14 23:15:32', '1')]
	try:
		with connection.cursor() as cursor:
			# create a new record
			sql = "REPLACE INTO `trade_file` (`file_name`, `last_modified`, `status`) \
					VALUES (%s, %s, %s)"
			cursor.executemany(sql, records)

			# save changes
			connection.commit()

	finally:
		connection.close()