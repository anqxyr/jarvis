# jarvis
IRC bot for the scp-wiki related channels. Powered by pyscp and sopel.

## Changelog

### 1.0.1

New features

* Added !cleantitles command.

Other changes

* !lastcreated no longer shows the ratings of the articles.
* Improved the architecture of modal commands.
* Standartised crosschannel commands.
* Commands bound to a specific channel can now all be used in PMs / from other channels.

Bug fixes

* Uptime now counts days correctly.
* The pages reported by !errors will now be displayed in alphabetical order.
* Fixed bugs in the autoban module.

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
