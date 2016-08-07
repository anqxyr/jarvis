# jarvis
IRC bot for the scp-wiki related channels. Powered by pyscp and sopel.

## Changelog

### 1.0.2

New features

* Added usage messages. Usage messages are great.
* Incorrectly issued commands will respond with their usage message.
* Added a global --usage argument to force the usage message even if the command is issued correctly. This is especially useful for modal commands or commands that don't require arguments.

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
