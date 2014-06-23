#include "NIDAQmx.h"
#include "ReadDigChan_Fn.h"

// Configures, starts and stops the task.
// Recommended parameters:
//   chan           = "Dev1/port0/line0:7"
int32 Configure_ReadDigChan(const char chan[], TaskHandle *taskHandle)
{
	int32       error=0;

/*********************************************************************
*    1. Create a task.
*    2. Create a Digital Input channel. Use one channel for all lines.
*********************************************************************/
	DAQmxErrChk (DAQmxCreateTask("",taskHandle));
	DAQmxErrChk (DAQmxCreateDIChan(*taskHandle,chan,"",DAQmx_Val_ChanForAllLines));
Error:
	return error;
}

int32 Start_ReadDigChan(TaskHandle taskHandle)
{
/*********************************************************************
*    3. Call the Start function to start the task.
*********************************************************************/
	return DAQmxStartTask(taskHandle);
}

int32 Read_ReadDigChan(TaskHandle taskHandle, uInt8 data[], uInt32 sizeOfData)
{
	int32		read,bytesPerSamp;

/*********************************************************************
*    4. Read the digital data. This read function reads a single
*       sample of digital data on demand, so no timeout is necessary.
*********************************************************************/
	return DAQmxReadDigitalLines(taskHandle,1,10.0,DAQmx_Val_GroupByChannel,data,sizeOfData,&read,&bytesPerSamp,NULL);
}

int32 Stop_ReadDigChan(TaskHandle taskHandle)
{
	int32       error=0;

/*********************************************************************
*    5. Call the Clear Task function to clear the Task.
*********************************************************************/
	error = DAQmxStopTask(taskHandle);
	DAQmxClearTask(taskHandle);
	return error;
}
