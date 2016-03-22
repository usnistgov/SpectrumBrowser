package gov.nist.spectrumbrowser.admin;


import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

class Threshold {
	private JSONObject threshold;
	
	public Threshold() {
		this.threshold = new JSONObject();
		this.threshold.put("systemToDetect", new JSONString("UNKNOWN"));
		this.threshold.put("maxFreqHz", new JSONNumber(-1));
		this.threshold.put("minFreqHz",new JSONNumber(-1));
		this.threshold.put("thresholdDbmPerHz", new JSONNumber(-1));
		this.threshold.put("channelCount", new JSONNumber(-1));
		this.threshold.put("active", JSONBoolean.getInstance(false));
	}
	
	public Threshold(JSONObject threshold) {
		this.threshold = threshold;
	}

	public boolean validate() {
		if (getSystemToDetect().equals("UNKNOWN") || 
				getMaxFreqHz() == -1 || getMinFreqHz() == -1 || getThresholdDbmPerHz() == -1  ||
				getMinFreqHz() > getMaxFreqHz() || getChannelCount() == -1 ) {
			return false;
		} else {
			return true;
		}
	}
	
	
	
	public String getSystemToDetect() {
		if (threshold.containsKey("systemToDetect")) {
			return threshold.get("systemToDetect").isString().stringValue();
		} else {
			return "UNKNOWN";
		}
	}
	
	public String getId() {
		return getSystemToDetect() + ":" + getMinFreqHz() + ":" + getMaxFreqHz();
	}
	
	public void setSystemToDetect(String systemToDetect) {
		if ( systemToDetect == null  || systemToDetect.equals("UNKNOWN")
				|| !systemToDetect.matches("[a-zA-Z0-9_-]+") ) {
			throw new IllegalArgumentException("Attempting to set Illegal value " + systemToDetect);
		}
		threshold.put("systemToDetect", new JSONString(systemToDetect));
	}
	
	public void setMaxFreqHz(long maxFreqHz) {
		threshold.put("maxFreqHz", new JSONNumber(maxFreqHz));
	}
	
	public long getMaxFreqHz() {
		if (threshold.containsKey("maxFreqHz")) {
			return (long) threshold.get("maxFreqHz").isNumber().doubleValue();
		} else {
			return -1;
		}
	}
	public void setMinFreqHz( long minFreqHz) {
		if (minFreqHz<=0) 
			throw new IllegalArgumentException("Attempting to set Illegal value "  + minFreqHz);
		threshold.put("minFreqHz", new JSONNumber(minFreqHz));
	}
	
	public long getMinFreqHz() {
		if (threshold.containsKey("minFreqHz")) {
			return (long) threshold.get("minFreqHz").isNumber().doubleValue();
		} else {
			return -1;
		}
	}
	
	public void setThresholdDbmPerHz(double dbmPerHz) {
		if ( dbmPerHz >= 0) 
			throw new IllegalArgumentException("Attempting to set Illegal value " + dbmPerHz);
		threshold.put("thresholdDbmPerHz", new JSONNumber(dbmPerHz));
	}
	
	public double getThresholdDbmPerHz() {
		if ( threshold.containsKey("thresholdDbmPerHz")) {
				return threshold.get("thresholdDbmPerHz").isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	public JSONObject getThreshold() {
		return this.threshold;
	}
	
	public boolean isActive() {
		return (threshold.get("active").isBoolean().booleanValue());
	}

	public void setActive(boolean value) {
		 threshold.put("active",JSONBoolean.getInstance(value));		
	}

	public long getChannelCount() {
		if (threshold.get("channelCount") != null) {
			return (long) threshold.get("channelCount").isNumber().doubleValue();
		} else {
			return -1;
		}
	}
	
	public void setChannelCount(long channelCount) {
		if (channelCount <= 0 ) {
			throw new IllegalArgumentException("Attempting to set Illegal value " + channelCount);
		}
		threshold.put("channelCount", new JSONNumber(channelCount));
	}
	
}