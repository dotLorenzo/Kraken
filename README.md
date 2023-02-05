# Kraken

1) CLI program written in Go to trade cryptocurrencies using the Kraken API
2) Scripts in ```parse_logs/``` parse a log file of crypto purchases in ```logs/``` to produce stats and visual plots (See jupyter notebook) to inform future trading decisions. See example log file in ```logs/```. 

## Usage
```
export API_KEY_KRAKEN={YOUR KRAKEN API KEY}
export API_SEC_KRAKEN={YOUR KRAKEN SEC KEY}
```
```
go build .
```
Todays BTC price in GBP
```
./kraken --price
```
Buy 50GBP of BTC at the market rate
```
./kraken --buy 50
```
Buy without confirmation
```
./kraken --buy 50 --noconfirmation
```
Check Kraken balance
```
./kraken --balance 
```

### Log Parser

To run the log parser:

See ```python parse_logs/main.py --help```

