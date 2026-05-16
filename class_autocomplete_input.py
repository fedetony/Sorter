# -*- coding: utf-8 -*-
# Autocomplete functions for Paths with key input functions.
########################
# F.garcia
# creation: 03.02.2025
########################

import os
import sys
import re
import glob as gb
import inquirer
from rich import print  # pylint: disable=redefined-builtin
import rich.text
from class_file_manipulate import FileManipulate
from key_press_functions import key_pressed, get_key, wait_key_press_timeout, wait_key
try:
    from class_sql_search_query import SQLSearchGenerator, ALLOWED_DICT,ALLOWED_OPERATORS_DICT
    ALLOWED_OPERATORS=list(ALLOWED_OPERATORS_DICT.keys())
    ALLOWED_OPERATIONS=list(ALLOWED_DICT.keys())

    SQL_SG=SQLSearchGenerator()
except:
    ALLOWED_OPERATORS=[]
    ALLOWED_OPERATIONS=[]
    SQL_SG=None
f_m = FileManipulate()
APP_PATH = f_m.get_app_path()
CTRL_KEY = "ctrl+"
ARROW_KEY = "arrow"


class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen."""

    def __init__(self):
        try:
            if os.name == 'nt':
                self.impl = _GetchWindows()
            else:
                self.impl = _GetchUnix()
        except (ImportError,ModuleNotFoundError):
            self.impl = _GetchUnix()

    def __call__(self):
        return self.impl()


class _GetchUnix:
    """Getch for unix"""

    def __init__(self):
        self.me = "posix"

    def __call__(self):
        import tty, termios  # pylint: disable=import-outside-toplevel, import-error, multiple-imports

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    """Getch for windows"""

    def __init__(self):
        self.me = "nt"

    def __call__(self):
        import msvcrt  # pylint: disable=import-outside-toplevel

        return msvcrt.getch()


# Function definition
getch = _Getch()
raw_key_pressed = key_pressed
get_raw_key = get_key
wait_raw_key_press_timeout = wait_key_press_timeout
wait_raw_key = wait_key


class AutocompletePathFile:
    """Autocomplete path and files functions"""

    def __init__(self, prompt, base_path=APP_PATH, absolute_path=True, verbose=True, inquire=False):
        self.prompt = prompt
        self.line_user_input = ""
        self.line_autocompleted = ""
        self.autocomplete_options = []
        self.base_path = base_path
        self.absolute_path = absolute_path
        self.verbose = verbose
        self.options = ""
        self.inquire = inquire
        self.limit_for_inquire = -11  # limit the list length.. else is not nice
        self.limit_for_not_verbose = 20
        self.char_sequence = []
        if self.prompt:
            print(self.prompt)

    def _get_possible_path_list(self, path) -> list[str]:
        """Use glob to find similar paths with patterns

        Args:
            path (str): path as pattern

        Returns:
            list: list of patterns found
        """
        try:
            if os.path.isdir(path):
                return gb.glob(os.path.join(path, "*"))
            list_ans = gb.glob(path + "*")
            # from application path
            if len(list_ans) == 0:
                path_app = os.path.join(self.base_path, path)
                if os.path.isdir(path_app):
                    return gb.glob(os.path.join(path_app, "*"))
                list_ans = gb.glob(path_app + "*")
                if len(list_ans) > 0:
                    return list_ans
                return [path]
            return list_ans
        except (TypeError, ValueError) as eee:
            print(f"Error: {eee}")
            return []

    @staticmethod
    def print_cycle(iii:int,total:int=None):
        """Prints a rotating cycle and iteration value in same position.

        Args:
            iii (int): iteration
            total (int, optional): total. Defaults to None.
        """
        cycle=['/','-','\\',"|"]
        iter,index=divmod(iii,len(cycle))
        # print(index)
        itstr=cycle[index]+' '+str(iter)
        if total:
            itstr=itstr+'/'+str(total)
        sys.stdout.write(itstr)
        sys.stdout.flush()
        sys.stdout.write('\b'*len(itstr))

    @staticmethod
    def get_commontxt_optionlist(a_string_list: list):
        """Takes a list of string, like paths, and returns the repeated text in the begining of each string.

        Args:
            a_string_list (list): List of strings

        Returns:
            tuple(str,list): Repeated text in string start.
                    List with non repeated end of strings
        """
        fill_add = ""
        ini_str = ""
        comp_list = a_string_list.copy()
        all_same = True
        if isinstance(comp_list, list) and len(comp_list) > 0:
            if len(comp_list[0]) > 0:
                ini_str = comp_list[0][0]

        while all_same and ini_str != "":
            new_comp = []
            for ccc in comp_list:
                if len(ccc) > 0:
                    if ccc[0] == ini_str:
                        new_comp.append(ccc[1:])
                    else:
                        all_same = False
                        break
                else:
                    break
            if all_same:
                fill_add = fill_add + ini_str
                if isinstance(new_comp, list) and len(new_comp) > 0:
                    if len(new_comp[0]) > 0:
                        ini_str = new_comp[0][0]
                    else:
                        break
                    comp_list = new_comp.copy()
                else:
                    break
            # print(f"options: {comp_list}")
        return fill_add, comp_list

    @staticmethod
    def _get_name_limit_count(comp_list, ini_l, limit_count):
        """gets name and count"""
        the_name = ""
        count = 0
        for ccc in comp_list:
            if ccc[:1] == ini_l:
                if the_name == "":
                    the_name = ccc
                elif the_name != "":
                    if count < limit_count:
                        the_name = the_name + ", " + ccc
                    elif count == limit_count:
                        the_name = the_name + ", ..."
                count = count + 1
        return the_name, count

    def do_inquire(self, a_path_file, list_auto, limit_count=4):
        """Use PyInquire to get the path

        Args:
            a_path_file (str): file for path
            list_auto (list): list of options to autofill

        Returns:
            str: Autofilled until exit.
        """
        comp_list = []
        while True:
            fill_add2, _ = self.get_commontxt_optionlist(list_auto)
            for path in list_auto:
                comp_list.append(path.replace(fill_add2, ""))
            fill_add, comp_list = self.get_commontxt_optionlist(comp_list)
            # print(a_path_file,'-->>',fill_add,"=?????=",fill_add2)
            if fill_add == "":
                end_path = fill_add2
            else:
                end_path = a_path_file + fill_add
            choices = []
            ini_letters = self.get_initial_letters(comp_list)
            opt_txt = []
            opt_count = []
            for ini_l in ini_letters:
                the_name, count = self._get_name_limit_count(comp_list, ini_l, limit_count)
                opt_count.append(count)
                opt_txt.append(the_name)
            choices.append(("-> Exit", ":"))
            for ini_l, ntxt, count in zip(ini_letters, opt_txt, opt_count):
                choices.append((f"{ini_l}({count}): {ntxt}", f"{ini_l}"))

            questions = [
                inquirer.List(
                    "letter",
                    message=f"Options for {end_path}",
                    choices=choices,
                    carousel=False,
                )
            ]
            # os.system('cls' if os.name == 'nt' else 'clear')
            answers = inquirer.prompt(questions)
            if answers["letter"] == ":":
                return end_path
            for ini_l, ntxt, count in zip(ini_letters, opt_txt, opt_count):
                if answers["letter"] == ini_l and count != 1:
                    end_path = end_path + answers["letter"]
                    return end_path
                if answers["letter"] == ini_l and count == 1:
                    end_path = end_path + ntxt
                    return end_path

    def autocomplete_path(self, a_path_file):
        """Autocompletes the paths. If only one possibility, will autocomplete. If many possibilities, will find

        Args:
            a_path_file (str): path to autocomplete

        Returns:
            _type_: autocompleted path
        """
        list_auto = self._get_possible_path_list(a_path_file)
        # print(f"List----->>>>{list_auto}")
        # print(f"base Path----->>>>{self.base_path} -> {a_path_file}")
        self.options = ""
        if len(list_auto) == 1:
            end_path = list_auto[0]
            if not self.absolute_path and os.path.exists(os.path.join(self.base_path, end_path)):
                end_path = os.path.join(self.base_path, end_path)
            path_exists = os.path.exists(end_path)
            if self.verbose:
                print(f"File/Path exists: {path_exists}")
            if path_exists:
                # to fix the separators
                end_path = f_m.fix_path_separators(end_path)
            return end_path
        if len(list_auto) > 1:
            if self.inquire and len(list_auto) < self.limit_for_inquire or self.inquire and self.limit_for_inquire < 0:
                return self.do_inquire(a_path_file, list_auto)
            comp_list = []
            fill_add2, _ = self.get_commontxt_optionlist(list_auto)
            for path in list_auto:
                comp_list.append(path.replace(fill_add2, ""))
            fill_add, comp_list = self.get_commontxt_optionlist(comp_list)
            # print(a_path_file,'-->>',fill_add,"=?????=",fill_add2)
            if fill_add == "":
                if len(fill_add2) < len(a_path_file):
                    end_path = a_path_file
                else:
                    end_path = fill_add2
            else:
                end_path = a_path_file + fill_add
            if self.verbose:
                self.options = f"[{len(comp_list)}] Options: {end_path}+{comp_list}"
                self.options = self.cut_string_to_size(self.options, 333)

            else:
                if len(comp_list) < self.limit_for_not_verbose:
                    self.options = (
                        f"[{len(comp_list)}options]+{comp_list}"  # -->{fill_add}<-{fill_add2} got {a_path_file}"
                    )
                else:
                    self.options = f"[{len(comp_list)} options starting with {self.get_initial_letters(comp_list)}]"
                self.options = self.cut_string_to_size(self.options, 333)
            return end_path
        return a_path_file

    def autocomplete_from_list(self,a_txt:str,selection_list:list)->str:
        """Autocompletes the text. If only one possibility, will autocomplete. If many possibilities, will set
        the options text.

        Args:
            a_path_file (str): path to autocomplete

        Returns:
            str: autocompleted path
        """
        list_auto=[]
        words = a_txt.split(" ")
        last_word =''
        if len(words)>0:
            last_word = words[-1]
        for possibletxt in selection_list:
            if last_word in possibletxt:
                startw,_ =self.get_commontxt_optionlist([last_word,possibletxt])
                if startw==last_word:
                    list_auto.append(possibletxt)
        self.options = ""
        if len(list_auto) == 1:
            return str(list_auto[0]).replace(last_word,'')
        if len(list_auto) > 1:
            fill_add, comp_list=self.get_commontxt_optionlist(list_auto)
            self.options = f"[{len(list_auto)}] Options for {a_txt}: {comp_list}"
            return fill_add.replace(last_word,'')
        return ""

    @staticmethod
    def get_initial_letters(comp_list: list) -> list:
        """Gets the first letters of the strings. Returns a list of initila letters"""
        ini_letters = []
        for ccc in comp_list:
            if ccc[:1] not in ini_letters:
                ini_letters.append(ccc[:1])
        return ini_letters

    @staticmethod
    def cut_string_to_size(txt: str, size: int) -> str:
        """Formats/ cuts a string to the size"""
        if len(txt) > size:
            aaa = int(size / 2) - 3
            bbb = int(size / 2) - 1
            sss = txt[:aaa] + " ... " + txt[-bbb:]
            return sss
        return txt

    @staticmethod
    def raw_key_to_sequence(rawkey: str):
        """Takes a key in raw converts it to int sequence list

        Args:
            rawkey (str): raw format \\x##

        Returns:
            list[int]: Sequence
        """
        keyhex = rawkey.split("\\x")
        for iii, an_hex in enumerate(keyhex):
            if an_hex != "":
                keyhex[iii] = "0x" + an_hex
            else:
                keyhex[iii] = "0x00"
        keyint = []
        iii = 0
        for an_hex in keyhex:
            hhh = int(an_hex, 16)
            if iii == 0 and hhh == 0:
                # ignore first 0 in sequence.
                iii += 1
            else:
                keyint.append(hhh)
        # print(keyhex,'->',keyint)
        return keyint

    def get_sql_input(self)->tuple:
        """Generates advanced search queries for Operations.

        Returns:
            tuple[str,str,bool]:  (SQL, message, is_valid)
                Returns only SQL WHERE statement
        """
        if not SQL_SG:
            return None,None,None
        text_input=''
        pos=0
        is_help=False
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            sql,msg,is_valid=SQL_SG.get_sql_from_text_input(text_input)
            print("Press F1 to print Options. Esc to Cancel. Enter to select SQL WHERE Query.", pos)
            if is_help:
                print("Available Operations:")
                print(ALLOWED_OPERATIONS)
                print("Available Operators:")
                print(ALLOWED_OPERATORS_DICT)
                is_help=False
            print("Message:",msg)
            print("Input Valid:",is_valid)
            print("SQL WHERE:",sql)
            if self.options != '':
                print(self.options)
            pretxt="Input Text:"
            print(rich.text.Text(self.highlight_cursor(pretxt+text_input, len(pretxt)+pos)),end='')
            (key_handle,is_special)=self.wait_key_press()
            if not is_special:
                text_input=self.insert_char_at_pos(text_input,key_handle,pos)
                pos += 1
            if key_handle == 'F1':
                is_help=True
            elif key_handle == 'backspace':
                if pos>0:
                    text_input=self.remove_char_at_pos(text_input,pos)
                    pos += -1
            elif key_handle == 'delete':
                if pos<len(text_input):
                    text_input=self.remove_char_at_pos(text_input,pos+1)
            elif key_handle == 'arrowleft':
                pos += -1
            elif key_handle == 'arrowright':
                pos += 1
            elif key_handle == 'home':
                pos = 0
            elif key_handle == 'end':
                pos = len(text_input)
            elif key_handle == 'tab':
                self.options = ""
                auto=self.autocomplete_from_list(text_input[:pos],ALLOWED_OPERATIONS)
                text_input=text_input[:pos]+auto+text_input[pos:]
                pos=len(text_input[:pos]+auto)
            if key_handle == 'enter':
                return sql,msg,is_valid
            if key_handle == 'esc':
                return '','User Cancel',False
            #Fix position before loop
            if pos<0:
                pos=0
            elif pos>=len(text_input):
                pos=len(text_input)

    def raw_key_to_key_handle(self, rawkey: str):
        """Converts a raw key into a key handle

        Args:
            rawkey (str): raw key in format \\x##

        Returns:
           tuple: key_handle, is_special_character
        """
        sequence = self.raw_key_to_sequence(rawkey)
        special_character = False
        key_handle = None
        for kkk in sequence:
            key_handle = self.handle_key(chr(kkk))

        if key_handle:
            if len(key_handle) > 1:  # words with more than 1 character is special character
                special_character = True
        return key_handle, special_character

    @staticmethod
    def list_compare(list1: list, list2: list) -> bool:
        """Compares two lists returns True if they are the same

        Args:
            list1 (list): list 1
            list2 (list): list 2

        Returns:
            bool: True if order and size are the same.
        """
        if not isinstance(list1, list) or not isinstance(list2, list):
            return False
        if len(list1) != len(list2):
            return False
        for l1, l2 in zip(list1, list2):
            if l1 != l2:
                return False
        return True

    def _get_key_comparison(self, char_sequence, opt1: list, opt2: list = None, result: str = None, skip: str = None):
        """Compares options to char_sequence: if are the same then returns (result,reseted char sequence)
            if opt2 the same then returns (result,reseted char sequence)
            else (None , same char_sequence)
        Args:
            char_sequence (_type_): char sequence
            opt1 (list): option to compare
            opt2 (list, optional): Second option. Defaults to None.
            result (str, optional): Value. Defaults to ''.

        Returns:
            tuple: (result,char_sequence)
        """
        if skip:
            return (skip, char_sequence)
        if self.list_compare(char_sequence, opt1):
            return result, []
        if self.list_compare(char_sequence, opt2):
            return result, []
        return (None, char_sequence)

    def _handle_key_linux(self, key):
        """Maps a key to a string for any character looking into sequences.
            After getch, a sequence is emmitted for special characters.
            Some characters map with a sequence.
        Args:
            key (bytes): ASCII value

        Returns:
            str: key pressed string, None
        """
        # Linux
        if len(self.char_sequence) >= 6:
            self.char_sequence = []
        self.char_sequence.append(ord(key))
        if isinstance(key, bytes):
            enc_key = key
        if isinstance(key, str):
            enc_key = key.encode("utf-8")
            if enc_key == b"":
                self.char_sequence = []
                return None
        if len(self.char_sequence) == 6:
            if self.list_compare(self.char_sequence, [27, 91, 49, 59, 53, 65]):
                self.char_sequence = []
                return CTRL_KEY + ARROW_KEY + "up"  # 27-> 91 -> 49 -> 59 -> 53 -> 65
            if self.list_compare(self.char_sequence, [27, 91, 49, 59, 53, 66]):
                self.char_sequence = []
                return CTRL_KEY + ARROW_KEY + "down"  # 27-> 91 -> 49 -> 59 -> 53 -> 66
            if self.list_compare(self.char_sequence, [27, 91, 49, 59, 53, 67]):
                self.char_sequence = []
                return CTRL_KEY + ARROW_KEY + "right"  # 27-> 91 -> 49 -> 59 -> 53 -> 67
            if self.list_compare(self.char_sequence, [27, 91, 49, 59, 53, 68]):
                self.char_sequence = []
                return CTRL_KEY + ARROW_KEY + "left"  # 27-> 91 -> 49 -> 59 -> 53 -> 68
            out = self.char_sequence[5]
            self.char_sequence = []
            return chr(out)  # 27-> 91 -> 49 -> 59 -> 53 -> X

        elif len(self.char_sequence) == 5:
            if self.list_compare(self.char_sequence, [27, 91, 49, 53, 126]):
                self.char_sequence = []
                return "F5"  # 27-> 91 ->49 ->53 ->126
            if self.list_compare(self.char_sequence, [27, 91, 49, 55, 126]):
                self.char_sequence = []
                return "F6"  # 27-> 91 ->49 ->55 ->126
            if self.list_compare(self.char_sequence, [27, 91, 49, 56, 126]):
                self.char_sequence = []
                return "F7"  # 27-> 91 ->49 ->56 ->126
            if self.list_compare(self.char_sequence, [27, 91, 49, 57, 126]):
                self.char_sequence = []
                return "F8"  # 27-> 91 ->49 ->57 ->126
            if self.list_compare(self.char_sequence, [27, 91, 50, 48, 126]):
                self.char_sequence = []
                return "F9"  # 27-> 91 ->50 ->48 ->126
            if self.list_compare(self.char_sequence, [27, 91, 50, 49, 126]):
                self.char_sequence = []
                return "F10"  # 27-> 91 ->50 ->49 ->126 # os uses this key
            if self.list_compare(self.char_sequence, [27, 91, 50, 51, 126]):
                self.char_sequence = []
                return "F11"  # os uses this key ?????? Assumed
            if self.list_compare(self.char_sequence, [27, 91, 50, 52, 126]):
                self.char_sequence = []
                return "F12"  # 27-> 91 ->50 ->52 ->126

        elif len(self.char_sequence) == 4:
            if self.list_compare(self.char_sequence, [27, 91, 53, 126]):
                self.char_sequence = []
                return "page" + "up"  # 27-> 91 -> 53 -> 126
            if self.list_compare(self.char_sequence, [27, 91, 54, 126]):
                self.char_sequence = []
                return "page" + "down"  # 27-> 91 -> 54 -> 126
            if self.list_compare(self.char_sequence, [27, 91, 51, 126]):
                self.char_sequence = []
                return "delete"  # 27-> 91 -> 51 -> 126
            if self.list_compare(self.char_sequence, [27, 91, 50, 126]):
                self.char_sequence = []
                return "insert"  # 27-> 91 -> 50 -> 126

        elif len(self.char_sequence) == 3:
            if self.list_compare(self.char_sequence, [27, 79, 80]):
                self.char_sequence = []
                return "F1"  # 27-> 79 -> 80
            if self.list_compare(self.char_sequence, [27, 79, 81]):
                self.char_sequence = []
                return "F2"  # 27-> 79 -> 81
            if self.list_compare(self.char_sequence, [27, 79, 82]):
                self.char_sequence = []
                return "F3"  # 27-> 79 -> 82
            if self.list_compare(self.char_sequence, [27, 79, 83]):
                self.char_sequence = []
                return "F4"  # 27-> 79 -> 83
            if self.list_compare(self.char_sequence, [27, 91, 65]):
                self.char_sequence = []
                return ARROW_KEY + "up"  # 27-> 91 -> 65
            if self.list_compare(self.char_sequence, [27, 91, 66]):
                self.char_sequence = []
                return ARROW_KEY + "down"  # 27-> 91 -> 66
            if self.list_compare(self.char_sequence, [27, 91, 67]):
                self.char_sequence = []
                return ARROW_KEY + "right"  # 27-> 91 -> 67
            if self.list_compare(self.char_sequence, [27, 91, 68]):
                self.char_sequence = []
                return ARROW_KEY + "left"  # 27-> 91 -> 68
            if self.list_compare(self.char_sequence, [27, 91, 70]):
                self.char_sequence = []
                return "end"  # 27-> 91 -> 70
            if self.list_compare(self.char_sequence, [27, 91, 72]):
                self.char_sequence = []
                return "home"  # 27-> 91 -> 72

        elif len(self.char_sequence) == 2:
            if self.char_sequence[0] == 27 and self.char_sequence[1] not in [79, 91]:  # esc
                self.char_sequence = []
                return "esc"

        elif self.list_compare(self.char_sequence, [13]):
            self.char_sequence = []
            return "enter"
        elif self.list_compare(self.char_sequence, [127]):
            self.char_sequence = []
            return "backspace"
        elif self.list_compare(self.char_sequence, [9]):
            self.char_sequence = []
            return "tab"
        elif len(self.char_sequence) == 1:
            if self.char_sequence[0] in range(1, 27):
                return CTRL_KEY + chr(96 + self.char_sequence.pop(0))
            if self.char_sequence[0] in range(32, 127):  # printable characters
                return chr(self.char_sequence.pop(0))
            if self.char_sequence[0] not in [27]:
                return chr(self.char_sequence.pop(0))
        else:
            try:
                return chr(ord(key))
            except (NameError, TypeError):
                return ""
        return None

    def _handle_key_windows(self, key):
        """Maps a key to a string for any character looking into sequences.
            After getch, a sequence is emmitted for special characters.
            Some characters map with a sequence.
        Args:
            key (bytes): ASCII value

        Returns:
            str: key pressed string, None
        """
        if len(self.char_sequence) > 2:
            self.char_sequence = []
        self.char_sequence.append(ord(key))

        if len(self.char_sequence) == 2:
            comp_result = None
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 59], [224, 59], result="F1", skip=comp_result
            )  # 0 -> 59
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 60], [224, 60], result="F2", skip=comp_result
            )  # 0 -> 60
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 61], [224, 61], result="F3", skip=comp_result
            )  # 0 -> 61
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 62], [224, 62], result="F4", skip=comp_result
            )  # 0 -> 62
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 63], [224, 63], result="F5", skip=comp_result
            )  # 0 -> 63
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 64], [224, 64], result="F6", skip=comp_result
            )  # 0 -> 64
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 65], [224, 65], result="F7", skip=comp_result
            )  # 0 -> 65
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 66], [224, 66], result="F8", skip=comp_result
            )  # 0 -> 66
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 67], [224, 67], result="F9", skip=comp_result
            )  # 0 -> 67
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 68], [224, 68], result="F10", skip=comp_result
            )  # 0 -> 68
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 133], [0, 133], result="F11", skip=comp_result
            )  # 224 -> 133
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 134], [0, 134], result="F12", skip=comp_result
            )  # 224 -> 134
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 72], [224, 72], result=ARROW_KEY + "up", skip=comp_result
            )  # 0 -> 72
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 80], [224, 80], result=ARROW_KEY + "down", skip=comp_result
            )  # 0 -> 80
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 77], [224, 77], result=ARROW_KEY + "right", skip=comp_result
            )  # 0 -> 77
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 75], [224, 75], result=ARROW_KEY + "left", skip=comp_result
            )  # 0 -> 75
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 141], [0, 141], result=CTRL_KEY + ARROW_KEY + "up", skip=comp_result
            )  # 224 -> 141
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 145], [0, 145], result=CTRL_KEY + ARROW_KEY + "down", skip=comp_result
            )  # 224 -> 145
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 116], [0, 116], result=CTRL_KEY + ARROW_KEY + "right", skip=comp_result
            )  # 224 -> 116
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [224, 115], [0, 115], result=CTRL_KEY + ARROW_KEY + "left", skip=comp_result
            )  # 224 -> 115
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 73], [224, 73], result="page" + "up", skip=comp_result
            )  # 0 -> 73
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 81], [224, 81], result="page" + "down", skip=comp_result
            )  # 0 -> 81
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 83], [224, 83], result="delete", skip=comp_result
            )  # 0 -> 83
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 79], [224, 79], result="end", skip=comp_result
            )  # 0 -> 79
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 71], [224, 71], result="home", skip=comp_result
            )  # 0 -> 71
            comp_result, self.char_sequence = self._get_key_comparison(
                self.char_sequence, [0, 82], [224, 82], result="insert", skip=comp_result
            )  # 0 -> 82
            if comp_result:

                return comp_result

            if not comp_result and self.char_sequence[1] not in [224, 0]:
                out = self.char_sequence[1]
                self.char_sequence = []
                return chr(out)
        comp_result = None
        comp_result, self.char_sequence = self._get_key_comparison(
            self.char_sequence, [13], result="enter", skip=comp_result
        )  # 13
        comp_result, self.char_sequence = self._get_key_comparison(
            self.char_sequence, [8], result="backspace", skip=comp_result
        )  # 8
        comp_result, self.char_sequence = self._get_key_comparison(
            self.char_sequence, [27], result="esc", skip=comp_result
        )  # 27
        comp_result, self.char_sequence = self._get_key_comparison(
            self.char_sequence, [9], result="tab", skip=comp_result
        )  # 9
        if comp_result:
            return comp_result
        if len(self.char_sequence) == 1:
            if self.char_sequence[0] in range(1, 27):
                return CTRL_KEY + chr(96 + self.char_sequence.pop(0))
            if self.char_sequence[0] in range(32, 127):  # printable characters
                return chr(self.char_sequence.pop(0))
            if self.char_sequence[0] not in [0, 224]:
                return chr(self.char_sequence.pop(0))
        else:
            try:
                char = chr(ord(key))
                return char.decode()
                # return chr(ord(key))
            except (NameError, TypeError):
                return key
        return None

    def handle_key(self, key) -> str:
        """Maps a key to a string for special characters ater getch
            Some characters map with a sequence.
        Args:
            last_key (char): last value
            key (char): ASCII value

        Returns:
            str: key pressed string
        """
        if not key:
            return ""
        # Windows
        if os.name == "nt":
            return self._handle_key_windows(key)
        return self._handle_key_linux(key)

    def wait_key_press(self):
        """Returns the key that was pressed and if its special character

        Returns:
            tuple[str,bool]: Key handle, True if special character.
        """
        key_handle = None
        while not key_handle:
            char = getch()
            key_handle = self.handle_key(char)
        special_character = False
        if len(key_handle) > 1:  # words with more than 1 character is special character
            special_character = True
        return key_handle, special_character

    def wait_specific_key_press(self, key="enter"):
        """Returns only when the specific key is pressed. Blocks the thread.

        Returns:
            tuple[str,bool]: Key handle, True if special character.
        """
        while True:
            key_handle, special_character = self.wait_key_press()
            if key_handle.lower() == key.lower():
                return key_handle, special_character
            if self.verbose:
                print(f"You pressed '{key_handle}' not '{key}'")

    def _get_input_verbosed(self, key_handle, is_special_character):
        """when verbosed"""
        os.system("cls" if os.name == "nt" else "clear")
        # Print prompt
        print(self.prompt)
        if key_handle == "enter":
            return (self.line_autocompleted, True)
        if key_handle == "tab":
            self.line_user_input = self.autocomplete_path(self.line_user_input)
            print(self.options)
            key_handle = None
        elif key_handle == "esc":
            return (None, True)
        elif key_handle == "backspace":
            lenght = len(self.line_user_input)
            self.line_user_input = self.line_user_input[: lenght - 1]
            lenght = len(self.line_user_input)
        else:
            if key_handle and not is_special_character:
                self.line_user_input = self.line_user_input + key_handle
        print(self.line_user_input)
        self.line_autocompleted = self.line_user_input
        return (self.line_autocompleted, False)

    def _get_input_not_verbosed(self, key_handle, is_special_character, pos, lenght, lenoptions):
        """when not verbosed"""
        if lenoptions > 0:
            for _ in range(1, lenoptions):
                self._sys_write_flush("\b ", True)
                self._sys_write_flush("\b", False)
            self._sys_write_flush("\r", True)
            self._sys_write_flush(self.line_user_input, True)
            lenoptions = 0
        if key_handle == "enter":
            self._sys_write_flush("\r", True)
            return (self.line_autocompleted, True, pos, lenght, lenoptions)
        elif key_handle == "tab":
            inlen = len(self.line_user_input)
            self.line_user_input = self.autocomplete_path(self.line_user_input)
            self._sys_write_flush("\b" * inlen + self.line_user_input, True)
            lenoptions = len(self.options)
            if lenoptions > 0:
                self._sys_write_flush(self.options, True)
            key_handle = None
        elif key_handle == "esc":
            return (None, True, pos, lenght, lenoptions)
        elif key_handle == "backspace":
            lenght = len(self.line_user_input)
            self.line_user_input = self.line_user_input[: lenght - 1]
            lenght = len(self.line_user_input)
            self._sys_write_flush("\b ", True)
            self._sys_write_flush("\b", False)
        else:
            pos = pos + 1
            if key_handle and not is_special_character:
                self.line_user_input = self.line_user_input + key_handle
                self._sys_write_flush(key_handle, True)
        self.line_autocompleted = self.line_user_input
        return (self.line_autocompleted, False, pos, lenght, lenoptions)

    def get_input(self):
        """Get user input.

        Returns:
            str: User input
        """
        pos = 0
        lenght = 0
        lenoptions = 0
        while True:
            key_handle, is_special_character = self.wait_key_press()
            if self.verbose:
                return_val, do_return = self._get_input_verbosed(key_handle, is_special_character)
            else:
                return_val, do_return, pos, lenght, lenoptions = self._get_input_not_verbosed(
                    key_handle, is_special_character, pos, lenght, lenoptions
                )
            if do_return:
                return return_val

    @staticmethod
    def _sys_write_flush(msg, do_flush=True):
        """Do sys.stdout.write(msg) and  sys.stdout.flush()"""
        sys.stdout.write(msg)
        if do_flush:
            sys.stdout.flush()
    
    @staticmethod
    def insert_char_at_pos(text, char, pos):
        """
        Inserts a character at a specified position in a given text.

        Args:
            text (str): The original text.
            char (str): The character to be inserted.
            pos (int): The position where the character should be inserted.

        Returns:
            str: The modified text with the character inserted.
        """
        return text[:pos] + char + text[pos:]
    
    @staticmethod
    def remove_char_at_pos(text, pos):
        """
        Inserts a character at a specified position in a given text.

        Args:
            text (str): The original text.
            char (str): The character to be inserted.
            pos (int): The position where the character should be inserted.

        Returns:
            str: The modified text with the character inserted.
        """
        return text[:pos-1] + text[pos:]
    
    @staticmethod
    def remove_ansi(txt: str) -> str:
        """
        Removes ANSI escape codes from styled text.

        Args:
            txt (str): The input string with ANSI escape codes.

        Returns:
            str: The unstyled text without ANSI escape codes.
        """
        pattern = r'\\033(?:[@-Z\\]|\[[0-?]*[ -/]*m)'
        return re.sub(pattern, '', txt)
    
    @staticmethod
    def add_ansi(txt: str, code: str) -> str:
        """
        Adds ANSI escape codes to style text.

        Args:
            txt (str): The input string.
            code (str): A single character representing a styling option. 
                        Supported options are:
                        'normal','bold','italic','underline',
                        'inverse'(white on black background),
                        'reverse'(black on white background),
                        'clear' (Clear the current line and move to the beginning of it),
                        'next' (Move to the next line without clearing the previous one)
                        Color Options:
                        'gray','red','green','yellow','blue','magenta','cyan','white'
                        f+color= foreground color
                        h+color= highligted color
                        
        Returns:
            str: The styled text with ANSI escape codes.
        """
        # Define a dictionary to map single character codes to their full form
        style_codes = {
            'normal': '\033[0m', #normal
            'bold': '\033[1m', #bold
            'italic': '\033[3m', #italic
            'underline': '\033[4m',  #underline
            'inverse': '\033[7m', #  Inverse (white on black background)
            'reverse': '\033[9m',# \033[9m: Reversed (black on white background)
            'clear':'\033[K',# Clear the current line and move to the beginning of it.
            'next':'\033[J', # Move to the next line without clearing the previous one.
        }
        end_style_code = style_codes['normal']
        if not code:
            return txt
        code=code.lower()
        if code in style_codes.keys():
            return style_codes[code]+txt+end_style_code
        # Add the color codes for red, green and yellow
        colors = {
            'gray':0,
            'red':1,
            'green':2,
            'yellow':3,
            'blue':4,
            'magenta':5,
            'cyan':6,
            'white':7,   
        }
        if code in colors.keys():
            return f'\033[{colors[code]+30}m' + txt + end_style_code
        for color,val in colors.items():
            if code == 'f'+color:
                return f'\033[{colors[color]+40}m' + txt + end_style_code
            if code == 'h'+color:
                return f'\033[{colors[color]+90}m' + txt + end_style_code
        return txt


    @staticmethod
    def highlight_cursor(text:str, pos:int)->str:
        """
        Highlights a specific position in text.
        Args:
            text (str): The string containing the highlighted character.
            pos (int): The position of the character to be highlighted.
        Returns:
            str: ANSI highlighted cursor string
        """
        ini_txt=''
        hl_txt=''
        end_txt=''
        index=pos-1
        lentxt=len(text)
        if lentxt>0 and index>0:
            if index+1>=lentxt:
                ini_txt=text
                hl_txt=''
                end_txt=''
            else:
                ini_txt=text[:-(lentxt-index-1)]
                hl_txt=text[index+1]
                if index+1>lentxt:
                    end_txt=''
                else:
                    end_txt=text[(index+2):]
        return f"\033[1m{ini_txt}\033[6m\033[4;36m{hl_txt}\033[0m{end_txt}"

if __name__ == "__main__":
    AC = AutocompletePathFile(
        "return string (ENTER), Autofill path/file (TAB), Cancel (ESC) Paste (CTRL+V)\nPlease type path: ",
        APP_PATH,
        False,
        verbose=False,
        inquire=False,
    )
    input_path = AC.get_input
    my_path = input_path()
    print("User input:", my_path)

    def test_handle():
        """To see internally the keyboard mapping sequences"""
        while True:
            print("Map keys: press enter to exit")
            char = getch()
            if isinstance(char, str):  # linux
                print(
                    type(char), "Here->", char, "str->", str(char), "ord->", ord(char), "encode->", char.encode("utf-8")
                )
            if isinstance(char, bytes):  # windows
                print(type(char), "Here->", char, "str->", str(char), "ord->", ord(char), "encode->", char)
            # os.system('cls' if os.name == 'nt' else 'clear')
            print(f"Sequence before:{AC.char_sequence}")
            key_handle = AC.handle_key(char)
            print(f"Sequence After:{AC.char_sequence}")
            print("Char: ", chr(ord(char)), " ord:", ord(char), "keyhandle=", key_handle)
            if char in [b"\r", b"\n", "\r", "\n"] or key_handle == "enter":
                return

    def test_handle2():
        """Teste wait key press"""
        while True:
            print("Map keys: press enter to exit")
            key_handle, is_special_character = AC.wait_key_press()
            print("keyhandle=", key_handle, "is_special_character:", is_special_character)
            if key_handle == "enter":  # enter
                return

    def test_raw_key():
        """Test raw keys"""
        print("Press key to print: ctrl+c to exit -> \\x03")
        akey = ""
        while akey != "\\x03":
            akey = get_raw_key(True)
            print(AC.raw_key_to_key_handle(akey))

    test_handle()
    test_handle2()
    test_raw_key()
