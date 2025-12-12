# iAnalyzer
iAnalyzer is a tool that validates the images of a given website.

## Run
```shell
$ uv venv
$ source .venv/bin/activate
$ uv sync
$ playwright install
$ uv run main.py --domain https://example.com \
    --ignore-prefix https://example.com/tags \
    --ignore-prefix https://example.com/categories
```

## Author
+ [ambersun1234](https://github.com/ambersun1234)

## License
This project is licensed under the GNU General Public License v3.0. See the [LICENSE](LICENSE) file for details.
