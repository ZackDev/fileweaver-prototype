---
date: 2021-12-07
---
Advance the `FileWeaver` prototype to development phase.

The FileWeaver is built on a client/server architecture. Consisting of the `FileWeaverClient` and `FileWeaverServer`. The goal is to provide a way of transfering files over the network with obscurity in mind.

* Instead of the traditional way of transferring a file byte-wise via a single network connection, the client requests a port for every unique character found in the file from the server.

Example file content and corresponding server ports:

File content: `Hello, world`

| unique character | server port |
| --- | --- |
| H | 3 |
| e | 5 |
| l | 4 |
| o | 7 |
| , | 2 |
|   | 1 |
| w | 6 |
| r | 8 |
| d | 10 |

After the server created the ports, it notifies the client that it has established the ports for the specific unique characters.

The client now uses this information to tell the server in which order the server needs to arrange the characters to form the file contents. Given the example file content above, the characters appear in the following order.

| H | e | l | o | , |   | w | r | d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 1 | 2, 3, 10 | 4, 8 | 5 | 6 | 7 | 9 | 11 |

As stated before, the client doesn't send the characters, but instead it sends the position of the specific character in the file to the port created by the server for that specific character.

| server char:port | client data |
| --- | --- |
| H:3 | 0 |
| e:5 | 1 |
| l:4 | 2, 3, 10 |
| o:7 | 4, 8 |
| ,:2 | 5 |
|  :1 | 6 |
| w:6 | 7 |
| r:8 | 9 |
| d:10 | 11 |

The server now puts the characters back together based on positional data received on the specific ports.

| char | H | e | l | l | o | , |   | w | o | r | l | d |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| position | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |

# Limitations
For now, the communication between the server and client requires `n(uchars) + 1` ports, the number of unique chars and one more for the command channel. In most realworld setups one may not find enough open ports. A future version could work with less than `n(uchars) + 1` ports by sequentially using one port for many uchars. In theory, only one port is enough, when client and server differentiate between indizes and commands sent.

# Speed
It's utterly slow, because the `uchars buckets` get worked on sequentially. Use a threading mechanism on the client side for sending indizes. On the serverside a mutex for building the uchar-array. This requires testing.

# Countermeasures
* A `Deep Packet Inspection` firewall can filter packets that don't match the expected packet patterns.
* An `Application` firewall can exclude packets based on the program they're created with.
