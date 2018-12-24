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

1) Trades are too fragmented, can we separate all trades into 3 trade files:

	- file 1: long for all securities
	- file 2: short for all securities, which cancelled out all positions in (1)
	- file 3: net openings for all securities


2) Will the trades in file 1, 2, 3 loaded into Geneva in sequence? If not, then
consider flow trade once when file 1 and 2 are loaded, flow one more time when
file 3 is loaded.




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



