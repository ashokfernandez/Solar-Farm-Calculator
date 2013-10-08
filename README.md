# Solar Farm Calculator
### A software tool to model a generic solar photovoltaic farm.


## Author
[Ashok Fernandez](https://github.com/ashokfernandez/),
[Jarrad Raumati](https://github.com/jarradraumati/),
Darren O'Neill


## Description: 
Models the technical and financial details of a photovoltaic farm. The user
specifies the parameters of the site which then calculates the expected output
energy at the grid entry point (GEP).

A site and grid entry point can be selected using GPS coordinates which assist
in calculating the insolation from the sun using [PySolar](https://github.com/pingswept/pysolar).
System components such as panels, DC and AC cables, inverter, transformer and
transmission lines can be specified using the graphical user interface, which
will then run the model simulation.

The outputs from the simulation can be listed and plotted for the user to
determine if the parameters produce a viable solar farm.
