# jarvis
IRC bot for the scp-wiki related channels. Powered by pyscp and sopel.

## Changelog

### 1.0

New features

* Changelog!
* !errors will now check for mainlist titles that weren't removed with their coresponding article.

Bug fixes

* Fixed channels with capital letters causing incorrect message logging for some users.
* Fixed number-only-names being treated as dates when adding quotes.
* Names that start with numbers are no longer invalid when retrieving quotes.