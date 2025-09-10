@echo off
REM Simple Windows runner for GUI tests
setlocal
python -m unittest -v gui_content_dse.tests.test_gui gui_content_dse.tests.test_gui_yaml
endlocal

