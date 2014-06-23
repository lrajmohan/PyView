#define DAQmxErrChk(functionCall) { if( DAQmxFailed(error=(functionCall)) ) { goto Error; } }

int32 Configure_ReadDigChan(const char chan[], TaskHandle *taskHandle);
int32 Start_ReadDigChan(TaskHandle taskHandle);
int32 Read_ReadDigChan(TaskHandle taskHandle, uInt8 data[], uInt32 sizeOfData);
int32 Stop_ReadDigChan(TaskHandle taskHandle);
