/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.admin;


import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

abstract class FrequencyBand {
	protected JSONObject threshold;
	
	public FrequencyBand(Sensor sensor) {
		this.threshold = new JSONObject();
		this.threshold.put("systemToDetect", new JSONString("UNKNOWN"));
		this.threshold.put("maxFreqHz", new JSONNumber(-1));
		this.threshold.put("minFreqHz",new JSONNumber(-1));
		this.threshold.put("thresholdDbmPerHz", new JSONNumber(-1));
		this.threshold.put("channelCount", new JSONNumber(-1));
		if (sensor.isStreamingEnabled())
			this.threshold.put("active", JSONBoolean.getInstance(false));
		else 
			this.threshold.put("active", JSONBoolean.getInstance(true));

	}
	
	public FrequencyBand(JSONObject threshold) {
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
				|| !systemToDetect.matches("[a-zA-Z0-9_-]+$") ) {
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
