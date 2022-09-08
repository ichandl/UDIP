@echo off
::Place Path to the Main GS Folder Here::
cd C:\Users\esack\Desktop\Code\UDIP\GS_Code_2023

::Translate from Designer File to Python File::
start cmd.exe /c python -m PyQt5.uic.pyuic -x gui_layout.ui -o gui_layout.py