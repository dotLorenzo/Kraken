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
)


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

func getBalance() (uriPath string, payload url.Values) {
  uriPath = "/0/private/Balance"
  payload = url.Values{}
  payload.Add("nonce", createNonce())
  return
}

func main() {
  BaseUrl := "https://api.kraken.com"
  apiKey := os.Getenv("API_KEY_KRAKEN")
  apiSec := os.Getenv("API_SEC_KRAKEN")

  uriPath, payload := getBalance()
  b64DecodedSecret, _ := base64.StdEncoding.DecodeString(apiSec)

  signature := getKrakenSignature(uriPath, payload, b64DecodedSecret)
  response := krakenRequest((BaseUrl + uriPath), payload, apiKey, signature)
  fmt.Println(response)
}
