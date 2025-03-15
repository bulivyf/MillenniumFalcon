# MillenniumFalcon


Based on problem listed here:
https://github.com/dataiku/millenium-falcon-challenge

pip install flask numpy networkx

flask app
```
python app.py 
```

CLI
```
give_me_the_odds [<options>] <falcon config file, json> <empire data, json>
```
usage: give_me_the_odds [-h] [-v] [--interactive] [--debug] falcon_config empire_data

Tests
```
pytest
```

BUG: empire044.json is expected to give 100% chance of success, but gives 90%.  The implemented dfs algorithm doesn't see a better route, than the results expect. This needs further investigation, but time ran out.