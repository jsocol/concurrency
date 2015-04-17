package main

import (
	"io"
	"log"
	"net"
	"time"
)

func HandleReq(conn net.Conn) {
	defer conn.Close()
	buf := make([]byte, 2048)
	for {
		_, err := conn.Read(buf)
		if err != nil {
			if err == io.EOF {
				break
			}
			log.Printf("Error reading from conn: %s", err)
		}
		time.Sleep(2.0 * time.Second)
		conn.Write([]byte("VALUE foo 0 3\r\nbar\r\nEND\r\n"))
	}
}

func main() {
	l, err := net.Listen("tcp", "127.0.0.1:11212")
	if err != nil {
		log.Fatalf("Could not listen: %s", err)
	}
	defer l.Close()
	log.Printf("Listening on 127.0.0.1:11212")
	for {
		conn, err := l.Accept()
		if err != nil {
			log.Printf("Error accepting: %s", err)
		}
		go HandleReq(conn)
	}
}
