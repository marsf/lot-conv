# lot-conv.py

Rewrited the convert part of [Lot (localization tools)](https://github.com/mozilla-japan/lot) in Python.
This script requires Python 3.10 or later.


Put [gecko-l10n](https://github.com/mozilla-japan/gecko-l10n/tree/master/ja) resources to ```./src``` directory and run the command:

```> python lot-conv.py -s ./src/gecko-l10n/ja```

Then, resources are converted to ./l10n/ja and ./l10n/ja-JP-mac directory.

Convert target of file types: .ftl, .properties, .ini, .dtd, .css, .inc
Other than these types will be just copied.

## Options

To show command options:

```> python lot-conv.py -h```

- -s, --src_dir [SRC_DIR] : Set source directory of resources. (Default = ./src)
- -t, --l10n_dir [L10N_DIR] : Set target directory to output. It will be followed by locale code sub-directory. (Default = ./l10n)
- -f, --filter [FILTER_JSON_FILE] : Set custom filters.json file. It must have LOCALES values are defined. (Default = ja.filters.json)
- -l, --locale [LOCALE] : Set specific locale code to convert which is defined in filters.json file. ('ja' or 'ja-JP-mac' only)


# lot-proof.py

Rewrited the error check part of Lot in Python.
Check data for word errors and character errors are defined in errorcheck.json.

```> python lot-proof.py -l ja```

Supported file types: .ftl, .properties, .ini, .dtd

## Options

To show command options:

```> python lot-proof.py -h```

- -t, --l10n_dir : Set target root directory of proofreedings. It must contain "locale code" sub-directory.
- -l, --locale : Set specific locale code of proofreedings.
- -f, --file : Set a file to proofread.

