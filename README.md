# jarvis
[![Build Status](https://travis-ci.org/anqxyr/jarvis.svg?branch=master)](https://travis-ci.org/anqxyr/jarvis)
[![Coverage Status](http://img.shields.io/coveralls/anqxyr/jarvis.svg)](https://coveralls.io/r/anqxyr/jarvis)
[![Python version](https://img.shields.io/badge/python-3.4-blue.svg)]()
[![license](https://img.shields.io/github/license/anqxyr/jarvis.svg?maxAge=2592000)]()

IRC bot for the scp-wiki related channels. Powered by pyscp and sopel.

## Changelog

### 1.1.5

* Numerous bugfixes, changes, and new commands, that went undocumented due to my poor bookkeeping habits.

### 1.1.1

* Large number of new commands in the websearch module.
* Updated dynamic help page generation.
* Bugfixes.

### 1.1

* Unit tests, Travis and Coveralls integration.
* Assorted bug fixes.

### 1.0.4

Changes

* Adjusted the help command.
* Normalised argument parsing for the !dice command.

Bug fixes

* Fixed incorrect creation times for articles that are less than a day old.
* Improved the results of --usage for modal commands.
* Fixed missing titles for several articles with non-standard series formatting.
* Fixed the bug that was causing multiple responses to all commands after a disconnect.

### 1.0.3

New features

* The !images command is now feature-complete.
* Twitter support.

Other changes

* Improved argument parsing.

Bug fixes

* Fixed attribution to multiple users.
* Fixed errors in the content of .ad pages.

### 1.0.2

New features

* Added usage messages. Usage messages are great.
* Incorrectly issued commands will respond with their usage message.
* Added a global --usage argument to force the usage message even if the command is issued correctly. This is especially useful for modal commands or commands that don't require arguments.
* Added !memo append

Other changes

* Reenabled !lc ratings in SSSC.

Bug fixes

* !ad works again.
* Fixed excessive false-positive missing title reports in !errors

### 1.0.1

New features

* Added !cleantitles command.
* Added wildcard support to the autoban module.
* Added !memo command, expanded the old memo functionality.

Other changes

* !lastcreated no longer shows the ratings of the articles.
* SCP Articles without a title no longer show up as [ACCESS DENIED]
* Improved the architecture of modal commands.
* Standartised crosschannel commands.
* Commands bound to a specific channel can now all be used in PMs / from other channels.

Bug fixes

* Uptime now counts days correctly.
* The pages reported by !errors will now be displayed in alphabetical order.
* Fixed bugs in the autoban module.
* It is no longer possible to accidentally overwrite memos.
* Fixed !random failing when called with any arguments.

### 1.0.0

New features

* Changelog!
* Added a check for orphaned mainlist titles to !errors.
* Added !version / !jarvis command. 
* Added !rejoin command.
* Added !tvtropes command.

Bug fixes

* Fixed channels with capital letters causing incorrect message logging for some users.
* Fixed number-only-names being treated as dates when adding quotes.
* Names that start with numbers are no longer invalid when retrieving quotes.
* !errors can now only be used in the SSSC.
* Ban expiration time is now checked at the time of banning instead of the last !updatebans call.
