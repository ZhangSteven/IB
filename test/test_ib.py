# coding=utf-8
# 

import unittest2
from os.path import join
from IB.utility import get_current_path
from IB.ib import createTradeRecords, toRecordGroups
from datetime import datetime



class TestIB(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestIB, self).__init__(*args, **kwargs)


    def testTradeRecords(self):
        records = createTradeRecords(join(get_current_path(), 'samples', 'trade1'))
        self.assertEqual(len(records), 32)
        self.verifyTrade1(records[0])
        self.verifyTrade2(records[28])



    def testRecordGroups(self):
        """
        After sorting, 6th and 7th records form a box position, therefore all
        records should be separated into 2 groups.
        """
        groups = toRecordGroups(createTradeRecords(join(get_current_path(), 'samples', 'trade2')))
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 6)     # 1st group has 6 trades
        self.assertEqual(len(groups[1]), 22)    # 2nd group has 22 trades
        self.verifyTrade3(groups[0][5])
        self.verifyTrade4(groups[1][0])



    def testRecordGroups2(self):
        """
        It will split to 3 groups.
        """
        groups = toRecordGroups(createTradeRecords(join(get_current_path(), 'samples', 'trade3')))
        self.assertEqual(len(groups), 3)
        self.assertEqual(len(groups[0]), 6)     # 1st group has 6 trades
        self.assertEqual(len(groups[1]), 6)     # 2nd group has 6 trades
        self.assertEqual(len(groups[2]), 4)



    def verifyTrade1(self, record):
        """
        First trade
        """
        self.assertEqual(len(record), 8)   # there should be 8 fields
        self.assertEqual('HIZ8 Index', record['BloombergTicker'])
        self.assertEqual('Buy', record['Side'])
        self.assertEqual(1, record['Quantity'])
        self.assertAlmostEqual(26198, record['Price'])
        self.assertEqual(datetime(2018,10,22), record['TradeDate'])
        self.assertEqual(datetime(2018,10,22), record['SettlementDate'])
        self.assertAlmostEqual(30, record['Commission Amt 1'])
        self.assertEqual('Broker Commission', record['Commission Code 1'])



    def verifyTrade2(self, record):
        """
        29th trade
        """
        self.assertEqual(len(record), 8)   # there should be 6 fields
        self.assertEqual('HIZ8 Index', record['BloombergTicker'])
        self.assertEqual('Sell', record['Side'])
        self.assertEqual(3, record['Quantity'])
        self.assertAlmostEqual(26150, record['Price'])
        self.assertEqual(datetime(2018,10,22), record['TradeDate'])
        self.assertEqual(datetime(2018,10,22), record['SettlementDate'])



    def verifyTrade3(self, record):
        """
        6th trade
        """
        self.assertEqual(len(record), 8)   # there should be 6 fields
        self.assertEqual('NQZ8 Index', record['BloombergTicker'])
        self.assertEqual('Short', record['Side'])
        self.assertEqual(4, record['Quantity'])
        self.assertAlmostEqual(6889, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['TradeDate'])
        self.assertEqual(datetime(2018,10,25), record['SettlementDate'])



    def verifyTrade4(self, record):
        """
        7th trade
        """
        self.assertEqual(len(record), 8)   # there should be 6 fields
        self.assertEqual('NQZ8 Index', record['BloombergTicker'])
        self.assertEqual('Cover', record['Side'])
        self.assertEqual(2, record['Quantity'])
        self.assertAlmostEqual(6897.25, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['TradeDate'])
        self.assertEqual(datetime(2018,10,25), record['SettlementDate'])
        self.assertAlmostEqual(4.1, record['Commission Amt 1'])
        self.assertEqual('Broker Commission', record['Commission Code 1'])

