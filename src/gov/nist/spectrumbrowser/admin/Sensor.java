package gov.nist.spectrumbrowser.admin;

import gov.nist.spectrumbrowser.common.Defines;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONBoolean;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONString;

public class Sensor {
	
	private static final int MIN_KEY_LENGTH = 3;

	private JSONObject sensorObj;

	public Sensor() {
		this.sensorObj = new JSONObject();
		sensorObj.put("SensorID", new JSONString("UNKNOWN"));
		sensorObj.put("SensorKey", new JSONString("UNKNOWN"));
		sensorObj.put("thresholds", new JSONObject());
		sensorObj.put(Defines.STREAMING, new JSONObject());
		sensorObj.put("dataRetentionDurationMonths", new JSONNumber(1));
		sensorObj.put("sensorStatus", new JSONString("NEW"));
		sensorObj.put("sensorAdminEmail", new JSONString("UNKNOWN"));
		sensorObj.put("measurementType", new JSONString("Swept-Frequency"));
		sensorObj.put(Defines.IS_STREAMING_ENABLED, JSONBoolean.getInstance(false));
	}

	public Sensor(JSONObject sensorObj) {
		this.sensorObj = sensorObj;
	}
	
	public void clear() {
		sensorObj.put("SensorID", new JSONString("UNKNOWN"));
		sensorObj.put("SensorKey", new JSONString("UNKNOWN"));
		sensorObj.put("sensorStatus", new JSONString("NEW"));
	}
	
	public JSONObject getSensorObj() {
		return sensorObj;
	}
	
	public JSONObject getMessageDates() {
		return sensorObj.get("messageDates").isObject();
	}
	
	public void addNewThreshold(String sysToDetect,JSONObject threshold){
		getThresholds().put(sysToDetect+":" + threshold.get("minFreqHz") + ":" + threshold.get("maxFreqHz"), threshold);
	}
	
	public void deleteThreshold(Threshold threshold) {
		// putting a null deletes the key.
		getThresholds().put(threshold.getId(), null);
	}

	public JSONObject getThresholds() {
		return sensorObj.get("thresholds").isObject();
	}
	
	public int getThresholdCount() {
		return sensorObj.get("thresholds").isObject().keySet().size();
	}
	
	public void setThresholds(JSONObject thresholds) {
		sensorObj.put("thresholds", thresholds);
	}
	
	public JSONObject getStreamingConfig() {
		return sensorObj.get("streaming").isObject();
	}
	
	private void setStreamingConfig(JSONObject streamingConfig) {
		sensorObj.put("streaming", streamingConfig);	
	}

	public String getSensorId() {
		return sensorObj.get("SensorID").isString().stringValue();
	}

	public String getSensorKey() {
		return sensorObj.get("SensorKey").isString().stringValue();
	}

	public boolean setSensorKey(String sensorKey) {
		if (getSensorKey().length() < MIN_KEY_LENGTH
			){
			return false;
		}
		sensorObj.put("SensorKey", new JSONString(sensorKey));
		return true;
	}

	public String getSensorAdminEmail() {
		return sensorObj.get("sensorAdminEmail").isString().stringValue();
	}

	public void setSensorAdminEmail(String sensorAdminEmail) {
		sensorObj.put("sensorAdminEmail", new JSONString(sensorAdminEmail));
	}

	public String getSensorStatus() {
		return sensorObj.get("sensorStatus").isString().stringValue();
	}

	public String getSensorLastMessageDate() {
		return sensorObj.get("lastMessageDate").isString().stringValue();
	}

	public String getSensorLastMessageType() {
		return sensorObj.get("lastMessageType").isString().stringValue();
	}

	public int getDataRetentionDurationMonths() {
		return (int) sensorObj.get("dataRetentionDurationMonths").isNumber()
				.doubleValue();
	}
	
	public String getMeasurementType() {
		
		return sensorObj.get(Defines.MEASUREMENT_TYPE).isString().stringValue();
	}


	@Override
	public String toString() {
		return sensorObj.toString();
	}

	public boolean validate() {
		if (getSensorAdminEmail().equals("UNKNOWN")
				|| getSensorKey().length() < MIN_KEY_LENGTH
				|| getSensorId().equals("UNKNOWN")
				|| getDataRetentionDurationMonths() == -1 
				|| getMeasurementType() == null 
				|| ( !getMeasurementType().equals(Defines.SWEPT_FREQUENCY) &&
						!getMeasurementType().equals(Defines.FFT_POWER)) ){
			return false;
		} else {
			return true;
		}
	}

	public void setSensorId(String sensorId) {
		sensorObj.put("SensorID", new JSONString(sensorId));
	}

	public boolean setDataRetentionDurationMonths(int value) {
		if ( value < 0) {
			return false;
		} else {
			sensorObj.put("dataRetentionDurationMonths", new JSONNumber(value));
			return true;
		}
	}

	public static Sensor createNew(Sensor sensor) {
		String sensorStr = sensor.sensorObj.toString();
		JSONObject newSensorObj = JSONParser.parseLenient(sensorStr).isObject();
		Sensor retval = new Sensor(newSensorObj);
		retval.clear();
		return retval;
	}

	public void setMeasurementType(String mtype) {
		sensorObj.put(Defines.MEASUREMENT_TYPE, new JSONString(mtype));
	}

	public boolean isStreamingEnabled() {
		return sensorObj.get(Defines.IS_STREAMING_ENABLED).isBoolean().booleanValue();
	}
	
	public void setStreamingEnabled(boolean flag) {
		if (! flag) {
			sensorObj.put(Defines.STREAMING, new JSONObject());
		}
		sensorObj.put(Defines.IS_STREAMING_ENABLED, JSONBoolean.getInstance(flag));
	}

	

}