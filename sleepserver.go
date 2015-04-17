package main

import (
	"fmt"
	"log"
	"net/http"
	"time"
)

var requests = 0

func Sleeper(w http.ResponseWriter, req *http.Request) {
	requests++
	i := requests
	log.Printf("req %d started", i)
	time.Sleep(2.0 * time.Second)
	fmt.Fprintf(w, "ok\n")
	log.Printf("req %d finished", i)
}

func main() {
	http.HandleFunc("/", Sleeper)
	log.Fatal(http.ListenAndServe("127.0.0.1:6000", nil))
}
