# Lidar-based Critter Detector

**TBD**

## Design Notes

* Requirements
  - simple standalone sensor device, remote from (heavy) processing and display
  - integration with HA (not necessarily direct)
  - high-quality GUI, capable of displaying lidar points at max generation rate
  - GUI:
    * set the device's min/max scan angles and ranges
    * capture current perimeter
      - allow averaging of perimeter over defined number of scans
    * define region certain distance in front of and behind the perimeter
    * generate notifications when points depart from the defined region
* Structure
  - driver -> lib/lidar.py -> webServer/wsLidar.py ==> lib/wcLidar.py -> webClient/webLidar.py ==> browser
  - SW components
    * device driver
      - from manufacturer
      - both C++ and python bindings available
    * lidar device library (lib/lidar.py)
      - object that encapsulates the device and provides interface that can be used locally
      - provides sequential, single-user, use of a device
      - thin layer on top of device driver interface
      - can be used for multiple different types of lidar devices
      - uses asyncio
    * device-side standalone program that presents a remote interface to the lidar device (webServer/wsLidar.py)
      - projects the functionality offered by the lidar device library to a remote/client application
        * interacts with the client library (lib/wcLidar.py)
      - uses asyncio
      - supports only a single client at a time
    * client-side library that creates a local interface to the remote lidar device (lib/wcLidar.py)
      - interacts with the device-side device server (lib/wsLidar.py)
      - uses asyncio
      - uses a queue to store streaming responses, which are removed by the client app
        * create max-sized queue and discard the oldest one when a new one arrives to a full queue
    * standalone application that offers a web-page as a GUI to the lidar device (webClient/webLidar.py)
      - uses Flask, Dash, Plotly, and Shapely libraries to create the GUI
      - uses asyncio
* Operation
  -  communications between the remote device and the processing/display client
      - uses a versioned, websocket-based, protocol consisting of JSON messages
      - protocol consists largely of synchronous interactions
        * a command from the client is acted upon by the server, which returns a response
          - responses can include return data or can indicate an error occurred
        * a streaming command is provided that continues to return responses until streaming is stopped
          - streaming is stopped by issuing a stop, disconnect, or single scan command
          - streaming responses are returned as soon as they are available from the device
      - server-side and client-side libraries use asyncio for all message send/receive operations
    * commands issued by the client
      - initialize/reset the device
      - query the state of device
      - setting/getting device parameters
      - turn laser on/off
      - get supported protocol version
      - acquire a single lidar scan
      - start/stop streaming of lidar scans
      - disconnect the client and server
    * uses a shared module (shared/shared.py) to define messages constants (using enums)
    * version all the libraries to allow runtime checking of protocol version compatibility
      - use SemVer semantics -- specifically, to allow compatibility with non-breaking changes
  - device is designed to automatically start up the server function and wait for client connections
    * device is designed to run unattended in remote locations
  - client components (i.e., library and application) are intended to be run on a (desktop) server
  - GUI is offered by the server to arbitrary devices with a browser



