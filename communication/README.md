# Communication database

This database defines both telemetry and telecommands between the Arduino and the base.
See the [ECom documentation](https://ecom.readthedocs.io/en/latest/database/README.html) for more info.
This communication database contains the following files and folders:

* [telemetry.csv](telemetry.csv):
  
  A list of telemetry packages and a description of them.
  Currently, this declares two telemetry packages: `HEARTBEAT` and `LOG`.

* [telemetryArguments](telemetryArguments):
  
  This folder contains the definition of the data that is sent with each telemetry type.
  The definition for each telemetry package is in a file with the name of that telemetry package.
  For this communication database, the telemetry arguments specify that a `HEARTBEAT` package only consists of a
  `time` data in milliseconds. The `LOG` package on the other hand is more interesting:
  It contains a `time` in milliseconds as well, but also a `level`, which is an enum value of an enum defined in the
  [`sharedDataTypes.json` file](sharedDataTypes.json). Additionally, the `LOG` package also contains an integer size
  and a variable length list of characters which means that the size of this package depends on its content.

* [sharedConstants.csv](sharedConstants.csv):
  
  Constant values that are used in the communication. It contains the values of the two synchronization bytes which are
  included at the start of every message, so the receiver can determine when a package starts.
  
* [sharedDataTypes.json](sharedDataTypes.json):
  
  A description of data types that are used in the communication.
  This communication database only contains two data types: `TelemetryMessageHeader` and `LogLevel`.
  The latter is used in the `LOG` telemetry,
  the former one is used to describe the general format of all telemetry packages.
  
* [units.csv](units.csv):
  
  A description of units and their base datatypes used in the communication.
  For this template, only one unit is defined; `ms` which wraps an 2 bit unsigned number
  and is used to represent and send milliseconds.
