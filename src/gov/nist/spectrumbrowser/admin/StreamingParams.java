package gov.nist.spectrumbrowser.admin;

import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

public class StreamingParams {
	
	private JSONObject jsonObject;
	private JSONObject savedValues;
	private static final String STREAMING_SAMPLING_INTERVAL_SECONDS = "streamingSamplingIntervalSeconds";
	private static final String STREAMING_SECONDS_PER_FRAME = "streamingSecondsPerFrame";
	private static final String STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS = "streamingCaptureSampleSizeSeconds";
	private static final String STREAMING_FILTER = "streamingFilter";

	public StreamingParams(JSONObject jsonObject) {
		this.jsonObject = jsonObject;
		this.savedValues = new JSONObject();
		for (String key : jsonObject.keySet()) {
			savedValues.put(key, jsonObject.get(key));
		}
	}
	
	public boolean setStreamingCaptureSamplingIntervalSeconds(int interval) {
		if (interval <= 0) return false;
		jsonObject.put(STREAMING_SAMPLING_INTERVAL_SECONDS, new JSONNumber(interval));
		return true;
	}
	
	public int getStreamingCaptureSamplingIntervalSeconds() {
		if (!jsonObject.containsKey(STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS)) return -1;
		return (int) jsonObject.get(STREAMING_SAMPLING_INTERVAL_SECONDS).isNumber().doubleValue();
	}
	
	public boolean setStreamingSecondsPerFrame(float secondsPerFrame) {
		if (secondsPerFrame <= 0) return false;
		jsonObject.put(STREAMING_SECONDS_PER_FRAME, new JSONNumber(secondsPerFrame));
		return true;
	}
	public float getStreamingSecondsPerFrame() {
		if (!jsonObject.containsKey(STREAMING_SECONDS_PER_FRAME)) return -1;
		return (float) jsonObject.get(STREAMING_SECONDS_PER_FRAME).isNumber().doubleValue();
	}
	public boolean setStreamingCaptureSampleSizeSeconds(int sampleSizeSeconds) {
		if ( sampleSizeSeconds <= 0) return false;
		jsonObject.put(STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS, new JSONNumber(sampleSizeSeconds));
		return true;
	}
	public int getStreamingCaptureSampleSizeSeconds() {
		if (!jsonObject.containsKey(STREAMING_SAMPLING_INTERVAL_SECONDS)) return -1;
		return (int) jsonObject.get(STREAMING_CAPTURE_SAMPLE_SIZE_SECONDS).isNumber().doubleValue();
	}
	
	public boolean setStreamingFilter(String streamingFilter) {
		if (!streamingFilter.equals("MAX_HOLD") && !streamingFilter.equals("MEAN")) {
			return false;
		}
		jsonObject.put(STREAMING_FILTER,new JSONString(streamingFilter));
		return true;
	}
	
	public String getStreamingFilter() {
		if (!jsonObject.containsKey(STREAMING_FILTER)) return "UNKNOWN";
		return jsonObject.get(STREAMING_FILTER).isString().stringValue();
	}

	public boolean verify() {
		if (getStreamingFilter().equals("UNKNOWN") || getStreamingCaptureSampleSizeSeconds() == -1 ||
				getStreamingCaptureSamplingIntervalSeconds() == -1 || getStreamingSecondsPerFrame() == -1 ) {
			return false;
		} else {
			return true;
		}
	}
	
	public void restore() {
		for (String key: jsonObject.keySet()) {
			jsonObject.put(key, null);
		}
		for (String key: savedValues.keySet()) {
			jsonObject.put(key, savedValues.get(key));
		}
	}

	public void clear() {
		for (String key: jsonObject.keySet()) {
			jsonObject.put(key, null);
		}
	}

}
