/*********************************************************************
*
* ANSI C Example program:
*    ReadDigChan_main.c
*
* Example Category:
*    DI
*
* Description:
*    This example demonstrates how to read values from one or more
*    digital input channels.
*
* Instructions for Running:
*    1. Select the digital lines on the DAQ device to be read.
*
* Steps:
*    1. Create a task.
*    2. Create a Digital Input channel. Use one channel for all
*       lines.
*    3. Call the Start function to start the task.
*    4. Read the digital data. This read function reads a single
*       sample of digital data on demand, so no timeout is necessary.
*    5. Call the Clear Task function to clear the Task.
*    6. Display an error if any.
*
* I/O Connections Overview:
*    Make sure your signal input terminals match the Lines I/O
*    Control. In this case wire your digital signals to the first
*    eight digital lines on your DAQ Device.
*
* Recommended Use:
*    1. Call the Read function.
*
*********************************************************************/

#include <stdio.h>
#include <conio.h>
#include "NIDAQmx.h"
#include "ReadDigChan_Fn.h"

int main(int argc, char *argv[])
{
	int32		error=0;
	TaskHandle	taskHandle=0;
	uInt8		data[100];
	char		errBuff[2048]={'\0'};
	int32		i;
	char		ch;

	DAQmxErrChk (Configure_ReadDigChan("Dev1/port0/line0:7",&taskHandle));
	DAQmxErrChk (Start_ReadDigChan(taskHandle));
	DAQmxErrChk (Read_ReadDigChan(taskHandle,data,100));

Error:
	if( DAQmxFailed(error) )
		DAQmxGetExtendedErrorInfo(errBuff,2048);
	if( taskHandle!=0 )
		Stop_ReadDigChan(taskHandle);
	if( DAQmxFailed(error) )
		printf("DAQmx Error: %s\n",errBuff);
	else
		// assuming 8 channels acquired
		for(i=0;i<8;++i)
			printf("Data acquired, channel %d: 0x%X\n",i,data[i]);
	printf("End of program, press any key to quit\n");
	while( !_kbhit() ) {}
	ch = _getch();
return 0;
}
