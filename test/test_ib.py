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
        self.assertEqual(len(records), 150)
        self.verifyTrade1(records[0])
        self.verifyTrade2(records[29])


    def verifyTrade1(self, record):
        """
        First trade
        """
        self.assertEqual(len(record), 6)   # there should be 6 fields
        self.assertEqual('VXF3', record['BloombergTicker'])
        self.assertEqual('LONG', record['Side'])
        self.assertEqual(10, record['Quantity'])
        self.assertAlmostEqual(18.9, record['Price'])
        self.assertEqual(datetime(2012,11,19), record['TradeDate'])
        self.assertEqual(datetime(2012,11,19), record['SettlementDate'])



    def verifyTrade2(self, record):
        """
        30th trade
        """
        self.assertEqual(len(record), 6)   # there should be 6 fields
        self.assertEqual('VXH3', record['BloombergTicker'])
        self.assertEqual('SHORT', record['Side'])
        self.assertEqual(10, record['Quantity'])
        self.assertAlmostEqual(20.8, record['Price'])
        self.assertEqual(datetime(2012,11,19), record['TradeDate'])
        self.assertEqual(datetime(2012,11,19), record['SettlementDate'])

