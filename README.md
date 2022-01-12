# ParticleCounter

This code is used to plot the data from a Panasonic Particle sensor.  Part number SN-GCJA5.

It listens to the serial data that is emitted from a 3.3V TX pin on the device.
Every second it emits a 32 Byte block of data starting with a header byte of 0x02 and finishing with a terminating 0x03

By syncing up with the 0x03, 0x02 sequence it is possible to collect the other data and then use it to reconstruct the data.

This project uses PyQT5 and pyqtgraph to create a UI that can display the particle count for the last hour.
You will need to make modifications to figure out which serial port you are listening to the device on and adapt the code accordingly.

