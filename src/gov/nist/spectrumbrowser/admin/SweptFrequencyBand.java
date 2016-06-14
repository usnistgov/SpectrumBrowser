package gov.nist.spectrumbrowser.admin;


import com.google.gwt.json.client.JSONObject;

class SweptFrequencyBand extends FrequencyBand {
	
	public SweptFrequencyBand(Sensor sensor) {
		super(sensor);
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