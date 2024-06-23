# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import re
import pathlib
import shutil

SRC_DIR = 'src'
L10N_DIR = 'l10n'
FILTER_JSON_FILE = 'ja.filters.json'
FILTERS = {}

# Regexp to get filter item, entity id, strings of the line.
RE_filter_item = r'@@([\w\-\.]+|\u005b?|\u005d?)@@'
RE_id_str = r'([\w\.\-]+)[\s\t]*=[\s\t]*(.*)'
RE_attr = r'[\s\t]*(\.[\w\.\-]+)[\s\t]*=[\s\t]*(.*)'
RE_str_series = r'([\s\t]*)(.*)'
RE_ftl_selector = r'[\s\t]*{[\s\t]*\$[a-zA-Z]+\s\->|[\s\t]*}$'
RE_comments = r'^#+\s|^<!\-\-|\-\->$|^;'


def load_filters_json(file:'file_path') -> json:
  # Load ja.filters.json file.
  try:
    with open(file, 'r', encoding='UTF-8') as j:
      global FILTERS
      FILTERS = json.load(j)
      return FILTERS
  except OSError as e:
      print(e)


def get_filter_word(item:'filter_str', loc:'locale_str') -> 'l10n_str':
  # Get filter word of the LOCALE from FILTERS.
  loc_index = FILTERS['LOCALES'].index(loc)
  try:
    return (FILTERS.get(item))[loc_index]
  except ValueError as e:
    print(e)
    return '[ERROR[' + item + ']ERROR]'


def get_filelist(dir:'src_path') -> list:
  # Get file list from SRC_DIR.
  src_p = pathlib.Path(dir)
  if src_p.is_dir():
    return [p for p in src_p.glob('**/*') if p.is_file()]
  else:
    print('Aborted. SRC_DIR is not found:', src_p)
    return []


def convert_file(fn:'file_path', ext:'file_ext_str', target_locale:'locale_str') -> 'list':
  results = []
  # Open and convert the file.
  try:
    with open(fn, 'r', encoding='UTF-8') as f:
      for l, line in enumerate(f.readlines()):
        # Skip comment line.
        if re.match(RE_comments, line):
          results.append(line)
          continue
        # Convert filter words.
        items = re.findall(RE_filter_item , line)
        if len(items) > 0:
          for i in items:
            if i in FILTERS:
              line = line.replace('@@'+i+'@@', get_filter_word(i, target_locale))
            elif 'COMMON' in FILTERS and i in FILTERS['COMMON']:
              line = line.replace('@@'+i+'@@', FILTERS['COMMON'].get(i))
            else:
              print(fn, '\n@line %d: Incorrect filter name: %s' % (l, i))
        results.append(line)
  except OSError as e:
    print(e)
  return results


def l10n_proc(target_locale:'locale_str'):
  count_converted = 0
  count_copied = 0
  count_skipped = 0
  for fp in get_filelist(SRC_DIR):
    # Exclude directories.
    if re.search(r'(\/.DS_Store|\/.hg|\/.git)', str(fp.as_posix())):
      print(' Directory skipped:', fp.parent)
      continue

    # Set target l10n dir, and mkdir().
    try:
      l10n_dir = pathlib.Path(L10N_DIR).joinpath(target_locale).joinpath(fp.parent.relative_to(SRC_DIR))
    except ValueError as e:
      print(e)
      return
    if not l10n_dir.exists():
      try:
        l10n_dir.mkdir(parents=True)
        #print('mkdir():', l10n_dir)
      except OSError as e:
        print(e)

    if re.search('\.(ftl|properties|ini|dtd|css|inc)', str(fp.suffix)):
      # Convert.
      res = convert_file(fp, fp.suffix, target_locale)
      if len(res) < 1:
        print('Convert skipped by error:', fp)
        count_skipped += 1
        continue
      # Write converted file to l10n_dir.
      target_fp = l10n_dir.as_posix()+'/'+fp.name
      with open(target_fp, mode='w', encoding='UTF-8') as f:
        try:
          f.writelines(res)
        except OSError as e:
          print(e)
          continue
      # Set original timestamp.
      shutil.copystat(fp, target_fp)
      #print('Converted:', target_fp)
    else:
      count_copied += 1
      #print(' %s copied:' % fp.suffix, shutil.copy2(fp, l10n_dir))
    count_converted += 1
  total_count = count_converted + count_copied + count_skipped
  print('\nResult for %s locale:\n Converted: %d\n Copied: %d\n Skipped: %d\n Total: %d files' % (target_locale, count_converted, count_copied, count_skipped, total_count))


def main(args_filter:'file_path', args_locale:'locale_str'):
  filters = load_filters_json(args_filter)
  locales = filters['LOCALES']
  if filters == None:
    return
  elif not 'LOCALES' in filters:
    print('No LOCALES values in', args_filter)
    return
  if args_locale != None:
    # FILTERS error check.
    try:
      filters['LOCALES'].index(args_locale)
    except ValueError as e:
      print('No locale items:', e)
      return
    else:
      locales = [args_locale]
  # Convert.
  for loc in locales:
    try:
      path = pathlib.Path(L10N_DIR).joinpath(loc)
      print('\nRemove existing directory:', path)
      shutil.rmtree(path)
    except OSError as e:
      print(e)
      return
    else:
      print('\nConvert to %s locale:' % loc)
      l10n_proc(loc)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--src_dir', type=pathlib.Path, default=SRC_DIR, help='Set source directory of resources.')
  parser.add_argument('-t', '--l10n_dir', type=pathlib.Path, default=L10N_DIR, help='Set target directory to output. It will be followed by locale code sub-directory.')
  parser.add_argument('-f', '--filter', type=pathlib.Path, default=FILTER_JSON_FILE, help='Load filters.json file. It must have LOCALES values are defined.')
  parser.add_argument('-l', '--locale', type=str, choices=['ja', 'ja-JP-mac'], help='Set specific locale code to convert which is defined in filters.json file.')
  args = parser.parse_args()
  SRC_DIR = args.src_dir
  L10N_DIR = args.l10n_dir
  FILTER_JSON_FILE = args.filter
  
  main(args.filter, args.locale)
