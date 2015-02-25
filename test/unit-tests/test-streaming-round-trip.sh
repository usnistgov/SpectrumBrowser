echo "use the LTE data file for this test "
echo "you can specify a sensor ID - which is replaced in the signaling messages"
echo "replicate this test in several shells to create system load."
python test-streaming-round-trip.py -data $SPECTRUM_BROWSER_HOME/flask/data/gburg/LTE_UL_bc17_ts109_stream_30m.dat -sensorId ECR16W4XS -dataLength 1000
