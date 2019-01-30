# IB
Convert broker files to Bloomberg and Geneva format:

Bloomberg file: CSV format, for trade upload
Geneva file: CSV format, for reconciliation

There are 3 files, one for each broker:

ib.py     : IB
henghua.py: Heng Hua International (HGNH)
guangfa.py: Guang Fa Securities



Solutions:

1. During trade conversion phase:

    write file name, last modified date => database

    so that when we load trade files from a folder, we won't load the same trade
    file twice.


2. During trade flow phase:

    for each item in AIM XML,
        if it is a trade
            if it is already in database,
                ignore
            else
                write to database
                write to output XML

        if it is a cancellation,
            if it is already in database,
                ignore
            else
                if it matches existing trade id in database,
                    write to database
                    write to output XML
                else
                    ignore


    Stop using local file after database is on.


3. For both (1) and (2), use two modes,
    production mode: use database, scheduled run
    test mode: run from command line, load file from local directory, no database


4. Use MySQL database on docker.



##########
Pending
##########

1) Only trades of type 'STK' and 'FUT' are handled in current ib.py, other types of trades, e.g., FX trades, are not handled. They are just ignored and need to be manually loaded into Bloomberg AIM.

2) HGNH trades do not mark partial execution, for example,

	Type	Quantity	Open/Close
	Buy	10		O (Open 10 long positions)
	Sell	15		O (but it actually is 10 for closing, 5 for opening)

Is there a way to auto detect and fix this?

3) No way to prevent uploading the same trade file twice or to prevent missing a trade file? Record the total number of trades for each broker and match with Bloomberg tickets, maybe.

4) Trade cancellations cannot flow AIM to Geneva.


# ver 0.23, 2019-01-30
1) Guang Fa security files (trade, position, cash) can now be handled.
2) Empty records files are handled now, whenever there are files with empty
 records, a csv file is written with headers only. This way, Geneva side won't
 generate files not found error.



# ver 0.22, 2018-12-31
1) Fixed the problem of producing too many trade files, now only two trade files are produced for IB or HGNH, the first being the opening position orders, the second the closing position orders.

2) IB multipler and Bloomberg multipler sometimes does not match, therefore IB price is adjusted to become Bloomberg AIM upload price.



# ver 0.21, 2018-11-04
finished interface with reconciliation helper



# ver 0.2, 2018-11-03
Broker Henghua finished



# ver 0.1, 2018-11-01
Broker IB finished



