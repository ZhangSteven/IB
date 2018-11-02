# coding=utf-8
# 

import unittest2
from os.path import join
from IB.utility import get_current_path, toRecordGroups
from IB.henghua import createTradeRecords, createCashRecords
from datetime import datetime



class TestHenghua(unittest2.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestHenghua, self).__init__(*args, **kwargs)


    def testTradeRecords(self):
        records = createTradeRecords(join(get_current_path(), 'samples', 'henghua_trades.xlsx'))
        self.assertEqual(len(records), 20)
        self.verifyTrade1(records[0])
        self.verifyTrade2(records[19])



    def testRecordGroups(self):
        """
        After sorting, 7th and 8th records form a box position, therefore all
        records should be separated into 2 groups.
        """
        groups = toRecordGroups(createTradeRecords(join(get_current_path(), 'samples', 'henghua_trades.xlsx')))
        self.assertEqual(len(groups), 2)
        self.assertEqual(len(groups[0]), 7)
        self.assertEqual(len(groups[1]), 13)
        self.verifyTrade3(groups[0][6])
        self.verifyTrade4(groups[1][0])



    def testCashRecords(self):
        records = createCashRecords(join(get_current_path(), 'samples', 'cash_henghua.xlsx'))
        self.assertEqual(len(records), 4)
        sortedRecords = sorted(records)
        self.assertEqual(sortedRecords[0][0], 'EUR')
        self.assertAlmostEqual(sortedRecords[0][1], 14879.55)
        self.assertEqual(sortedRecords[1][0], 'HKD')
        self.assertAlmostEqual(sortedRecords[1][1], 4600520.48)
        self.assertEqual(sortedRecords[2][0], 'TWD')
        self.assertAlmostEqual(sortedRecords[2][1], 17329.36)
        self.assertEqual(sortedRecords[3][0], 'USD')
        self.assertAlmostEqual(sortedRecords[3][1], 264762.136)



    # def testHolding(self):
    #     records = createPositionRecords(join(get_current_path(), 'samples', 'position.csv'))
    #     self.assertEqual(len(records), 12)
    #     self.verifyPosition1(records[0])
    #     self.verifyPosition2(records[11])



    def verifyTrade1(self, record):
        """
        First trade
        """
        self.assertEqual(len(record), 9)   # there should be 8 fields
        self.assertEqual('HIV8 Index', record['BloombergTicker'])
        self.assertEqual('Buy', record['Side'])
        self.assertEqual(1, record['Quantity'])
        self.assertAlmostEqual(25680, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['TradeDate'])
        self.assertEqual(datetime(2018,10,25), record['SettlementDate'])
        self.assertAlmostEqual(15, record['Commission Amt 1'])
        self.assertEqual('Broker Commission', record['Commission Code 1'])



    def verifyTrade2(self, record):
        """
        29th trade
        """
        self.assertEqual(len(record), 9)   # there should be 6 fields
        self.assertEqual('ESZ9 Index', record['BloombergTicker'])
        self.assertEqual('Cover', record['Side'])
        self.assertEqual(3, record['Quantity'])
        self.assertAlmostEqual(2842, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['TradeDate'])
        self.assertEqual(datetime(2018,10,25), record['SettlementDate'])
        self.assertAlmostEqual(18, record['Commission Amt 1'])



    def verifyTrade3(self, record):
        """
        7th trade
        """
        self.assertEqual('GXH9 Index', record['BloombergTicker'])
        self.assertEqual('Cover', record['Side'])
        self.assertEqual(6, record['Quantity'])
        self.assertAlmostEqual(11510, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['TradeDate'])



    def verifyTrade4(self, record):
        """
        8th trade
        """
        self.assertEqual('GXH9 Index', record['BloombergTicker'])
        self.assertEqual('Buy', record['Side'])
        self.assertEqual(1, record['Quantity'])
        self.assertAlmostEqual(11510, record['Price'])
        self.assertEqual(datetime(2018,10,25), record['SettlementDate'])
        self.assertAlmostEqual(6, record['Commission Amt 1'])
        self.assertEqual('Broker Commission', record['Commission Code 1'])



    # def verifyPosition1(self, record):
    #     self.assertEqual(record['Currency'], 'USD')
    #     self.assertEqual(record['BloombergTicker'], 'SPY US Equity')
    #     self.assertAlmostEqual(record['Quantity'], 500)
    #     self.assertEqual(record['Date'], datetime(2018,10,26))



    # def verifyPosition2(self, record):
    #     self.assertEqual(record['Currency'], 'USD')
    #     self.assertEqual(record['BloombergTicker'], 'S H9 Comdty')
    #     self.assertAlmostEqual(record['Quantity'], -24)
    #     self.assertEqual(record['Date'], datetime(2018,10,26))

