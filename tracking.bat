@echo off
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Running People Counter...
python people_counter.py --prototxt models/MobileNetSSD_deploy.prototxt --model models/MobileNetSSD_deploy.caffemodel --input utils/data/test.mov --output output.mp4

pause

