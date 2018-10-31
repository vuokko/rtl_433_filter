Reason for existence
--------------------

This is my second python program.

Writing this software was started for dropping key codes from MQTT
messages. However some features were interesting to add and this
software bloated badly.

The current way of my usage is multiple mkfifo(1) interfaces as log
interfaces which read side puts in different places of the MQTT tree

This program can drop, add and log JSON objects.

Filtering
---------

Filtering has following priorities:
1. Inserted items can't be removed.
2. Passed items are only original items.
3. Dropping items removes only defined items.


Config file has single JSON object
----------------------------------

Some error detection is done with the config file.

Top level targets are:
"log_path", string.
Base dir for log files

"filter", Array of objects
This array has all the filtering and writing objects

"beacon", object.
Object to configure beacon message

"interval_seconds" string
defines how often beacon packet is sent in seconds. 0 to disable

Filtering object keys:

"match", array of objects or strings.
When object is defined, value and key must match. When string is used, only such key must be present in incoming data object.

"drop" array of strings. Fields to be removed from incoming data packet. Rest of fields are printed. Inserted items aren't removed.
"pass" array of strings. Print only defined fields and inserted fields

"insert" object to be added to the output.

OUTPUT HANDLING

"file" string.
Output is sent to given file

"report" boolean.
Output is sent to stderr when true

"print" boolean.
Output to stdout. If print is false, output isn't sent to stdout
ever. If print is true, output is sent to stdout always

"filter_time" boolean.
If true, "filter_time":"2018-10-31T17:54:37+02:00" object with current
time is added to output

Example but non-working config
------------------------------

1) Send to stderr messages which have temperature in -15 and have a id
   field. Remove fields "a" and "b"

2) Send to /some/path/for/logs/log.json file fields "c", "d" and add
   "filter_time" field if "id" is 10

3) Send to stdout messages which "id" is 20, add "message" and
   "weather" field with their value. Always print to stdout

Possible messages:
filter 1) is active
filter 2) is active
filter 3) is active
filters 1) and 2) are active
filters 1) and 3) are active

beacon is sent to stdout every minute.

{
    "log_path" : "/some/path/for/logs/"
    "filter":
    [
        {
            "match" : ["id", {"temperature" : -15}],
            "drop" : ["a", "b"],
            "report" : true
        },
        {
            "match" : [{"id" : 10}],
            "pass" : ["c", "d"],
            "filter_time" : true,
            "file": "log.json"
        },
        {
            "match" : [{"id" : 20}],
            "insert" : {"message" : "Hello!", "weather" : "bad"},
            "print" : true
        }   
    ],
    "beacon" :
    {
        "interval_seconds" : 60
    }
}

License
-------

MIT
