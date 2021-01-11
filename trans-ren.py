import re
import io
import os
import threading
import shutil
import time
import argparse
import validators
from sys import platform
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


PROGRAM_NAME = "Trans Ren"
VERSION = "1.0"
DESCRIPTION = "TransRen: Translate your Renpy game into any language"
EPILOG = "For more information, visit https://github.com/duc010298-1/translate-renpy"

XPATH_INPUT = "/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz[1]/span/span/div/textarea"
XPATH_OF_TEXTBOX = "/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz[2]/div[5]/div/div[1]/span[1]/span/span"
XPATCH_OF_DELETE_BUTTON = "/html/body/c-wiz/div/div[2]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[2]/c-wiz[1]/div[2]/div/div/span/button"
MERGED_FILE_FOLDER = "temp1"
BLOCK_TRANSLATED_FOLDER = "temp2"
MERGED_RPY_FILE = "temp.txt"
MERGED_BLOCK_FILE = "output-temp.txt"
SIGN_BREAK_FILE = "ThisIsSomeRandomString"
MAX_CHAR_IN_THREAD = 1000
MAX_TIME_WAIT_ELEMENT = 3
DRIVER_PATH_WIN = "Driver/Win/chromedriver.exe"
DRIVER_PATH_LINUX = "Driver/Linux/chromedriver"
DRIVER_PATH_MAC = "Driver/Mac/chromedriver"
LANGUAGE_SUPPORT = ["af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca", "ceb", "zh-CN", "zh-TW", "co", "hr", "cs",
                    "da", "nl", "en", "eo", "et", "fi", "fr", "fy", "gl", "ka", "de", "el", "gu", "ht", "ha", "haw", "he", "hi", "hmn",
                    "hu", "is", "ig", "id", "ga", "it", "ja", "jv", "kn", "kk", "km", "rw", "ko", "ku", "ky", "lo", "la", "lv", "lt",
                    "lb", "mk", "mg", "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no", "ny", "or", "ps", "fa", "pl", "pt", "pa",
                    "ro", "ru", "sm", "gd", "sr", "st", "sn", "sd", "si", "sk", "sl", "so", "es", "su", "sw", "sv", "tl", "tg", "ta",
                    "tt", "te", "th", "tr", "tk", "uk", "ur", "ug", "uz", "vi", "cy", "xh", "yi", "yo", "zu"]
WEB_DRIVER_OPTIONS = webdriver.ChromeOptions()

# Global variable
current_location = None
lock = threading.Lock()
dialogue_thread_done = []
total_cluster_translate = []


class CurrentLocation:
    def __init__(self, index, offset):
        self.index = index
        self.offset = offset


class WhitespaceObject:
    def __init__(self, whitespace_begin, whitespace_end):
        self.whitespace_begin = whitespace_begin
        self.whitespace_end = whitespace_end


class ClusterUnit:
    def __init__(self, text, is_translate, whitespace_obj):
        self.text = text
        self.is_translate = is_translate
        self.whitespace_obj = whitespace_obj


class LineUnit:
    def __init__(self, text, clusters_unit):
        self.text = text
        self.clusters_unit: ClusterUnit = clusters_unit


class BlockUnit:
    def __init__(self, index, raw_text, lines_unit):
        self.index = index
        self.raw_text = raw_text
        self.lines_unit: LineUnit = lines_unit


def build_web_driver_options(show_browser):
    if not show_browser:
        WEB_DRIVER_OPTIONS.add_argument("--headless")
    WEB_DRIVER_OPTIONS.add_argument("--no-sandbox")
    WEB_DRIVER_OPTIONS.add_argument("--disable-gpu")
    WEB_DRIVER_OPTIONS.add_argument("--log-level=3")
    WEB_DRIVER_OPTIONS.add_argument("--disable-extensions")
    WEB_DRIVER_OPTIONS.add_argument("disable-infobars")
    WEB_DRIVER_OPTIONS.add_argument("--window-size=500,420")


def clear_console():
    # TODO check system is linux
    return os.system('cls')


def is_directory_exists(directory_path):
    return os.path.exists(directory_path)


def get_rpy_files_in_directory(directory_path):
    files = []
    for f in os.listdir(directory_path):
        full_path = os.path.join(directory_path, f)
        if os.path.isfile(full_path) and f.endswith(".rpy"):
            files.append(full_path)
    return files


def merge_files(files):
    with open("{}\\{}".format(MERGED_FILE_FOLDER, MERGED_RPY_FILE), "w", encoding="utf-8") as temp_file:
        for file in files:
            temp_file.write("{}{}{}\n".format(
                SIGN_BREAK_FILE, file, SIGN_BREAK_FILE))
            with open(file, "r", encoding="utf8") as f:
                for line in f:
                    temp_file.write(line)
            temp_file.write("{}\n".format(SIGN_BREAK_FILE))


def count_substring_in_string(sub, str):
    return str.count(sub)


def get_content_from_raw(raw_line):
    result = ""
    is_start = False
    for i in range(len(raw_line), 0, -1):
        if raw_line[i-1] == '"':
            if not is_start:
                is_start = True
                continue
            if raw_line[i-2] != '\\':
                return result[::-1].replace('\n', '')
        result += raw_line[i-1]


def get_whitespace_begin_and_end(text):
    if text.count(" ") == len(text):
        return WhitespaceObject(text, "")
    whitespace_begin = ""
    whitespace_end = ""
    for c in text:
        if c != " ":
            break
        whitespace_begin += c
    for c in text[::-1]:
        if c != " ":
            break
        whitespace_end += c
    return WhitespaceObject(whitespace_begin, whitespace_end)


def break_clusters(content):
    clusters_unit = []
    temp = ""
    stop_scan_type = None
    for i in range(len(content)):
        if stop_scan_type is None:
            if content[i] == "[":
                stop_scan_type = 1
            if content[i] == "{":
                stop_scan_type = 2
            if content[i] == "\\" and content[i+1] == '"':
                stop_scan_type = 3
            if content[i] == "\\" and content[i+1] == "[":
                stop_scan_type = 4
            if content[i] == "\\" and content[i+1] == "]":
                stop_scan_type = 5
            if content[i] == "\\" and content[i+1] == "{":
                stop_scan_type = 6
            if content[i] == "\\" and content[i+1] == "}":
                stop_scan_type = 7
            if len(content) >= 2 and content[i] == "%" and content[i+1] != ".":
                stop_scan_type = 8
            if len(content) >= 4 and content[i] == "%" and content[i+1] == ".":
                stop_scan_type = 9
            if content[i] == "\\" and content[i+1] == "n":
                stop_scan_type = 10
            if stop_scan_type is not None:
                if temp != "":
                    whitespace_obj = get_whitespace_begin_and_end(temp)
                    clusters_unit.append(ClusterUnit(
                        temp.strip(), True, whitespace_obj))
                    temp = ""
        else:
            if (stop_scan_type == 1 and content[i] == "]") or (stop_scan_type == 2 and content[i] == "}") \
                    or (stop_scan_type == 3 and content[i-1] == "\\" and content[i] == '"') \
                    or (stop_scan_type == 4 and content[i-1] == "\\" and content[i] == '[') \
                    or (stop_scan_type == 5 and content[i-1] == "\\" and content[i] == ']') \
                    or (stop_scan_type == 6 and content[i-1] == "\\" and content[i] == '{') \
                    or (stop_scan_type == 7 and content[i-1] == "\\" and content[i] == '}') \
                    or (stop_scan_type == 8 and content[i-1] == "%") \
                    or (stop_scan_type == 9 and content[i-2] == "." and content[i-3] == "%") \
                    or (stop_scan_type == 10 and content[i-1] == "\\" and content[i] == 'n'):
                stop_scan_type = None
                if temp != "":
                    temp += content[i]
                    whitespace_obj = get_whitespace_begin_and_end(temp)
                    clusters_unit.append(ClusterUnit(
                        temp.strip(), False, whitespace_obj))
                    temp = ""
                    continue
        temp += content[i]
    if temp != "":
        whitespace_obj = get_whitespace_begin_and_end(temp)
        clusters_unit.append(ClusterUnit(temp.strip(), True, whitespace_obj))
    return clusters_unit


def break_blocks(current_location: CurrentLocation):
    if current_location.offset == -1:
        return None
    current_location.index += 1
    with open("{}\\{}".format(MERGED_FILE_FOLDER, MERGED_RPY_FILE), "r", encoding="utf8") as f:
        f.seek(current_location.offset)
        temp_str = ""
        line_units = []
        is_source_line = True
        while True:
            line = f.readline()
            if not line:
                break
            temp_str += line
            if count_substring_in_string('"', line) > 0:
                if is_source_line:
                    content = get_content_from_raw(line)
                    line_units.append(
                        LineUnit(content, break_clusters(content)))
                else:
                    if len(temp_str + line) > MAX_CHAR_IN_THREAD:
                        current_location.offset = f.tell()
                        return BlockUnit(current_location.index, temp_str, line_units)
                is_source_line = not is_source_line
    current_location.offset = -1
    return BlockUnit(current_location.index, temp_str, line_units)


def translate(txt, input_text_area, wait):
    if len(txt) <= 1 or validators.url(txt):
        return txt
    if ("with fade" in txt) or ("with dissolve" in txt) or ("with pixellate" in txt) \
            or ("with move" in txt) or ("with moveinright" in txt) or ("with moveoutright" in txt) or ("with ease" in txt) \
            or ("with zoomin" in txt) or ("with zoomout" in txt) or ("with zoominout" in txt) or ("with vpunch" in txt) \
            or ("with hpunch" in txt) or ("with blinds" in txt) or ("with squares" in txt) or ("with wipeleft" in txt) \
            or ("with slideleft" in txt) or ("with slideawayleft" in txt) or ("with pushright" in txt) or ("with irisin" in txt) \
            or ("with moveinleft" in txt) or ("with moveintop" in txt) or ("with moveinbottom" in txt) or ("with moveoutleft" in txt) \
            or ("with moveouttop" in txt) or ("with moveoutbottom" in txt) or ("with easeinright" in txt) or ("with easeinleft" in txt) \
            or ("with easeintop" in txt) or ("with easeinbottom" in txt) or ("with easeoutright" in txt) or ("with easeoutleft" in txt) \
            or ("with easeouttop" in txt) or ("with easeoutbottom" in txt) or ("with wiperight" in txt) or ("with wipeup" in txt) \
            or ("with wipedown" in txt) or ("with slideright" in txt) or ("with slideup" in txt) or ("with slidedown" in txt) \
            or ("with slideawayright" in txt) or ("with slideawayup" in txt) or ("with slideawaydown" in txt) or ("with pushleft" in txt) \
            or ("with pushup" in txt) or ("with pushdown" in txt) or ("with irisout" in txt) or ("with fdissolve" in txt):
        return ""
    result = ""
    input_text_area.send_keys(txt)

    is_translate_ok = False
    for x in range(0, 30):
        try:
            # wait text availible
            result = wait.until(
                EC.element_to_be_clickable((By.XPATH, XPATH_OF_TEXTBOX))
            ).text
            is_translate_ok = True
        except:
            input_text_area.send_keys(".")
            result = txt
        if is_translate_ok:
            break
    if not is_translate_ok:
        print("Error: Cannot translate text")

    is_clear_ok = False
    for x in range(0, 30):
        try:
            wait.until(
                EC.element_to_be_clickable((By.XPATH, XPATCH_OF_DELETE_BUTTON))
            ).click()
            is_clear_ok = True
        except:
            try:
                input_text_area.clear()
                is_clear_ok = True
            except:
                is_clear_ok = False
        if is_clear_ok:
            break
    if not is_translate_ok:
        print("Error: Cannot clear text area")
    return result.replace("<span title class>", "").replace("</span>", "").replace('"', "'")


def process_line(line_unit: LineUnit):
    line_unit.text += " - "
    line_unit.text = line_unit.text.replace('with fade', '')
    line_unit.text = line_unit.text.replace('with dissolve', '')
    line_unit.text = line_unit.text.replace('with pixellate', '')
    line_unit.text = line_unit.text.replace('with move', '')
    line_unit.text = line_unit.text.replace('with moveinright', '')
    line_unit.text = line_unit.text.replace('with moveoutright', '')
    line_unit.text = line_unit.text.replace('with ease', '')
    line_unit.text = line_unit.text.replace('with zoomin', '')
    line_unit.text = line_unit.text.replace('with zoomout', '')
    line_unit.text = line_unit.text.replace('with zoominout', '')
    line_unit.text = line_unit.text.replace('with vpunch', '')
    line_unit.text = line_unit.text.replace('with hpunch', '')
    line_unit.text = line_unit.text.replace('with blinds', '')
    line_unit.text = line_unit.text.replace('with squares', '')
    line_unit.text = line_unit.text.replace('with wipeleft', '')
    line_unit.text = line_unit.text.replace('with slideleft', '')
    line_unit.text = line_unit.text.replace('with slideawayleft', '')
    line_unit.text = line_unit.text.replace('with slideawayleft', '')
    line_unit.text = line_unit.text.replace('with pushright', '')
    line_unit.text = line_unit.text.replace('with irisin', '')
    line_unit.text = line_unit.text.replace('with moveinleft', '')
    line_unit.text = line_unit.text.replace('with moveintop', '')
    line_unit.text = line_unit.text.replace('with moveinbottom', '')
    line_unit.text = line_unit.text.replace('with moveoutleft', '')
    line_unit.text = line_unit.text.replace('with moveouttop', '')
    line_unit.text = line_unit.text.replace('with moveoutbottom', '')
    line_unit.text = line_unit.text.replace('with easeinright', '')
    line_unit.text = line_unit.text.replace('with easeinleft', '')
    line_unit.text = line_unit.text.replace('with easeintop', '')
    line_unit.text = line_unit.text.replace('with easeinbottom', '')
    line_unit.text = line_unit.text.replace('with easeoutright', '')
    line_unit.text = line_unit.text.replace('with easeoutleft', '')
    line_unit.text = line_unit.text.replace('with easeouttop', '')
    line_unit.text = line_unit.text.replace('with easeoutbottom', '')
    line_unit.text = line_unit.text.replace('with wiperight', '')
    line_unit.text = line_unit.text.replace('with wipeup', '')
    line_unit.text = line_unit.text.replace('with wipedown', '')
    line_unit.text = line_unit.text.replace('with slideright', '')
    line_unit.text = line_unit.text.replace('with slideup', '')
    line_unit.text = line_unit.text.replace('with slidedown', '')
    line_unit.text = line_unit.text.replace('with slideawayright', '')
    line_unit.text = line_unit.text.replace('with slideawayup', '')
    line_unit.text = line_unit.text.replace('with slideawaydown', '')
    line_unit.text = line_unit.text.replace('with pushleft', '')
    line_unit.text = line_unit.text.replace('with pushup', '')
    line_unit.text = line_unit.text.replace('with pushdown', '')
    line_unit.text = line_unit.text.replace('with irisout', '')
    line_unit.text = line_unit.text.replace('with fdissolve', '')
    for cluster in line_unit.clusters_unit:
        line_unit.text += "{}{}{}".format(
            cluster.whitespace_obj.whitespace_begin,
            cluster.text,
            cluster.whitespace_obj.whitespace_end
        )


def process_block(block_unit: BlockUnit, input_text_area, wait, thread_index):
    global total_cluster_translate
    old_before_translate = ""
    old_after_translate = ""
    for line in block_unit.lines_unit:
        for cluster in line.clusters_unit:
            if not cluster.is_translate:
                continue
            temp = cluster.text
            if cluster.text == old_before_translate:
                cluster.text = old_after_translate
                continue
            else:
                cluster.text = translate(cluster.text, input_text_area, wait)
                old_after_translate = cluster.text
            old_before_translate = temp
            total_cluster_translate[thread_index] += 1
    for line in block_unit.lines_unit:
        process_line(line)


def check_have_old_translate_content(line):
    if get_content_from_raw(line) != "":
        return True
    else:
        return False


def remove_old_translate_content(line):
    is_start = False
    start_index = 0
    for i in range(len(line), 0, -1):
        if line[i-1] == '"':
            if not is_start:
                start_index = i
                is_start = True
                continue
            if line[i-2] != '\\':
                return line[0:i] + line[start_index-1::]


def write_block_unit(block_unit: BlockUnit, thread_index):
    global dialogue_thread_done
    index = 0
    with open("{}\\{}".format(BLOCK_TRANSLATED_FOLDER, block_unit.index), "w", encoding="utf-8") as trans_temp:
        is_source_line = True
        buf = io.StringIO(block_unit.raw_text)
        for line in buf:
            if count_substring_in_string('"', line) > 0:
                if not is_source_line:
                    if check_have_old_translate_content(line):
                        line = remove_old_translate_content(line)
                    line = line.replace('""', '"{}"'.format(
                        block_unit.lines_unit[index].text))
                    index += 1
                    dialogue_thread_done[thread_index] += 1
                is_source_line = not is_source_line
            trans_temp.write(line)


def count_file_in_folder(directory_path):
    count = 0
    for f in os.listdir(directory_path):
        full_path = os.path.join(directory_path, f)
        if os.path.isfile(full_path):
            count += 1
    return count


def merge_translated_blocks():
    print("--")
    print("Merge the translated blocks...")
    total_temp_file = count_file_in_folder(BLOCK_TRANSLATED_FOLDER)
    with open("{}\\{}".format(MERGED_FILE_FOLDER, MERGED_BLOCK_FILE), "w", encoding="utf-8") as output_file:
        for i in range(total_temp_file):
            with open("{}\\{}".format(BLOCK_TRANSLATED_FOLDER, i+1), "r", encoding="utf8") as f:
                for line in f:
                    output_file.write(line)
    print("-------------Merge completed-------------")


def runner(thread_index, input_lang, output_lang, driver_path):
    global current_location
    with webdriver.Chrome(executable_path=driver_path, options=WEB_DRIVER_OPTIONS) as driver:
        driver.get(
            "https://translate.google.com/?hl={input_lang}#{input_lang}/{output_lang}/".format(
                input_lang=input_lang,
                output_lang=output_lang
            )
        )
        driver.execute_script(
            "document.title = 'Thread {}'".format(thread_index + 1))
        input_text_area = driver.find_element(By.XPATH, XPATH_INPUT)
        wait = WebDriverWait(driver, MAX_TIME_WAIT_ELEMENT)
        while True:
            block_unit = None
            with lock:
                block_unit = break_blocks(current_location)
            if block_unit is None:
                break
            process_block(block_unit, input_text_area, wait, thread_index)
            write_block_unit(block_unit, thread_index)
            if current_location.offset == -1:
                break


def monitoring_process(total_dialogue):
    global dialogue_thread_done
    global total_cluster_translate
    while True:
        clear_console()
        total = sum(dialogue_thread_done)
        print("Total dialogue: {}".format(int(total_dialogue)))
        print("Process: {}/{}".format(total, int(total_dialogue)))
        print("-----------------------------------------")
        for i in range(len(total_cluster_translate)):
            print("Total translated on thread {}: {}".format(
                i + 1, total_cluster_translate[i]))
        print("-----------------------------------------")
        for i in range(len(dialogue_thread_done)):
            print("Total dialogue done on thread {}: {}".format(
                i + 1, dialogue_thread_done[i]))
        time.sleep(1)
        if total == total_dialogue:
            print("----------Translation completed----------")
            break


def count_string_have_char(char, sourceFile):
    count = 0
    with open(sourceFile, "r", encoding="utf-8") as f:
        for line in f:
            if count_substring_in_string(char, line) > 0:
                count += 1
    return count


def delete_temp_folder():
    if os.path.exists(MERGED_FILE_FOLDER):
        shutil.rmtree(MERGED_FILE_FOLDER, ignore_errors=True)
    if os.path.exists(BLOCK_TRANSLATED_FOLDER):
        shutil.rmtree(BLOCK_TRANSLATED_FOLDER, ignore_errors=True)


def create_temp_folder():
    if not os.path.exists(MERGED_FILE_FOLDER):
        os.mkdir(MERGED_FILE_FOLDER)
    if not os.path.exists(BLOCK_TRANSLATED_FOLDER):
        os.mkdir(BLOCK_TRANSLATED_FOLDER)


def build_rpy_file():
    print("--")
    print("Building rpy file...")
    current_rpy_file_path = ""
    with open("{}\\{}".format(MERGED_FILE_FOLDER, MERGED_BLOCK_FILE), "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                break
            if count_substring_in_string(SIGN_BREAK_FILE, line) == 2:
                current_rpy_file_path = re.search(
                    "{}(.*){}".format(SIGN_BREAK_FILE, SIGN_BREAK_FILE), line).group(1)
                with open(current_rpy_file_path, "w", encoding="utf-8") as rpy_filefile:
                    while True:
                        line = f.readline()
                        if not line or count_substring_in_string(SIGN_BREAK_FILE, line) == 1:
                            break
                        rpy_filefile.write(line)
    print("-------Rpy file building completed-------")


def main(args):
    driver_path = ""
    if platform == "linux" or platform == "linux2":
        driver_path = DRIVER_PATH_LINUX
    elif platform == "darwin":
        driver_path = DRIVER_PATH_MAC
    elif platform == "win32":
        driver_path = DRIVER_PATH_WIN

    build_web_driver_options(args.show_browser)
    start = time.time()
    global current_location
    global dialogue_thread_done
    global total_cluster_translate
    delete_temp_folder()
    create_temp_folder()
    current_location = CurrentLocation(0, 0)
    merge_files(get_rpy_files_in_directory(args.input_directory))

    total_dialogue = count_string_have_char(
        '"', "{}\\{}".format(MERGED_FILE_FOLDER, MERGED_RPY_FILE)) / 2

    threads = []
    for i in range(args.number_of_thread):
        threads.append(threading.Thread(
            target=runner, args=(i, args.input_lang, args.output_lang, driver_path)))
        dialogue_thread_done.append(0)
        total_cluster_translate.append(0)
        threads[i].start()

    monitoring_process(total_dialogue)
    merge_translated_blocks()
    build_rpy_file()
    delete_temp_folder()
    end = time.time()
    print("--")
    print("All done at: {}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
    print("Total time: {}".format(time.strftime(
        '%H:%M:%S', time.gmtime(end - start))))


def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def check_args(args):
    if not is_directory_exists(args.input_directory):
        print("Error: The directory does not exist")
        return False
    if not args.input_lang in LANGUAGE_SUPPORT:
        print("Error: '{}' is not a supported language".format(args.input_lang))
        print("Please visit https://cloud.google.com/translate/docs/languages to refer ISO-639-1 Code")
        return False
    if not args.output_lang in LANGUAGE_SUPPORT:
        print("Error: '{}' is not a supported language".format(args.output_lang))
        print("Please visit https://cloud.google.com/translate/docs/languages to refer ISO-639-1 Code")
        return False
    if not represents_int(args.number_of_thread) or int(args.number_of_thread) < 1:
        print("Error: Number of thread must be number > 0")
        return False
    args.input_directory = args.input_directory.strip()
    args.number_of_thread = int(args.number_of_thread)
    args.input_lang = args.input_lang.strip()
    args.output_lang = args.output_lang.strip()
    return True


def cli():
    parser = argparse.ArgumentParser(
        description=DESCRIPTION,
        epilog=EPILOG
    )
    program_arguments = parser.add_argument_group('program arguments')

    # set version arg
    parser.add_argument(
        "-v", "--version", help="show version and exit.",
        action="version", version="{} version {}".format(PROGRAM_NAME, VERSION)
    )

    program_arguments.add_argument(
        "-d", help="directory path containing the .rpy file",
        dest="input_directory", action="store", metavar="<path>", required=True
    )
    program_arguments.add_argument(
        "-i", help="the language you want to translate from",
        dest="input_lang", action="store", metavar="<language>", required=True
    )
    program_arguments.add_argument(
        "-o", help="the language you want to translate into",
        dest="output_lang", action="store", metavar="<language>", required=True
    )
    program_arguments.add_argument(
        "-t", help="number of thread (many threads will take high CPU)",
        dest="number_of_thread", action="store", metavar="<number>", required=True
    )
    program_arguments.add_argument(
        "-sb", "--show-browser", help="show browser while translating (show browser windows can take high RAM)",
        dest="show_browser", action="store_true"
    )

    args = parser.parse_args()

    if check_args(args):
        main(args)


cli()
