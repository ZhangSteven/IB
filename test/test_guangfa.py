# coding=utf-8
# 

import unittest2
from os.path import join
from IB.utility import get_current_path, toOpenCloseGroup
from IB.guangfa import tradefileToRecords, createTradeRecords, \
                        createCashRecords, createPositionRecords
from datetime import datetime



class TestGF(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestGF, self).__init__(*args, **kwargs)


    def testFileToRecords(self):
        records = tradefileToRecords(join(get_current_path(), 'samples',
            'XXXtrddata_f20130603.txt'))
        self.assertEqual(len(records), 20)
        self.verifyFileRecord1(records[0])
        self.verifyFileRecord2(records[19])



    def testCreateTradeRecords(self):
        records = list(createTradeRecords(join(get_current_path(), 'samples',
            'XXXtrddata_f20130607.txt')))
        self.assertEqual(len(records), 19)
        self.verifyTradeRecord1(records[0])

        # make sure sorting works
        self.assertAlmostEqual(3.83, records[1]['Price'])
        self.assertAlmostEqual(3.85, records[2]['Price'])
        self.assertAlmostEqual(3.86, records[3]['Price'])
        self.assertAlmostEqual(3.80, records[4]['Price'])



    def testCreateTradeRecords2(self):
        records = list(createTradeRecords(join(get_current_path(), 'samples',
            '8888802200trddata_f20140131.txt')))
        self.assertEqual(len(records), 6)
        self.verifyTradeRecord2(records[5])



    def testRecordGroups(self):
        """
        After sorting, 6th and 7th records form a box position, therefore all
        records should be separated into 2 groups.
        """
        groups = list(toOpenCloseGroup(createTradeRecords(join(get_current_path(), 
                        'samples', '8888802200trddata_f20140131.txt'))))
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 1)     # 1st group has 1 trade
        self.assertEqual(len(groups[1]), 5)     # 2nd group has 5 trades
        self.verifyTradeRecord2(groups[0][0])
        self.verifyTradeRecord3(groups[1][4])


    def testCreateCashRecords(self):
        records = createCashRecords(join(get_current_path(), 'samples',
            '8888802200cusfund_f20140129.txt'))
        self.assertEqual(len(records), 9)
        self.assertEqual('HKD', records[1]['Currency'])
        self.assertEqual(datetime(2014,1,29), records[1]['Date'])
        self.assertAlmostEqual(0, records[1]['Quantity'])
        self.assertEqual('USD', records[6]['Currency'])
        self.assertEqual(datetime(2014,1,29), records[6]['Date'])
        self.assertAlmostEqual(1026915.92, records[6]['Quantity'])



    def testCreatePositionRecords(self):
        records = createPositionRecords(join(get_current_path(), 'samples',
            '8888802200holddata_f20140129.txt'))
        self.assertEqual(len(records), 15)
        self.assertEqual(datetime(2014,1,29), records[0]['Date'])
        self.assertEqual('SMH4 Comdty', records[0]['BloombergTicker'])
        self.assertEqual('USD', records[0]['Currency'])
        self.assertEqual(8, records[0]['Quantity'])
        self.assertEqual(datetime(2014,1,29), records[5]['Date'])
        self.assertEqual('S K4 Comdty', records[5]['BloombergTicker'])
        self.assertEqual('USD', records[5]['Currency'])
        self.assertEqual(-4, records[5]['Quantity'])



    def verifyFileRecord1(self, record):
        """
        First trade
        """
        self.assertEqual(len(record), 22)   # there should be 22 fields
        self.assertEqual('2013-06-03', record['SettlementDate'])
        self.assertEqual('2013-06-03', record['TradeDate'])
        self.assertEqual('USD', record['Currency'])
        self.assertEqual('CME', record['Exchange'])
        self.assertEqual('AD1306', record['Contract'])
        self.assertEqual('L', record['OpenClose'])
        self.assertEqual('1', record['BuyQuantity'])
        self.assertEqual('0.96', record['Price'])
        self.assertEqual('96060.00', record['Amount'])



    def verifyFileRecord2(self, record):
        """
        Last trade
        """
        self.assertEqual(len(record), 22)   # there should be 22 fields
        self.assertEqual('2013-06-03', record['SettlementDate'])
        self.assertEqual('2013-06-03', record['TradeDate'])
        self.assertEqual('USD', record['Currency'])
        self.assertEqual('CME', record['Exchange'])
        self.assertEqual('GC1308', record['Contract'])
        self.assertEqual('O', record['OpenClose'])
        self.assertEqual('1', record['BuyQuantity'])
        self.assertEqual('0', record['SellQuantity'])
        self.assertEqual('1,414.40', record['Price'])
        self.assertEqual('23:19:26', record['Time'])
        self.assertEqual('20.00', record['Commission'])



    def verifyTradeRecord1(self, record):
        """
        first trade
        """
        self.assertEqual(len(record), 10)   # there should be 10 fields
        self.assertEqual('NGN13 Comdty', record['BloombergTicker'])
        self.assertEqual('Cover', record['Side'])
        self.assertEqual(1, record['Quantity'])
        self.assertAlmostEqual(3.84, record['Price'])
        self.assertEqual(datetime(2013,6,7), record['TradeDate'])
        self.assertEqual(datetime(2013,6,7), record['SettlementDate'])
        self.assertEqual(datetime(2013,6,7,hour=19,minute=1,second=1), record['Datetime'])



    def verifyTradeRecord2(self, record):
        """
        last trade in file (before sorting), 1st trade in 1st trade group (after
        trading)
        """
        self.assertEqual(len(record), 10)   # there should be 10 fields
        self.assertEqual('S K4 Comdty', record['BloombergTicker'])
        self.assertEqual('Short', record['Side'])
        self.assertEqual(2, record['Quantity'])
        self.assertAlmostEqual(1262, record['Price'])
        self.assertEqual(datetime(2014,1,31), record['TradeDate'])
        self.assertEqual(datetime(2014,1,31), record['SettlementDate'])
        self.assertEqual(datetime(2014,1,31,hour=22,minute=47,second=36), record['Datetime'])



    def verifyTradeRecord3(self, record):
        """
        last trade in 2nd trade group (after trading)
        """
        self.assertEqual(len(record), 10)   # there should be 10 fields
        self.assertEqual('COH4 Comdty', record['BloombergTicker'])
        self.assertEqual('Cover', record['Side'])
        self.assertEqual(1, record['Quantity'])
        self.assertAlmostEqual(106.95, record['Price'])
        self.assertEqual(datetime(2014,1,31), record['TradeDate'])
        self.assertEqual(datetime(2014,1,31), record['SettlementDate'])
        self.assertEqual(datetime(2014,1,31,hour=21,minute=32,second=2), record['Datetime'])
