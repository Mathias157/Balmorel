# Check that pybalmorel is the correct branch
pybalmorel_branch=$(cd ~/Repos/pybalmorel && git status | grep branch | awk '{print $3}' | head -1)
if [[ $pybalmorel_branch != "weekly_transmission_outage_availabilities" ]]; then
  echo "pybalmorel branch is not weekly_transmission_outage_availabilities, but $pybalmorel_branch" >&2
  exit 1
fi
