package gov.nist.spectrumbrowser.admin;


import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

class SweptFrequencyBand extends FrequencyBand {
	private JSONObject threshold;
	
	public SweptFrequencyBand() {
		super();
	}
	
	public SweptFrequencyBand(JSONObject threshold) {
		super(threshold);
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
	
}