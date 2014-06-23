from libnidaqmx import System
from libnidaqmx import Device
import numpy as np

from libnidaqmx import AnalogOutputTask
from libnidaqmx import DigitalOutputTask

system = System()

print 'libnidaqmx version:', system.version
print 'NI-DAQ devices:', system.devices
dev1 = system.devices[0]
print 'Product Type:', dev1.get_product_type()
print 'Product Number:',dev1.get_product_number()
print 'Product Serial:', dev1.get_serial_number()
print 'Bus Type:', dev1.get_bus()


#ddata = np.zeros(nsamples, dtype=np.uint8)
#ddata[0:nsamples:5]=1

task = DigitalOutputTask()

# have to connect channel port2/line7 P2.7
# have to be 'for_all_lines' because the port is mentioned

task.create_channel('Dev1/Port2/Line7');    
task.start();
data = [1];
task.write(data);
task.stop();
task.clear();


#task.configure_timing_sample_clock(rate = 1, active_edge='rising', sample_mode = 'continuous', samples_per_channel = 100)

#task.configure_timing_sample_clock(source=r'ao/SampleClock',rate=1000,sample_mode='finite',samples_per_channel=1000)
#task.write(ddata, auto_start=False)
#task.start()

#task.stop()


