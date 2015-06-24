echo "You can specify a sensor ID - which is replaced in the signaling messages."
echo "Thus you can configure multiple dummy sensors."
echo "Replicate this test in several shells specifying sensor IDs to create streaming load."
python test-streaming-round-trip.py -data LTE_UL_bc17_ts1012_stream_peak1s.dat -sensorId E6R16W5XS  -dataLength 100 -nConsumers 1 &
