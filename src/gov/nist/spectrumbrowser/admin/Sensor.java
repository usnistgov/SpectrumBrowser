package gov.nist.spectrumbrowser.admin;

import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONNumber;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONString;

public class Sensor {

	private JSONObject sensorObj;

	public Sensor() {
		this.sensorObj = new JSONObject();
		sensorObj.put("SensorID", new JSONString("UNKNOWN"));
		sensorObj.put("SensorKey", new JSONString("UNKNOWN"));
		sensorObj.put("thresholds", new JSONObject());
		sensorObj.put("streaming", new JSONObject());
		sensorObj.put("dataRetentionDurationMonths", new JSONNumber(1));
		sensorObj.put("sensorStatus", new JSONString("NEW"));
		sensorObj.put("lastMessageDate", new JSONString("UNKNOWN"));
		sensorObj.put("lastMessageType", new JSONString("UNKNOWN"));
		sensorObj.put("sensorAdminEmail", new JSONString("UNKNOWN"));
	}

	public Sensor(JSONObject sensorObj) {
		this.sensorObj = sensorObj;
	}
	
	public JSONObject getMessageDates() {
		return sensorObj.get("messageDates").isObject();
	}
	
	public void addNewThreshold(String sysToDetect,JSONObject threshold){
		getThresholds().put(sysToDetect, threshold);
	}
	
	public void deleteThreshold(String sysToDetect) {
		// putting a null deletes the key.
		getThresholds().put(sysToDetect, null);
	}

	public JSONObject getThresholds() {
		return sensorObj.get("thresholds").isObject();
	}
	
	public JSONObject getStreamingConfig() {
		return sensorObj.get("streaming").isObject();
	}

	public String getSensorId() {
		return sensorObj.get("SensorID").isString().stringValue();
	}

	public String getSensorKey() {
		return sensorObj.get("SensorKey").isString().stringValue();
	}

	public boolean setSensorKey(String sensorKey) {
		if (AddNewSensor.passwordCheckingEnabled && !getSensorKey()
						.matches(
								"((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$")){
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


	@Override
	public String toString() {
		return sensorObj.toString();
	}

	public boolean validate() {
		if (getSensorAdminEmail().equals("UNKNOWN")
				|| (AddNewSensor.passwordCheckingEnabled && !getSensorKey()
						.matches(
								"((?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&+=])).{12,}$"))
				|| getSensorId().equals("UNKNOWN")
				|| getDataRetentionDurationMonths() == -1) {
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

}