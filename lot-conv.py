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


def load_filters_json() -> json:
  # Load ja.filters.json file.
  try:
    with open(FILTER_JSON_FILE, 'r', encoding='UTF-8') as j:
      return json.load(j)
  except OSError as e:
      print(e)


def get_filter_word(item:'filter_str', loc:'locale_str') -> 'l10n_str':
  # Get filter word of the LOCALE from FILTER.
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
            elif i in FILTERS['COMMON']:
              line = line.replace('@@'+i+'@@', FILTERS['COMMON'].get(i))
            else:
              print(fn, '\n@line %d: Incorrect filter name: %s' % (l, i))
        results.append(line)
  except OSError as e:
    print(e)
  return results


def l10n_proc(target_locale:'locale_str'):
  count = 0
  for fp in get_filelist(SRC_DIR):
    # Exclude directories.
    if re.search(r'(\/.DS_Store|\/.hg|\/.git)', str(fp.as_posix())):
      print('Directory skipped:', fp.parent)
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
      print('%s copied:' % fp.suffix, shutil.copy2(fp, l10n_dir))
    count += 1
  print('Converted: %d files to %s/%s' % (count, L10N_DIR, target_locale))


def main(args_locale:'locale_str'):
  global FILTERS
  FILTERS = load_filters_json()
  if FILTERS == None:
    return
  elif not 'LOCALES' in FILTERS or not 'COMMON' in FILTERS:
    print('No LOCALES nor COMMON values in', FILTER_JSON_FILE)
    return
  #shutil.rmtree(pathlib.Path(L10N_DIR).joinpath(args_locale))
  if args_locale != None:
    # FILTERS error check.
    try:
      FILTERS['LOCALES'].index(args_locale)
    except ValueError as e:
      print('No locale items:', e)
    else:
      l10n_proc(args_locale)
  else:
    # Convert all locale.
    for loc in FILTERS['LOCALES']:
      l10n_proc(loc)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-s', '--src_dir', type=pathlib.Path, default=SRC_DIR, help='Set source directory of resources.')
  parser.add_argument('-t', '--l10n_dir', type=pathlib.Path, default=L10N_DIR, help='Set target directory to output. It will be followed by locale code sub-directory')
  parser.add_argument('-f', '--filter', type=pathlib.Path, default=FILTER_JSON_FILE, help='Load filters.json file. It must have LOCALES and COMMON values are defined.')
  parser.add_argument('-l', '--locale', type=str, choices=['ja', 'ja-JP-mac'], help='Set specific locale code to convert.')
  args = parser.parse_args()
  SRC_DIR = args.src_dir
  L10N_DIR = args.l10n_dir
  FILTER_JSON_FILE = args.filter
  
  main(args.locale)
