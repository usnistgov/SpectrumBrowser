echo "Use the LTE data file for this test "
echo "You can specify a sensor ID - which is replaced in the signaling messages."
echo "Thus you can configure multiple dummy sensors."
echo "Replicate this test in several shells specifying sensor IDs to create streaming load."
python test-streaming-round-trip.py -data $SPECTRUM_BROWSER_HOME/flask/data/gburg/LTE_UL_bc17_ts109_stream_30m.dat -sensorId ECR16W4XS -dataLength 1000 -nConsumers 10 &
