# lot-conv

Rewrite the convert part of [Lot (localization tools)](https://github.com/mozilla-japan/lot) in Python.
This script requires Python 3.10 or above.

Put [gecko-l10n](https://github.com/mozilla-japan/gecko-l10n/tree/master/ja) resources to ./src and run the command:

```> python lot-conv.py [-s SRC_DIR] [-t L10n_DIR]```

Then, resources are converted to ./l10n/ja and ./l10n/ja-JP-mac directory.

To show command options:

```> python lot-conv.py -h```
