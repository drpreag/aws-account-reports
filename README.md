# aws-account-reports
Collection of random scripts and tools used every day

# Python venv
For running python scripts you need to use virtual environment

# Environment creation
```
python3 -m venv .venv
```

## Every day use
```
source .venv/bin/activate
pip install -r requirements.txt
```

...

run python scripts

...

```
deactivate
```

# config.txt example
config.txt is mandatory for ec2-search-org.py script only
```
[aws]
main_account=111222333444
main_account_profile=default
```
