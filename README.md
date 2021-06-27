# Kraken

CLI program written in Go to trade cryptocurrencies using the Kraken API

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
Buy 50GBP of BTC
```
./kraken --buy 50
```
Check Kraken balance
```
./kraken --balance 
```
