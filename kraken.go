package main

import (
  "crypto/hmac"
  "crypto/sha256"
  "crypto/sha512"
  "encoding/base64"
  "io/ioutil"
  "net/url"
  "net/http"
  "fmt"
  "time"
  "strconv"
  "strings"
  "os"
  "flag"
  "bufio"
)

var BaseUrl string = "https://api.kraken.com"

func getKrakenSignature(urlPath string, values url.Values, secret []byte) string {

  sha := sha256.New()
  sha.Write([]byte(values.Get("nonce") + values.Encode()))
  shasum := sha.Sum(nil)

  mac := hmac.New(sha512.New, secret)
  mac.Write(append([]byte(urlPath), shasum...))
  macsum := mac.Sum(nil)
  return base64.StdEncoding.EncodeToString(macsum)
}

func krakenRequest(urlPath string, payload url.Values, apiKey string, apiSign string) string {
  request, _ := http.NewRequest("POST", urlPath, strings.NewReader(payload.Encode()))

  request.Header.Set("Content-Type", "application/x-www-form-urlencoded")
  request.Header.Set("API-Key", apiKey)
  request.Header.Set("API-Sign", apiSign)

  client := &http.Client{}
  response, err := client.Do(request)
  if err != nil {
    return fmt.Sprintf("The HTTP request failed with error %s\n", err)
  } else {
    data, _ := ioutil.ReadAll(response.Body)
    return string(data)
  }
}

func createNonce() string {
  currTime := time.Now().Unix()
  nonce := strconv.FormatInt(int64(currTime), 10)
  return nonce
}

// Quantity of BTC from given quantity of GBP
func getBTCQuantity(GBPAmount uint, BTCPrice float64) float64 {
  return float64(GBPAmount) / BTCPrice
}

func kraken(balance bool, buyAmount uint, AutoConfirm bool) {
  apiKey := os.Getenv("API_KEY_KRAKEN")
  apiSec := os.Getenv("API_SEC_KRAKEN")

  var uriPath string
  var payload url.Values

  if balance {
    uriPath, payload = getBalance()
    fmt.Println("Balance:")
  } else {
    BTCprice := getBTCPrice(BaseUrl)
    BTCquantity := getBTCQuantity(buyAmount, BTCprice)
    fmt.Printf("Quantity of BTC to be bought for %d GBP: %g\n", buyAmount, BTCquantity)
    if confirmationMessage(AutoConfirm) {
      uriPath, payload = addOrder(BTCquantity)
    }
  }

  b64DecodedSecret, _ := base64.StdEncoding.DecodeString(apiSec)

  signature := getKrakenSignature(uriPath, payload, b64DecodedSecret)
  response := krakenRequest((BaseUrl + uriPath), payload, apiKey, signature)
  fmt.Println(response)
}

func confirmationMessage(AutoConfirm bool) bool {
  if AutoConfirm {
    return true
  }
  scanner := bufio.NewScanner(os.Stdin)
  fmt.Printf("Type YES to confirm payment.\n")
  scanner.Scan()
  input := scanner.Text()
  if input == "YES" {
    return true
  } else {
    fmt.Printf("Invalid input.\n")
    os.Exit(1)
    return false
  }
}

func main() {
  balanceFlag := flag.Bool("balance", false, "Get Kraken balance.")
  priceFlag := flag.Bool("price", false, "Get current market price of BTC.")
  noConfirmationFlag := flag.Bool("noconfirmation", false, "Do not confirm a buy order.")
  buyFlag := flag.Uint("buy", 0, "Amount of GBP to spend on market price of BTC.")
  helpFlag := flag.Bool("help", false, "Show commands.")
  flag.Parse()

  if *helpFlag {
      flag.PrintDefaults()
      os.Exit(1)
  }

  if *priceFlag {
    BTCprice := getBTCPrice(BaseUrl)
    fmt.Printf("Todays BTC Price: %g GBP\n", BTCprice)
  }
  if *balanceFlag || *buyFlag > 0 {
    kraken(*balanceFlag, *buyFlag, *noConfirmationFlag)
  }
}
