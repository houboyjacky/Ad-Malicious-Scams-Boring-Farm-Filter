@echo off
pipdeptree > "Python_Tree.txt"
pip list -o > "Python_Upgrade.txt"
