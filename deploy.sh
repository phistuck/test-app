echo Getting the latest version.
#projectversion=`gcloud app versions list --hide-no-traffic --format='value(version.id)'`
projectversion="0-5"

tmp_base=~/tmp
tmppath=${tmp_base}/${DEVSHELL_PROJECT_ID}-original-code
versionedtmppath=${tmppath}/${projectversion}

# https://stackoverflow.com/questions/1885525/how-do-i-prompt-a-user-for-confirmation-in-bash-script
read -p "Should I delete ${versionedtmppath} and re-download the sources into it? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]; then
 read
 rm -rf ${versionedtmppath}
 mkdir ${tmp_base}
 mkdir ${tmppath}
 mkdir ${versionedtmppath}
 
 command_to_run="appcfg.py download_app -A $DEVSHELL_PROJECT_ID -V ${projectversion} ${versionedtmppath}/"
 echo ${command_to_run}
 ${command_to_run}
else
 read
fi
echo ".gitignore has -"
cat .gitignore
echo
echo "Make sure I did not forget anything!"
echo
echo
command_to_run="cp -i ${versionedtmppath}/configuration.py ."
echo ${command_to_run}
${command_to_run}
command_to_run="cp -i ${versionedtmppath}/myrsacert.pem ."
echo ${command_to_run}
${command_to_run}
blog="./static/blog"
others="${blog}/others"
echo "Looking for ${others}"
if [[ ! -d ${others} ]]; then
 echo "Did not find it."
 command_to_run="cp -i -r ${versionedtmppath}/${blog}/* ${blog}"
 echo ${command_to_run}
 ${command_to_run}
else
 echo "Found it, not copying."
fi
echo Done.