# coding=utf-8
# 

import unittest2
from os.path import join
from IB.utility import get_current_path
from IB.ib import createTradeRecords
from datetime import datetime



class TestIB(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestIB, self).__init__(*args, **kwargs)


    def testTradeRecords(self):
        records = createTradeRecords(join(get_current_path(), 'samples'))
        self.assertEqual(len(records), 32)
        self.verifyTrade1(records[0])
        self.verifyTrade2(records[11])


    def verifyTrade1(self, record):
        """
        First trade
        """
        self.assertEqual(len(record), 6)   # there should be 6 fields
        self.assertEqual('GXH9 Index', record['BloombergTicker'])
        self.assertEqual('Short', record['Side'])
        self.assertEqual(4, record['Quantity'])
        self.assertAlmostEqual(11594, record['Price'])
        self.assertEqual(datetime(2018,10,22), record['TradeDate'])
        self.assertEqual(datetime(2018,10,22), record['SettlementDate'])



    def verifyTrade2(self, record):
        """
        12th trade
        """
        self.assertEqual(len(record), 6)   # there should be 6 fields
        self.assertEqual('HIZ8 Index', record['BloombergTicker'])
        self.assertEqual('Sell', record['Side'])
        self.assertEqual(2, record['Quantity'])
        self.assertAlmostEqual(26150, record['Price'])
        self.assertEqual(datetime(2018,10,22), record['TradeDate'])
        self.assertEqual(datetime(2018,10,22), record['SettlementDate'])

