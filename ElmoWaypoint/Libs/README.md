# Bundled libraries

The broker/launcher libraries below were copied unmodified from the existing
ElmoLFM bundle. Original source headers are retained.

- LibStub, revision 2; public domain, credits retained in the source header.
- CallbackHandler-1.0, revision 8.
- LibDataBroker-1.1, revision 4.
- LibDBIcon-1.0, revision 56.
- HereBeDragons-2.0, revision 35, and HereBeDragons-Pins-2.0, revision 17:
  Nevcairiel's independent mapping libraries, release 2.18, declared BSD by
  upstream. Copied unmodified from the installed TomTom library bundle. See
  [upstream metadata](HereBeDragons/UPSTREAM.md).

They load in the order listed above, before ElmoWaypoint's own files. LibStub reuses an existing library of the same or a newer revision when another addon has already loaded it.
