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
package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.ui.Label;

public class BandInfo {

	private JSONObject jsonObj;
	private FrequencyRange freqRange;
	private long selectedMinFreq;
	private long selectedMaxFreq;
	private SpectrumBrowser spectrumBrowser;
	private String sensorId;
	private SensorInfo sensorInfo;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	private String formatToPrecision(int precision, double value) {
		String format = "00.";
		for (int i = 0; i < precision; i++) {
			format += "0";
		}
		return NumberFormat.getFormat(format).format(value);
	}

	private float round(double val) {
		return (float) ((int) ((val + .05) * 10) / 10.0);
	}

	private long getLong(String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return (long) jsonObj.get(keyName).isNumber().doubleValue();
		} else {
			return -1;
		}
	}
	
	private boolean getBoolean(String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return jsonObj.get(keyName).isBoolean().booleanValue();
		} else {
			return false;
		}
	}

	private String getString(String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return jsonObj.get(keyName).isString().stringValue();
		} else {
			return "";
		}
	}

	private double getDouble(String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return jsonObj.get(keyName).isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	public BandInfo(SensorInfo sensorInfo, JSONObject jsonObj, String sensorId,
			SpectrumBrowser spectrumBrowser) {
		this.sensorInfo = sensorInfo;
		this.jsonObj = jsonObj;
		this.sensorId = sensorId;
		this.freqRange = new FrequencyRange(this.getSysToDetect(),
				this.getMinFreq(), this.getMaxFreq());
		this.selectedMinFreq = this.getMinFreq();
		this.selectedMaxFreq = this.getMaxFreq();
		this.spectrumBrowser = spectrumBrowser;
	}
	
	public boolean isActive() {
		return getBoolean(Defines.ACTIVE);
	}

	public long getTstartDayBoundary() {
		return getLong(Defines.TSTART_DAY_BOUNDARY);
	}

	public String getSysToDetect() {
		return getString(Defines.SYSTEM_TO_DETECT);
	}

	public long getTEndReadings() {
		return (long) jsonObj.get(Defines.T_END_READINGS).isNumber()
				.doubleValue();
	}

	public String getTStartLocalTimeFormattedTimeStamp() {
		return getString(Defines.TSTART_LOCAL_FORMATTED_TIMESTAMP);
	}

	public String getTEndLocalTimeFormattedTimeStamp() {
		return getString(Defines.TEND_LOCAL_FORMATTED_TIMESTAMP);
	}

	public long getTstartLocalTime() {
		return getLong(Defines.TSTART_LOCAL_TIME);
	}

	public long getMaxFreq() {
		return getLong(Defines.MAX_FREQ);
	}

	public float getMaxOccupancy() {
		return round(getDouble(Defines.MAX_OCCUPANCY));
	}

	public long getTendReadingsLocalTime() {
		return getLong(Defines.T_END_READINGS_LOCAL_TIME);
	}

	public long getMinFreq() {
		return getLong(Defines.MIN_FREQ);
	}

	public long getTendDayBoundary() {
		return getLong(Defines.T_END_DAY_BOUNDARY);
	}

	public float getMinOccupancy() {
		return round(getDouble(Defines.MIN_OCCUPANCY));
	}

	public long getTstartReadings() {
		return getLong(Defines.T_START_READINGS);
	}

	public float getMeanOccupancy() {
		return round(getDouble(Defines.MEAN_OCCUPANCY));
	}

	public long getCount() {
		return getLong(Defines.COUNT);
	}

	public FrequencyRange getFreqRange() {
		return this.freqRange;
	}

	public String getDescription() {

		if (sensorInfo.getMeasurementType().equals(Defines.FFT_POWER)) {
			return  "<div align=\"left\", height=\"300px\">"
					+ "System To Detect = "
					+ this.freqRange.sys2detect
					+ "<br/>fStart = "
					+ this.getMinFreq() / 1E6
					+ "MHz; fStop = "
					+ this.getMaxFreq() / 1E6
					+ "MHz"
					+ "<br/>Data Start Time = "
					+ this.getTStartLocalTimeFormattedTimeStamp()
					+ "<br/>Data End Time = "
					+ this.getTEndLocalTimeFormattedTimeStamp()
					+ "<br/>Occupancy: Max = "
					+ this.formatToPrecision(2, getMaxOccupancy() * 100)
					+ "%"
					+ "; Min= "
					+ this.formatToPrecision(2, getMinOccupancy() * 100)
					+ "%"
					+ "; Mean = "
					+ this.formatToPrecision(2, getMeanOccupancy() * 100)
					+ "%"
					+ "<br/>Aquisition Count = " + getCount() 
					+ "<br/>Enabled? " + isActive() + "<br/>";
		} else {
			return  "<div align=\"left\", height=\"300px\">"
					+ "System To Detect = " + this.freqRange.sys2detect
					+ "<br/>Data Start Time = "
					+ this.getTStartLocalTimeFormattedTimeStamp() 
					+ "<br/>Data End Time = "
					+ this.getTEndLocalTimeFormattedTimeStamp()
					+ "<br/>Occupancy: Max = "
					+ this.formatToPrecision(2, getMaxOccupancy() * 100) + "%"
					+ "; Min= "
					+ this.formatToPrecision(2, getMinOccupancy() * 100) + "%"
					+ "; Mean = "
					+ this.formatToPrecision(2, getMeanOccupancy() * 100) + "%"
					+ "<br/>Aquisition Count = " + getCount() 
					+ "<br/>Enabled? " + isActive() + "<br/>";
		}
	}

	public long getSelectedMinFreq() {
		return selectedMinFreq;
	}

	public boolean setSelectedMinFreq(long selectedMinFreq) {
		if (selectedMinFreq >= this.getMinFreq()
				&& selectedMinFreq <  this.getMaxFreq()) {
			this.selectedMinFreq = selectedMinFreq;
			return true;
		} else {
			return false;
		}
	}

	public long getSelectedMaxFreq() {
		return selectedMaxFreq;
	}

	public String getSystemToDetect() {
		return this.freqRange.sys2detect;
	}

	public boolean setSelectedMaxFreq(long selectedMaxFreq) {
		if (selectedMaxFreq <= this.getMaxFreq()
				&& selectedMaxFreq > this.getMinFreq()) {
			this.selectedMaxFreq = selectedMaxFreq;
			return true;
		} else {
			return false;
		}
	}

	public void updateAcquistionCount(
			final SensorInfoDisplay sensorInfoDisplay, long startTime,
			int dayCount) {
		spectrumBrowser.getSpectrumBrowserService().getAcquisitionCount(
				sensorId, getSystemToDetect(), getMinFreq(), getMaxFreq(),
				startTime, dayCount, new SpectrumBrowserCallback<String>() {

					@Override
					public void onSuccess(String result) {
						logger.finer("updateAcquistionCount");
						JSONObject jsonObject = JSONParser.parseLenient(result)
								.isObject();
						if (jsonObject.get(Defines.STATUS).isString()
								.stringValue().equals(Defines.OK)) {
							long count = (long) jsonObject.get(Defines.COUNT)
									.isNumber().doubleValue();
							sensorInfoDisplay.updateReadingsCountLabel(count);
							if (count != 0) {
								long tStart = (long) jsonObject
										.get(Defines.TSTART_DAY_BOUNDARY)
										.isNumber().doubleValue();
								long tEnd = (long) jsonObject
										.get(Defines.T_END_DAY_BOUNDARY)
										.isNumber().doubleValue();
								long dayCount = (tEnd - tStart)
										/ Defines.SECONDS_PER_DAY + 1;
								
								long tEndReadingsDayBoundary = (long) jsonObject
										.get(Defines.T_END_READINGS_DAY_BOUNDARY)
										.isNumber().doubleValue();
								
								long maxDayCount = (tEndReadingsDayBoundary - tStart) / Defines.SECONDS_PER_DAY + 1;
								
								sensorInfoDisplay.updateUserDayCountMenuBar((int) dayCount, (int)maxDayCount);
							} else {
								sensorInfoDisplay.updateUserDayCountMenuBar(0,0);
							}
						} else {
							logger.log(Level.SEVERE,
									"Unexpected Error in processing request");
						}
					}

					@Override
					public void onFailure(Throwable throwable) {
						logger.log(Level.SEVERE,
								"Failure communicating with server ", throwable);
						spectrumBrowser
								.displayError("Error Communicating with Server");
					}
				});
	}

}
