# IB
Convert InteractiveBrokers' files to Bloomberg and Geneva format:

Bloomberg file: CSV format, for trade upload
Geneva file: CSV format, for reconciliation



# ver 0.1, 2018-11-01
When extracting trades for certain portfolios (the "right" portfolio, e.g. 40006-A etc.) from Bloomberg's XML file, the program saves the key values of the converted trades to a text file. Therefore subsequent calls to the extraction function will not retrieve trades that have been extracted before (on the same day). But trade cancellations for those portfolios won't be extracted because in the XML cancellations don't have the <Portfolio> tag.




