= Python linting using black and flake8

```sh
#!/bin/sh -l

black --check --quiet .
python3 -m flake8 --ignore=E501 .
```
