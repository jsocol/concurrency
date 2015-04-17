package main

import (
	"fmt"
	"github.com/bradfitz/gomemcache/memcache"
	"io/ioutil"
	"log"
	"net/http"
	"time"
)

const UPSTREAM = "http://127.0.0.1:6000/"
const CACHE = "127.0.0.1:11212"

func ProxyHandler(w http.ResponseWriter, req *http.Request) {
	res, err := http.Get(UPSTREAM)
	if err != nil {
		log.Printf("Error from upstream: %s", err)
		http.Error(w, "", 503)
		return
	}
	resBody, err := ioutil.ReadAll(res.Body)
	if err != nil {
		log.Printf("Error reading response: %s", err)
		http.Error(w, "", 503)
		return
	}
	fmt.Fprintf(w, "%s", resBody)
}

var mc = memcache.New(CACHE)

func CacheHandler(w http.ResponseWriter, req *http.Request) {
	foo, err := mc.Get("foo")
	if err != nil {
		log.Printf("Could not read from cache: %s", err)
		http.Error(w, "", 503)
		return
	}
	fmt.Fprintf(w, "%s", foo.Value)
}

func main() {
	mc.Timeout = 5.0 * time.Second
	http.HandleFunc("/sync", ProxyHandler)
	http.HandleFunc("/cache", CacheHandler)
	log.Printf("Listening on :5300")
	log.Fatal(http.ListenAndServe(":5300", nil))
}
