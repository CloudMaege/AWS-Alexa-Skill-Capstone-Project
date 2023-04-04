# Delete any previous artifacts and rebuild the directories
rm -fr {build,pyvenv,dist}
mkdir -p {build,dist} || exit 0

# Create a virtual environment
virtualenv pyvenv
source pyvenv/bin/activate
pip3 install pip --upgrade
pip3 install -r requirements.txt --target build/

# Copy the python file and build the package
cp alexa_awshelper_skill.py build/handler.py
cd build; zip -qr ../dist/Alexa_AWSHelper_Skill.zip *
# cd build; zip -qr ../dist/Alexa_AWSHelper_Skill_Dev.zip *

# Cleanup
cd ../
rm -fr {pyvenv,build}
deactivate

