"""Outbound (driven) ports: what the application drives and needs from outside.

The application is in charge of every conversation through these ports: it opens a
source, pulls its events, decides when to stop and closes it, and it decides what
is written where. `providers` holds the ports of the data providers, `outputs` the
ports of what the application writes and reads back, `system` clock and environment.
Every port is an ABC so that each adapter declares the abstraction it implements.
"""
