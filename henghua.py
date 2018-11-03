# coding=utf-8
# 
# Convert files from Heng Hua International to the below format:
# 
# 1. Bloomberg upload trade file.
# 2. Geneva reconciliation file.
#

from IB.utility import get_current_path, writeToFile, toRecordGroups, \
                        writeCashFile, writePositionFile
from xlrd import open_workbook
from xlrd.xldate import xldate_as_datetime
from os.path import join
from functools import reduce
import csv, logging, datetime
logger = logging.getLogger(__name__)



class InvalidTradeType(Exception):
    pass



def processTradeFile(file, outputDir):
    logger.info('processTradeFile(): {0}'.format(file))
    return writeToFile(
                toRecordGroups(
                    createTradeRecords(file)
                )
                , outputDir
                , '40006-C'
                , 'HGNH-QUANT'
            )



def processCashFile(file, outputDir):
    logger.info('processCashFile(): {0}'.format(file))
    return writeCashFile('40006-C', createCashRecords(file), outputDir)



def processPositionFile(file, outputDir):
    logger.info('processPositionFile(): {0}'.format(file))
    return writePositionFile('40006-C', createPositionRecords(file), outputDir)



def createTradeRecords(file):
    """
    [String] file => [List] trade records
    """
    return sortByTradeTime(
                list(map(toTradeRecord, linesToRecords(fileToLines(file))))
            )



def createPositionRecords(file):
    """
    [String] file => [List] position records
    """
    return list(map(toPositionRecord, linesToRecords(fileToLines(file))))



def createCashRecords(file):
    """
    [String] file => [List] cash records

    A cash record is a tuple, looks like ('HKD', 1234.56)
    """
    record = getEndingBalanceRecord(linesToRecords(fileToLines(file)))
    date = xldate_as_datetime(record['Date'], 0)

    def tupleToRecord(t):
        """
        [Tuple] (currency, quantity) => [Dictionary] cash record

        The conversion is necessary so that we can reuse the write cash file
        function.
        """
        r = {}
        r['Currency'] = t[0]
        r['Quantity'] = t[1]
        r['Date'] = date 
        return r 


    return list(map(tupleToRecord
                    , mergeCashEntries(getCashEntries(record)).items()
                    )
                )
    


def getEndingBalanceRecord(records):
    """
    [List] records from file => [Dictionary] the record showing ending balance
    """
    return list(
                filter(
                    lambda record: record['Currency'] == 'Ending Balance'
                    , records
                )
            )[0]



def getCashEntries(record):
    """
    [Dictionary] cash record showing ending balance => [List] cash records
    
    We look for columns that look like: HKD-HKFE, USD-OTHER, etc.
    """
    return filter(
                lambda record: '-' in record[0]
                , record.items()
            )



def mergeCashEntries(entries):
    """
    [Iterable] cash entries => [List] cash records

    A cash entry is a tuple looks like ('HKD-HKFE', 1234), a cash record
    is a tupe looks like ('HKD', 1234)
    """
    def toCashRecord(cashEntry):
        key, value = cashEntry
        return (key.split('-')[0], value)


    def addCashRecordToDict(cashDict, record):
        """
        [Dictionary] cashDict, [tuple] cash record => [Dictionary] cashDict
        
        It's the accumulator that merges a new cash record to the dictionary
        holding all cash records.
        """
        key, value = record
        if key in cashDict:
            cashDict[key] = cashDict[key] + value
        else:
            cashDict[key] = value

        return cashDict


    return reduce(addCashRecordToDict, map(toCashRecord, entries), {})



def fileToLines(file):
    """
    [String] file => [List] lines, each line is a list of columns
    """
    wb = open_workbook(filename=file)
    ws = wb.sheet_by_index(0)
    lines = []
    row = 0
    while row < ws.nrows:
        thisRow = []
        column = 0
        while column < ws.ncols:
            cellValue = ws.cell_value(row, column)
            if isinstance(cellValue, str):
                cellValue = cellValue.strip()
            thisRow.append(cellValue)
            column = column + 1

        lines.append(thisRow)
        row = row + 1

    return lines



def linesToRecords(lines):
    """
    [List] lines => [Iterable] records

    Using the first row as header, the function converts the remaining lines
    as records.
    """
    def lineToRecord(line):
        r = {}
        for (field, value) in zip(headers, line):
            r[field] = value

        return r

    headers = lines[0]
    return map(lineToRecord, lines[1:])



def toPositionRecord(record):
    """
    [Dictionary] record => [Dictionary] position record

    Create a new position record from the line record, position record has the
    below fields:

    1. BloombergTicker:
    2. Quantity: float number, use negative to indicate short position
    3. Currency
    4. Date: of type datetime
    """
    def toPositionQuantity(buySell, quantity):
        if buySell == 'B':
            return quantity
        else:
            return -1 * quantity

    r = {}
    r['BloombergTicker'] = record['Product']
    r['Quantity'] = toPositionQuantity(record['B/S'], record['Lots'])
    r['Currency'] = record['Currency'].split('_')[1]
    r['Date'] = xldate_as_datetime(record['Date'], 0)
    return r



def toTradeRecord(record):
    """
    [Dictionary] record => [Dictionary] Bloomberg upload record

    Create a new trade record from the existing record, the trade record has 8
    necessary fields:

    1. BloombergTicker
    2. Side
    3. Quantity
    4. Price
    5. TradeDate: of type datetime
    6. SettlementDate: of type datetime
    7. Commission Code 1: fixed to 'Broker Commission'
    8. Commission Amt 1: total commission
    """
    r = {}
    r['BloombergTicker'] = record['Contract']
    r['Side'] = getTradeSide(record)
    r['Quantity'] = record['Lots']
    r['Price'] = record['Trade Price']
    r['TradeDate'] = xldate_as_datetime(record['Trade Date'], 0)
    r['SettlementDate'] = xldate_as_datetime(record['Settlement Date'], 0)
    r['Commission Code 1'] = 'Broker Commission'
    r['Commission Amt 1'] = record['Commission']

    r['tradeTime'] = record['Trade Time']   # to be used for sorting

    # Convert to integer if possible, sometimes if the quantity of a futures
    # contract is a float (like 15.0), BLoomberg may generate an error.
    if r['Quantity'].is_integer():
        r['Quantity'] = int(r['Quantity'])

    return r



def getTradeSide(record):
    """
    [Dictionary] record => [String] side
    """
    tMap = {
        ('B', 'O'): 'Buy',
        ('B', 'C'): 'Cover',
        ('S', 'O'): 'Short',
        ('S', 'C'): 'Sell'
    }

    try:
        return tMap[(record['B/S'], record['O/C'])]
    except KeyError:
        raise InvalidTradeType('{0}'.format(record))



def sortByTradeTime(records):
    """
    [List] records => [List] new records

    Sort the list of records by their trade date and time, the earlier trades 
    are put in front. Here we assume the trade date is always the same, therefore
    we just sort by trade time.
    """
    def takeTradeTime(record):
        return record['tradeTime']

    return sorted(records, key=takeTradeTime)




if __name__ == '__main__':
    import logging.config
    logging.config.fileConfig('logging.config', disable_existing_loggers=False)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('file', metavar='input file', type=str)
    parser.add_argument('--type', metavar='file type', choices=['t', 'c', 'p'], 
                        default='t')
    args = parser.parse_args()

    """
    To run the program, put a trade/cash/position file in the local directory, 
    then do:

        python henghua.py <file_name> --type <type> 

        for type, p for position file, c for cash file, t for trade file, 
        default is 't'.
    """
    import sys
    if args.file == None:
        print('input file name is missing')
        sys.exit(1)
    elif args.type == 't':
        processTradeFile(join(get_current_path(), args.file), get_current_path())

    elif args.type == 'c':
        processCashFile(join(get_current_path(), args.file), get_current_path())

    elif args.type == 'p':
        processPositionFile(join(get_current_path(), args.file), get_current_path())