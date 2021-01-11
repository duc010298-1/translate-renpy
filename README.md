# TranslateRenPy
TranslateRenPy

Author: duc010298

## Features

- Unlimited number of characters to be translated
- Using selenium to translate (no need Yandex API key or Google Cloud Services - free for all)
- Automatically override available languages (you do not need renpy sdk to Generate Translations)
- Automatically ignores variables or special characters during translation:
    ### Example
    1. `[earnings]` is kept after translation
        ```
        # m "OK, let's check the school's account. The school's owners have transferred me [earnings] credits."
        m "OK, vérifions le compte de l'école. Les propriétaires de l'école m'ont transféré [earnings] crédits."
        ```
    2. `\n` (break line) is kept after translation
        ```
        old "Loading will lose unsaved progress.\nAre you sure you want to do this?"
        new "Le chargement perdra la progression non enregistrée.\nEs-tu sûr de vouloir faire ça?"
        ```
    3. `%s` is kept after translation
        ```
        old "Saved screenshot as %s."
        new "Capture d'écran enregistrée sous %s."
        ```
    And some other special cases

## Quick Start

### Installation instructions

1. Install Python

    You need Python 3 or later to run translate-renpy
    
    For Windows, packages are available at
    
    https://www.python.org/getit/

2. Install requirements

    Clone or download zip source code, open Command line in source code folder
    
    Install requirements using `pip`:
    
        pip install -r requirements.txt

3. Install Driver

    You should instal Chrome browser and check your browser version
    
    And then download ChromeDriver suitable for your browser at: [chromedriver.chromium.org](https://chromedriver.chromium.org/)
    
    After downloaded, extract it, copy and rewrite `chromedriver` to folder `Driver\[your_os]` in source code folder

### Usage

1. First you need generate RenPy translations

    You can read and follow Generate RenPy translations section on this post: 
    
    [F95 RenPy Translation tool](https://f95zone.to/threads/renpy-translation-tool.21920/)

    ** Note: Some games do not compile rpyc files. If in the folder `[your_game]\game\tl\[language]` there are many files with .rpy extension look like on screen below, you can skip this step.
    
    ![preview](https://i.imgur.com/qwSUosi.png)
    
2. To open help menu, open command line in source code folder and run:

    `python trans-ren.py --help`
    
    Help menu may show look like below:
    
       usage: trans-ren.py [-h] [-v] -d <path> -i <language> -o <language> -t <number> [-sb]

       TransRen: Translate your Renpy game into any language

       optional arguments:
          -h, --help           show this help message and exit
          -v, --version        show version and exit.

       program arguments:
          -d <path>            directory path containing the .rpy file
          -i <language>        the language you want to translate from
          -o <language>        the language you want to translate into
          -t <number>          number of thread (many threads will take high CPU)
          -sb, --show-browser  show browser while translating (show browser windows can take high RAM)

       For more information, visit https://github.com/duc010298-1/translate-renpy

    `-d` For directory, this is directory of your transitions folder 
    
    `-i` `-o` For input language and output language, you should go to [cloud.google.com/translate/docs/languages](https://cloud.google.com/translate/docs/languages) and find `ISO-639-1 Code` of your language
    
    `-t` For number of thread, this is the number of browser tabs the tool will open simultaneously (I recommended 4 for 8Gb Ram)
    
    If you want to see the process live, you can add `-sb` (show browser) to your command
### Examples
    
- Transitions folder: `D:\Game\My_cute_roommate-1.6.1ex-win\game\tl\english`
- Language you want to translate from: `english`
- Language you want to translate into: `vietnamese`
- Command should use:

      python trans-ren.py -d "D:\Game\My_cute_roommate-1.6.1ex-win\game\tl\english" -i en -o vi -t 4 -sb

### Demo
In short, I deleted some files in the Transitions folder to make the translation faster

[Demo](https://imgur.com/26O2xlr.gif)

### Help me
- Please Star this github repository if it is of help to you
