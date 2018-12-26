# IB
Convert broker files to Bloomberg and Geneva format:

Bloomberg file: CSV format, for trade upload
Geneva file: CSV format, for reconciliation

There are 3 files, one for each broker:

ib.py: IB
henghua.py: Heng Hua International (HGNH)
gf.py: Guang Fa Securities


##########
Pending
##########
Problem:

1) Trades are too fragmented, can we separate all trades into 2 trade files:

	- file 1: open position orders for all securities (buy, short sell)
	- file 2: close position orders for all securities (sell, cover short)


	Loading to Bloomberg AIM leads to box position warnings, can choose to ignore.
	Geneva position looks OK.


2) FX trades are not handled in current ib.py




test trade, cash, position file
handle FX trade in trade file: should we just ignore them? They may be already booked. Yes we need. How to upload a FX trade with commission

put trade file into a folder and automate them?

how to prevent upload the same trade file twice? how to prevent missing a trade file? record the total number of trades for each broker and match with Bloomberg tickets, maybe.



# ver 0.21, 2018-11-04
finished interface with reconciliation helper


# ver 0.2, 2018-11-03
Broker Henghua finished


# ver 0.1, 2018-11-01
Broker IB finished



