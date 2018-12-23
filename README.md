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



