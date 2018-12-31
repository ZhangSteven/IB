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

1) Only trades of type 'STK' and 'FUT' are handled in current ib.py, other types of trades, e.g., FX trades, are not handled. They are just ignored and need to be manually loaded into Bloomberg AIM.

2) HGNH trades do not mark partial execution, for example,

	Type	Quantity	Open/Close
	Buy		10			O (Open 10 long positions)
	Sell	15			O (but it actually is 10 for closing, 5 for opening)

Is there a way to auto detect and fix this?

3) No way to prevent from uploading the same trade file twice? how to prevent missing a trade file? record the total number of trades for each broker and match with Bloomberg tickets, maybe.


# ver 0.22, 2018-12-31
1) Fixed the problem of producing too many trade files, now only two trade files are produced for IB or HGNH, the first being the opening position orders, the second the closing position orders.

2) IB multipler and Bloomberg multipler sometimes does not match, therefore IB price is adjusted to become Bloomberg AIM upload price.



# ver 0.21, 2018-11-04
finished interface with reconciliation helper



# ver 0.2, 2018-11-03
Broker Henghua finished



# ver 0.1, 2018-11-01
Broker IB finished



