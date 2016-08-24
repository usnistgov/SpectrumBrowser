package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.Defines;

import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;

/**
 * Tracks the measurement params that should match what is sent
 * in the Data message of the HTTP POST.
 * @author mranga
 *
 */
public class MeasurementParams {
	JSONObject jsonObj;
	
	public MeasurementParams(JSONObject postingConfig) {
		this.jsonObj = postingConfig;
		if ( this.jsonObj == null) {
			this.jsonObj = new JSONObject();
			this.jsonObj.put(Defines.SPECTRUMS_PER_MEASUREMENT, new JSONNumber((double) -1));
			//this.jsonObj.put(Defines.SPECTROGRAM_INTERVAL_SECONDS, new JSONNumber((double) -1));
			this.jsonObj.put(Defines.TIME_PER_SPECTRUM, new JSONNumber((double) -1));
		}
		
 	}
	
	public MeasurementParams() {
		this.jsonObj = new JSONObject();
		this.jsonObj.put(Defines.SPECTRUMS_PER_MEASUREMENT, new JSONNumber((double) -1));
		this.jsonObj.put(Defines.SPECTROGRAM_INTERVAL_SECONDS, new JSONNumber((double) -1));
		this.jsonObj.put(Defines.TIME_PER_SPECTRUM, new JSONNumber((double) -1));
	}
	
	public int getSpectrumsPerMeasurement() {
		if (!jsonObj.containsKey(Defines.SPECTRUMS_PER_MEASUREMENT)) return -1;
		return (int) jsonObj.get(Defines.SPECTRUMS_PER_MEASUREMENT).isNumber().doubleValue();
	}
	
	public boolean setSpectrumsPerMeasurement(int measurementCount) {
		if ( measurementCount <= 0) return false; 
		jsonObj.put(Defines.SPECTRUMS_PER_MEASUREMENT, new JSONNumber((double)measurementCount));
		return true;
	}
	
	public boolean setTimePerSpectrum(float tm) {
		if (tm <= 0) return false;
		jsonObj.put(Defines.TIME_PER_SPECTRUM, new JSONNumber((float) tm));
		return true;
	}
	
	public float getTimePerSpectrum() {
		if(!jsonObj.containsKey(Defines.TIME_PER_SPECTRUM)) return (float) -1;
		return (float) jsonObj.get(Defines.TIME_PER_SPECTRUM).isNumber().doubleValue();
	}
	
	public boolean setSpectrogramIntervalSeconds(int size) {
		if (size <= 0 ) return false;
		jsonObj.put(Defines.SPECTROGRAM_INTERVAL_SECONDS, new JSONNumber((double) size));
		return true;
	}
	
	public int getSpectrogramIntervalSeconds() {
		if (!jsonObj.containsKey(Defines.SPECTROGRAM_INTERVAL_SECONDS)) return -1;
		return (int) jsonObj.get(Defines.SPECTROGRAM_INTERVAL_SECONDS).isNumber().doubleValue();
	}

	public boolean verify() {
		if (getSpectrumsPerMeasurement() == -1 || getTimePerSpectrum() == -1 ) {
		    return false;
		} else {
			return true;
		}
	}

}
