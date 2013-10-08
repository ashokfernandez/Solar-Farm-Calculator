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

## How to run:
In it's current state, the calculator should run on any operating system that supports python and the dependant packges.

### Install Dependancies
The packages that this project depends on are
 * [NumPy](http://www.numpy.org/)
 * [MatPlotLib](http://matplotlib.org/)
 * [PySolar](http://pysolar.org/)
 * [wxPython 2.9](http://www.wxpython.org/)

Special thanks goes out to the above projects for providing such great tools!

### OpenExchangeRates.org API Key
An API key is required from [OpenExchangeRates.org](https://openexchangerates.org/signup/free). The free API key will suffice
for this project as there is a limit to how often the software will hit the API for new data. When you have gotten an API key 
place it at the top of Assets.py to ensure the exchange rates are retreieved.

## Build the Documentation:
The code has been heavily documented, this can be compiled into a PDF using [doxygen](http://www.stack.nl/~dimitri/doxygen/) and [latex](http://www.latex-project.org/). To build the documentation install doxygen and latex then open a shell in the Docs directory and type

    doxygen
    cd latex/
    make

A documentation file 'refman.pdf' will be avaliable in the latex folder which outlines in detail the different classes in the code and how they function