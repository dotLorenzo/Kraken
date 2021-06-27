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
