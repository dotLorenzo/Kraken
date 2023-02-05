package main

import (
  "encoding/json"
  "io/ioutil"
  "fmt"
  "net/url"
  "net/http"
  "strconv"
)

func getBalance() (uriPath string, payload url.Values) {
  uriPath = "/0/private/Balance"
  payload = url.Values{}
  payload.Add("nonce", createNonce())
  return
}

// Create a market order for the specified amount in GBP
func addOrder(quantity float64) (uriPath string, payload url.Values) {
  uriPath = "/0/private/AddOrder"
  strQuantity := strconv.FormatFloat(quantity, 'f', -1, 64)
  payload = url.Values{}
  payload.Add("pair","XBTGBP")
  payload.Add("type","buy")
  payload.Add("ordertype","market")
  payload.Add("volume", strQuantity)
  payload.Add("nonce", createNonce())
  return
}

// Get todays bitcoin price in GBP
func getBTCPrice(BaseUrl string) float64 {
  uriPath := "/0/public/Ticker?pair=XBTGBP"
  response, err := http.Get(BaseUrl + uriPath)

  if err != nil {
    panic(fmt.Sprintf("The HTTP request failed with error %s\n", err))
  } else {
    data, _ := ioutil.ReadAll(response.Body)
    var jsonData JsonResponseData
    json.Unmarshal(data, &jsonData)
    todaysPrice := jsonData.Result.XXBTZGBP.P[0]
    PriceFloat, _ := strconv.ParseFloat(todaysPrice, 64)
    return PriceFloat
  }
}

type JsonResponseData struct {
  Error  []interface{} `json:"error"`
  Result struct {
    XXBTZGBP struct {
      A []string `json:"a"`
      B []string `json:"b"`
      C []string `json:"c"`
      V []string `json:"v"`
      P []string `json:"p"`
      T []int    `json:"t"`
      L []string `json:"l"`
      H []string `json:"h"`
      O string   `json:"o"`
    } `json:"XXBTZGBP"`
  } `json:"result"`
}
