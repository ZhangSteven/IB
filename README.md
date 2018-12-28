# IB
Convert broker files to Bloomberg and Geneva format:

Bloomberg file: CSV format, for trade upload
Geneva file: CSV format, for reconciliation

There are 3 files, one for each broker:

ib.py: IB
henghua.py: Heng Hua International (HGNH)
gf.py: Guang Fa Securities


##########
Changes
##########
Now trades are separated into two groups only, the first being the opening
 position orders, the second the closing position orders.



##########
Pending
##########
Problem:

1) FX trades are not handled in current ib.py, need to manually handle.

2) HGNH trades do not mark partial execution, for example,

	Type	Quantity	Open/Close
	Buy		10			O
	Sell	15			O (but it should be 10 for closing, 5 for opening)

Is there a way to auto detect and fix this?

put trade file into a folder and automate them?

how to prevent upload the same trade file twice? how to prevent missing a trade file? record the total number of trades for each broker and match with Bloomberg tickets, maybe.



# ver 0.21, 2018-11-04
finished interface with reconciliation helper


# ver 0.2, 2018-11-03
Broker Henghua finished


# ver 0.1, 2018-11-01
Broker IB finished



