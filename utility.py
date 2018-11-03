# coding=utf-8
# 

import os
from utils.utility import writeCsv
from os.path import join



def get_current_path():
	"""
	Get the absolute path to the directory where this module is in.

	This piece of code comes from:

	http://stackoverflow.com/questions/3430372/how-to-get-full-path-of-current-files-directory-in-python
	"""
	return os.path.dirname(os.path.abspath(__file__))



def writeToFile(recordGroups, outputDir, portfolio, broker):
	"""
	[List] recordGroups, [String] outputDir, [String] portfolio, [String] broker

	 => create output csv file(s) for each group

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
		file = createTradeFileName(index, group, outputDir, portfolio)
		writeCsv(file, [createCsvRow(fields, portfolio, broker, record) for record in group])
		outputFiles.append(file)

	return outputFiles



def createTradeFileName(index, group, outputDir, portfolio):
	return join(outputDir
				, toFileName(
					group[0]['TradeDate']
					, portfolio
					, 'trade'
					, createSuffix(index)))



def createSuffix(i):
	if i == 0:
		return ''
	else:
		return '_part' + str(i+1)	# i = 1 => '_part2'



def toFileName(dt, portfolio, fileType, suffix=''):
	"""
	[datetime] dt, 
	[String] portfolio, the portfolio id
	[String] fileType, trade, cash or position
	[String] suffix

	=> [String] final file name (full path)

	e.g., 40006-B_trade_yyyy-mm-dd.csv
	"""
	return portfolio + '_' + fileType + '_' + dateToString_yyyymmdd(dt) + \
			suffix + '.csv'



def dateToString(dt):
	"""
	[datetime] dt => [String] mm/dd/yy

	This format is required by Bloomberg trade upload
	"""
	return str(dt.month) + '/' + str(dt.day) + '/' + str(dt.year)[2:]



def dateToString_yyyymmdd(dt):
	"""
	[datetime] dt => [String] yyyy-mm-dd

	This format is required for cash or position file
	"""
	return str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day)



def createCsvRow(fields, portfolio, broker, record):
	"""
	[List] fields, [Dictionary] trade record => [List] String items in a row

	For trade uploaded to Bloomberg
	"""
	def fieldToRow(field):
		if field == 'Account':
			return portfolio
		elif field == 'Broker':
			return broker
		elif field in ['TradeDate', 'SettlementDate']:
			return dateToString(record[field])
		else:
			return record[field]

	return list(map(fieldToRow, fields))



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



def createCsvRows(fields, records, portfolio):
	"""
	[List] fields, [List] position or cash records => [List] rows in csv
	
	The first row is the headers (fields)
	"""
	def fieldToColumn(field, record):
		if field == 'Portfolio':
			return portfolio

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



def writeCashFile(portfolio, records, outputDir):
	"""
	[List] cash records => [String] output csv file name

	The cash file will be uploaded to Geneva for reconciliation, it 
	contains the below fields:

	Portfolio: account code in Geneva (e.g., 40006)
	Date: [String] yyyy-mm-dd
	Currency:
	Quantity:

	A header row is included.
	"""
	fields = ['Portfolio', 'Date', 'Currency', 'Balance']

	file = join(outputDir, toFileName(records[0]['Date'], portfolio, 'cash'))
	writeCsv(file, createCsvRows(fields, records, portfolio))

	return file



def writePositionFile(portfolio, records, outputDir):
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
	fields = ['Portfolio', 'Date', 'Investment', 'Currency', 'Quantity']

	file = join(outputDir, toFileName(records[0]['Date'], portfolio, 'position'))
	writeCsv(file, createCsvRows(fields, records, portfolio))

	return file