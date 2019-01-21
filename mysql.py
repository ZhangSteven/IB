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

	try:
		with connection.cursor() as cursor:
			# create a new record
			sql = "INSERT INTO `trade_file` (`file_name`, `last_modified`, `status`) \
					VALUES (%s, %s, %s)"
			cursor.execute(sql, ('Trade File 20190117.xlsx'
								, '2019-01-20 10:05:22'
								, '0')
							)

			# save changes
			connection.commit()

	finally:
		connection.close()