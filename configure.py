# coding=utf-8
# 
# Read configure file and return values from it.
#

from IB.utility import get_current_path
from os.path import join
import configparser


def _load_config():
	"""
	Read the config file, convert it to a config object. The config file is 
	supposed to be located in the same directory as the py files, and the
	default name is "config".

	Caution: uncaught exceptions will happen if the config files are missing
	or named incorrectly.
	"""
	cfg = configparser.ConfigParser()
	cfg.read(join(get_current_path(), 'ib.config'))
	return cfg



# initialized only once when this module is first imported by others
if not 'config' in globals():
	config = _load_config()



def getTradeFileDir():
	"""
	The directory where the log file resides.
	"""
	global config
	return config['directory']['input']



def getTradeOutputDir():
	"""
	The directory where the log file resides.
	"""
	global config
	return config['directory']['output']



def getMailSender():
	global config
	return config['email']['sender']



def getMailSubject():
	global config
	return config['email']['subject']



def getMailRecipients():
	global config
	return config['email']['recipents']



def getMailServer():
	global config
	return config['email']['server']



def getMailTimeout():
	global config
	return float(config['email']['timeout'])



def getDbName():
	global config
	return config['database']['name']



def getDbHost():
	global config
	return config['database']['host']



def getDbUser():
	global config
	return config['database']['username']



def getDbPassword():
	global config
	return config['database']['password']