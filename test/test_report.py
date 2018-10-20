# coding=utf-8
# 

import unittest2
from os.path import join
from clamc_trustee.utility import get_current_path
from clamc_trustee.report import readFiles, consolidateRecords



def htmBond(record):
    if (record['type'], record['accounting']) == ('bond', 'htm'):
        return True
    return False



class TestReport(unittest2.TestCase):
    """
    Consolidated records from two files.
    """

    def __init__(self, *args, **kwargs):
        super(TestReport, self).__init__(*args, **kwargs)


    def test1(self):
        """
        Test consolidated records
        """
        records = readFiles(join(get_current_path(), 'samples', 'testfolder'))
        records = list(consolidateRecords(filter(htmBond, records)))
        self.assertEqual(len(records), 93)
        self.verifyBond1([r for r in records if r['isin'] == 'HK0000175916'])
        self.verifyBond2([r for r in records if r['isin'] == 'US268317AB08'])



    def verifyBond1(self, records):
        """
        DBANFB12014 Dragon Days Ltd 6.0%, the bond exists in both 
        portfolio 12229 and 12734. 
        """
        self.assertEqual(len(records), 1)   # there should be only one
        record = records[0]
        self.assertTrue(not 'portfolio' in record)
        self.assertEqual('DBANFB12014 Dragon Days Ltd 6.0%', record['description'])
        self.assertEqual('HKD', record['currency'])
        self.assertEqual(1000000000, record['quantity'])
        self.assertAlmostEqual(6, record['coupon'])
        self.assertEqual('2018-3-21', record['interest start day'])
        self.assertEqual('2022-3-21', record['maturity'])
        self.assertAlmostEqual(103.730688, record['average cost'])
        self.assertAlmostEqual(101.599947, record['amortized cost'])
        self.assertEqual(1037306880, record['total cost'])
        self.assertAlmostEqual(6739726.03, record['accrued interest'], 2)
        self.assertAlmostEqual(1022739195.71, record['total amortized cost'], 2)



    def verifyBond2(self, records):
        """
        US268317AB08 Electricite D F6.5%, from consolidated
        HTM bond records of 12229 and 12734. The bond exists only
        in 12734.
        """
        self.assertEqual(len(records), 1)   # there should be only one
        record = records[0]
        self.assertTrue(not 'percentage of fund' in record)
        self.assertEqual('2018-04-30', record['valuation date'])
        self.assertEqual('US268317AB08 Electricite D F6.5%', record['description'])
        self.assertEqual('bond', record['type'])
        self.assertEqual('USD', record['currency'])
        self.assertEqual(33000000, record['quantity'])
        self.assertAlmostEqual(6.5, record['coupon'])
        self.assertEqual('2018-1-26', record['interest start day'])
        self.assertAlmostEqual(100.6170829, record['average cost'])
        self.assertAlmostEqual(100.3129323, record['amortized cost'])
        self.assertAlmostEqual(-100369.69, record['total amortized gain loss'])
        self.assertAlmostEqual(259771977.25, record['total cost HKD'])
        self.assertAlmostEqual(4442578.047, record['accrued interest HKD'], 2)
        self.assertAlmostEqual(264253574.355629, record['total amortized cost HKD'], 2)
        self.assertAlmostEqual(-787751.512, record['total amortized gain loss HKD'], 2)
        self.assertAlmostEqual(826770.5706, record['FX gain loss HKD'], 2)

