# If the Punisher traded crypto..

![alt text](docs/punisher.png "Logo Title Text 1")

## Quickstart

**Users**

Run the ```demo.ipynb``` jupyter notebook

or

```$ python -m punisher.strategies.simple -ohlcv .data/binance_ETH_BTC_30m.csv -t 30m -m backtest -a ETH/BTC -ex binance```

**Developers**

Run ```developers.ipynb``` to see how various components interact

## Install

1. Install [Anaconda](https://www.anaconda.com/download) with Python 3.6

2. Create conda environment
```
conda env create -f environment.yaml -n punisher
source activate punisher
```
3. Add your API keys to ```dotenv_example``` and rename ```.env```.

**No API keys?**
You can still download data with the Exchange APIs, just empty the dictionary we pass in as a config in exchange.py

4. Initialize [submodules](https://chrisjean.com/git-submodules-adding-using-removing-and-updating/)
```
git submodule init
git submodule update
```

5. Install Extras (Optional)
```
conda install ipywidgets
jupyter nbextension enable --py --sys-prefix widgetsnbextension
conda install -c tim_shawver/label/dev qgrid==1.0.0b10
conda install -c conda-forge python.app
conda install pytorch torchvision -c pytorch
```

## Running Tests
```
python -m pytest tests/ (all tests)
python -m pytest -k filenamekeyword (tests matching keyword)
python -m pytest tests/utils/test_sample.py (single test file)
python -m pytest tests/utils/test_sample.py::test_answer_correct (single test method)
python -m pytest --resultlog=testlog.log tests/ (log output to file)
python -m pytest -s tests/ (print output to console)
```

## How to commit (cleanly)

1. Before coding:

```
git pull master
git checkout -b feature
```

2. After coding, when you're ready to merge
```
# Pull latest changes from repo
git checkout master
git pull

# Merge master into feature branch.
git checkout feature
git merge master
```

3. Resolve conflicts

4. Merge feature into master and squash all your commits
```
git checkout master
git merge feature --squash
git commit -m 'Detailed Commit message describing your changes'
git push
```

## Resources

### Data

* https://www.quandl.com/collections/markets/bitcoin-data
* https://market.mashape.com/bravenewcoin/digital-currency-tickers
* https://bravenewcoin.com/
* https://coinmetrics.io/data-downloads/


### Exchanges

* https://www.coinigy.com
* https://poloniex.com
* https://www.gdax.com/
* https://gemini.com/
* https://www.binance.com/
* https://www.kraken.com/

### Research

* https://arxiv.org/archive/q-fin

### Tutorials

* [Buy/Sell/Short on Poloneix](https://www.youtube.com/watch?v=YwmoHfZ-qm8)

### Blogs/News

* TODO

### Tools / Charts

* https://zeroblock.com/
* https://www.tradingview.com/

### Repos

* https://github.com/Crypto-AI/Gemini
* https://github.com/quantopian/qgrid

### Known Issues

* [TODO](TODO.md)
