# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import re
import pathlib

ERRORCHECK_JSON_FILE = 'errorcheck.json'
WORDCHECK = {}
CHARCHECK = {}
CHAR_BASE = ''
EX_PATHS = {}

L10N_DIR = 'l10n'

# Regexp to get filter item, entity id, strings of the line.
RE_filter_item = r'@@([\w\-\.]+|\u005b?|\u005d?)@@'
RE_comments = r'^#+\s|^<!\-\-|\-\->$|^;'
RE_id_only = r'[\w\.\-]+[\s\t]*=[\s\t]*$'
RE_id_str = r'([\w\.\-]+)[\s\t]*=[\s\t]*(.*)'
RE_ftl_attr = r'[\s\t]*(\.[\w\.\-]+)[\s\t]*=[\s\t]*(.*)'
RE_ftl_selector = r'[\s\t]*{[\s\t]*\$[a-zA-Z]+\s\->|[\s\t]*}$'
RE_ftr_str_series = r'([\s\t]*)(.*)'
RE_dtd_id_str = r'<\!ENTITY[\s]+([\w\.\-]+)[\s\t]*\"(.*)\"\s?>'


def load_json(file:'file_path') -> json:
  # Load errorcheck.json file.
  try:
    with open(file, 'r', encoding='UTF-8') as j:
      return json.load(j)
  except OSError as e:
      print(e)



def get_filelist(dir:'src_path') -> list:
  # Get file list from L10N_DIR.
  src_p = pathlib.Path(dir)
  if src_p.is_dir():
    return [p for p in src_p.glob('**/*') if p.is_file()]
  else:
    print('Aborted. Target directory is not found:', src_p)
    return []



def grep_file(fn:'file_path', target_locale:'locale_str') -> 'list':
  try:
    with open(fn, 'r', encoding='UTF-8') as f:
      err_str = []
      err_count = [0, 0, 0]

      # Set word checks.
      deny_words = WORDCHECK['deny'].get('COMMON') +'|'+ WORDCHECK['deny'].get(target_locale)
      allow_words = WORDCHECK['allow'].get('COMMON') +'|'+ WORDCHECK['allow'].get(target_locale)
      allow_chars = CHARCHECK['allow']
      for p in EX_PATHS.keys():
        if (str(fn.as_posix()).find(p) > 0):
          # Add deny words in defined PATH.
          if('deny' in EX_PATHS[p]):
            deny_words = deny_words + '|' + EX_PATHS[p].get('deny')
          # Add allowed words and characters in defined PATH.
          if ('allow' in EX_PATHS[p]):
            allow_words = allow_words + '|' + EX_PATHS[p].get('allow')
            allow_chars = CHARCHECK['allow'] + '|' + EX_PATHS[p].get('allow')

      for l, line in enumerate(f.readlines()):
        # Skip comment line.
        if re.match(RE_comments, line) or re.match(RE_id_only, line):
          continue
        match(fn.suffix):
          case '.ftl':
            m = re.match(RE_id_str, line) or re.match(RE_ftl_attr, line) or re.match(RE_ftr_str_series, line)
          case '.properties':
            m = re.match(RE_id_str, line)
          case '.ini':
            m = re.match(RE_id_str, line)
          case '.dtd':
            m = re.match(RE_dtd_id_str, line)
          case _:
            print(fn.suffix, 'skipped.')
            continue
        if m is None:
          continue

        # Check "deny" words.
        items_d = re.findall(deny_words, m.group(2))
        if items_d != []:
          # Exclude allowed words.
          items_d = [i for i in items_d if i not in allow_words]
          if items_d != []:
            err_str.append('  W!  @line %d: %s\t%s' % (l+1, m.group(1), items_d))
            err_count[0] += len(items_d)
         # Check "suspected" words.
        items_s = re.findall(WORDCHECK['suspected'].get(target_locale), m.group(2))
        if items_s != []:
          # Exclude allowed words.
          items_s = [i for i in items_s if i not in allow_words]
          if items_s != []:
            err_str.append('  W?  @line %d: %s\t%s' % (l+1, m.group(1), items_s))
            err_count[1] += len(items_s)
        # Check ranged chracters and kanji.
        chars = re.findall(CHAR_BASE, m.group(2))
        if chars != []:
          # Exclude allowed characters.
          chars = [c for c in chars if c not in allow_chars]
          if chars != []:
            err_str.append('  C!  @line %d: %s\t%s' % (l+1, m.group(1), chars))
            err_count[2] += len(chars)

      if len(err_str) > 0:
        print(fn)
        for err in err_str:
          print(err)
  except OSError as e:
    print(e)
    return []
  return err_count



def grep_proc(target_locale) -> 'list':
  try:
    cnt_error = 0
    cnt_suspected = 0
    cnt_char = 0
    for fp in get_filelist(pathlib.Path(L10N_DIR).joinpath(target_locale)):
      # Exclude directories.
      if re.search(r'(\/.DS_Store|\/.hg|\/.git)', str(fp.as_posix())):
        print('Directory skipped:', fp.parent)
        continue
      if re.search('\.(ftl|properties|ini|dtd)', str(fp.suffix)):
        res = grep_file(fp, target_locale)
        if res != None:
          cnt_error += res[0]
          cnt_suspected += res[1]
          cnt_char += res[2]
  except OSError as e:
    print(e)
  return [cnt_error, cnt_suspected, cnt_char]



def main(args_file:'file_path', args_locale:'locale_str'):
  errorchecks = load_json(ERRORCHECK_JSON_FILE)
  if errorchecks == None:
    return
  elif not 'WORDCHECK' in errorchecks:
    print('No WORDCHECK data in', ERRORCHECK_JSON_FILE)
    return
  elif not 'CHARCHECK' in errorchecks:
    print('No CHARCHECK data in', ERRORCHECK_JSON_FILE)
    return
  global WORDCHECK, CHARCHECK, CHAR_BASE, EX_PATHS
  WORDCHECK = errorchecks['WORDCHECK']
  CHARCHECK = errorchecks['CHARCHECK']
  # "(?![ ... ])" Excludes 'basechars', 'kanji_jyouyou_news' and 'kanji_supplement'.
  CHAR_BASE = '(?![' + CHARCHECK['basechars'] + CHARCHECK['kanji_jyouyou_news'] + CHARCHECK['kanji_supplement'] + ']).'
  EX_PATHS = errorchecks['PATH']

  if (args_file):
    if re.search('\.(ftl|properties|ini|dtd)', str(args_file.suffix)):
      res = grep_file(args_file, args_locale)
  else:
    print('Check for %s locale.\n' % args_locale)
    res = grep_proc(args_locale)

  print('\nResults (%s):\nWord errors \t%s\nSuspected words\t%s\nChar errors\t%s' % (args_locale, res[0], res[1], res[2]))
  return



if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-t', '--l10n_dir', type=pathlib.Path, default=L10N_DIR, help='Set target directory of proofreedings. It should be followed by locale code sub-directory')
  parser.add_argument('-l', '--locale', type=str, choices=['ja', 'ja-JP-mac'], default='ja', help='Set specific locale code of proofreedings.')
  parser.add_argument('-f', '--file', type=pathlib.Path, help='Set a file to proofreadings.')
  
  args = parser.parse_args()
  L10N_DIR = args.l10n_dir
  
  main(args.file, args.locale)
