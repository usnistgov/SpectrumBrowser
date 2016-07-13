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
		sensorObj.put(Defines.SENSOR_ID, new JSONString("UNKNOWN"));
		sensorObj.put(Defines.SENSOR_KEY, new JSONString("UNKNOWN"));
		sensorObj.put("thresholds", new JSONObject());
		sensorObj.put(Defines.STREAMING, new JSONObject());
		sensorObj.put("dataRetentionDurationMonths", new JSONNumber(1));
		sensorObj.put("sensorStatus", new JSONString("NEW"));
		sensorObj.put("sensorAdminEmail", new JSONString("UNKNOWN"));
		sensorObj.put("measurementType", new JSONString("Swept-Frequency"));
		sensorObj.put(Defines.IS_STREAMING_ENABLED, JSONBoolean.getInstance(false));
		sensorObj.put(Defines.STARTUP_PARAMS, new JSONString("NONE"));
	}

	public Sensor(JSONObject sensorObj) {
		this.sensorObj = sensorObj;
	}
	
	public void clear() {
		sensorObj.put(Defines.SENSOR_ID, new JSONString("UNKNOWN"));
		sensorObj.put(Defines.SENSOR_KEY, new JSONString("UNKNOWN"));
		sensorObj.put("sensorStatus", new JSONString("NEW"));
	}
	
	public JSONObject getSensorObj() {
		return sensorObj;
	}
	
	public JSONObject getMessageDates() {
		if (sensorObj.get("messageDates") != null) {
			return sensorObj.get("messageDates").isObject();
		} else {
			return null;
		}
	}

	public JSONObject getMessageJsons() {
		if (sensorObj.get("messageJsons") != null) {
			return sensorObj.get("messageJsons").isObject();
		} else {
			return null;
		}
	}

	public JSONObject getMessageData() {
		if (sensorObj.get("messageData") != null) {
			return sensorObj.get("messageData").isObject();
		} else {
			return null;
		}
	}
	
	public void addNewThreshold(String sysToDetect,JSONObject threshold){
		getThresholds().put(sysToDetect+":" + threshold.get("minFreqHz") + ":" + threshold.get("maxFreqHz"), threshold);
	}
	
	public void deleteThreshold(FrequencyBand threshold) {
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
	
	public boolean isStreamingConfigured() {
		return new StreamingParams(getStreamingConfig()).verify();
	}
	

	public String getSensorId() {
		return sensorObj.get(Defines.SENSOR_ID).isString().stringValue();
	}

	public String getSensorKey() {
		return sensorObj.get(Defines.SENSOR_KEY).isString().stringValue();
	}

	public boolean setSensorKey(String sensorKey) {
		if (getSensorKey().length() < MIN_KEY_LENGTH
			){
			return false;
		}
		sensorObj.put(Defines.SENSOR_KEY, new JSONString(sensorKey));
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
	
	public String getStartupParams() {
		return sensorObj.get(Defines.STARTUP_PARAMS).isString().stringValue();
	}

	public void setStartupParams(String value) {
		if (value == null || value.equals("") ) {
			sensorObj.put(Defines.STARTUP_PARAMS, new JSONString("NONE"));
		} else {
			sensorObj.put(Defines.STARTUP_PARAMS, new JSONString(value));
		}
		
	}

	public JSONObject getThreshold(String key) {
		return  getThresholds().get(key).isObject();
	}

	

}
