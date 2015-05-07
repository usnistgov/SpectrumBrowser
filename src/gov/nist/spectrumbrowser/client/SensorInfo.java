package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.HashSet;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import java.util.HashMap;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.HTML;

public class SensorInfo {

	private static Logger logger = Logger.getLogger("SpectrumBrowser");
	private JSONObject locationMessage;
	private HashMap<String, BandInfo> bandInfo = new HashMap<String, BandInfo>();
	private float maxOccupancy;
	private float minOccupancy;
	private long acquistionCount;
	private SpectrumBrowser spectrumBrowser;
	private String sensorId;
	private double lat;
	private double lng;
	private double alt;
	private long tEndReadings;
	private long tStartDayBoundary;
	private String measurementType;
	private long tStartReadings;
	private SensorInfoDisplay sensorInfo;
	private String tStartLocalFormattedTimeStamp;
	private String tEndLocalFormattedTimeStamp;
	private JSONObject systemMessageJsonObject;
	private HashSet<FrequencyRange> frequencyRanges = new HashSet<FrequencyRange>();
	private BandInfo selectedBand;

	public String formatToPrecision(int precision, double value) {
		String format = "00.";
		for (int i = 0; i < precision; i++) {
			format += "0";
		}
		return NumberFormat.getFormat(format).format(value);
	}

	private long getLong(JSONObject jsonObj, String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return (long) jsonObj.get(keyName).isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	private float round(double val) {
		return (float) ((int) ((val + .05) * 10) / 10.0);
	}

	private String getString(JSONObject jsonObj, String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return jsonObj.get(keyName).isString().stringValue();
		} else {
			return "";
		}
	}

	private double getDouble(JSONObject jsonObj, String keyName) {
		if (jsonObj.containsKey(keyName)) {
			return jsonObj.get(keyName).isNumber().doubleValue();
		} else {
			return -1;
		}
	}

	public SensorInfo(JSONObject systemMessageObject, JSONObject locationMessage,
			SpectrumBrowser spectrumBrowser, SensorInfoDisplay sensorInfo) {
		this.systemMessageJsonObject = systemMessageObject;
		this.locationMessage = locationMessage;
		this.spectrumBrowser = spectrumBrowser;
		this.sensorId = getString(locationMessage, Defines.SENSOR_ID);
		this.lat = getDouble(locationMessage, Defines.LAT);
		this.lng = getDouble(locationMessage, Defines.LON);
		this.alt = getDouble(locationMessage, Defines.ALT);
		this.sensorInfo = sensorInfo;
		logger.finer("SensorInfo.SensorInfo()");
	}

	public void updateDataSummary(long startTime, int dayCount, long minFreq,
			long maxFreq) {
		
		spectrumBrowser.getSpectrumBrowserService().getDataSummary(sensorId,
				lat, lng, alt, startTime, dayCount, minFreq, maxFreq,
				new SpectrumBrowserCallback<String>() {

					@Override
					public void onSuccess(String text) {
						try {
							logger.fine(text);
							JSONObject jsonObj = (JSONObject) JSONParser
									.parseLenient(text);
							String status = jsonObj.get(Defines.STATUS)
									.isString().stringValue();
							if (status.equals("NOK")) {
								Window.alert(jsonObj.get(Defines.ERROR_MESSAGE)
										.isString().stringValue());
								return;
							}
							acquistionCount = (long) jsonObj.get(Defines.COUNT)
									.isNumber().doubleValue();
							if (acquistionCount == 0) {
								Window.alert("No Data");
								return;
							}

							measurementType = jsonObj
									.get(Defines.MEASUREMENT_TYPE).isString()
									.stringValue();
							logger.finer(measurementType);

							tStartReadings = (long) jsonObj
									.get(Defines.T_START_READINGS).isNumber()
									.doubleValue();

							tEndReadings = (long) jsonObj
									.get(Defines.T_END_READINGS).isNumber()
									.doubleValue();

							maxOccupancy = round(jsonObj
									.get(Defines.MAX_OCCUPANCY).isNumber()
									.doubleValue());
							minOccupancy = round(jsonObj
									.get(Defines.MIN_OCCUPANCY).isNumber()
									.doubleValue());
							

							tStartDayBoundary = (long) jsonObj
									.get(Defines.TSTART_DAY_BOUNDARY)
									.isNumber().doubleValue();

							sensorInfo.setSelectedStartTime(tStartDayBoundary);
							sensorInfo.setDayBoundaryDelta(tStartDayBoundary
									- sensorInfo
											.getSelectedDayBoundary((long) jsonObj
													.get(Defines.TSTART_DAY_BOUNDARY)
													.isNumber().doubleValue()));

							tStartLocalFormattedTimeStamp = (String) jsonObj
									.get(Defines.TSTART_LOCAL_FORMATTED_TIMESTAMP)
									.isString().stringValue();

							tEndLocalFormattedTimeStamp = jsonObj
									.get(Defines.TEND_LOCAL_FORMATTED_TIMESTAMP)
									.isString().stringValue();
							JSONArray bands = jsonObj.get(
									Defines.BAND_STATISTICS).isArray();
							for (int i = 0; i < bands.size(); i++) {
								BandInfo bi = new BandInfo(bands.get(i)
										.isObject(),getSensorId(),spectrumBrowser);
								String key = bi.getFreqRange().toString();
								bandInfo.put(key, bi);
								frequencyRanges.add(bi.getFreqRange());
								if (selectedBand == null) {
									selectedBand = bi;
								}
							}
							
							sensorInfo.buildSummary();
						} catch (Throwable ex) {
							logger.log(Level.SEVERE,
									"Error Parsing returned data ", ex);
							Window.alert("Error parsing returned data!");
						} finally {

						}
						// iwo.setPixelOffet(Size.newInstance(0, .1));

					}

					@Override
					public void onFailure(Throwable throwable) {
						logger.log(Level.SEVERE,
								"Error occured in processing request",
								throwable);

						Window.alert("Error in contacting server. Try later");
						return;

					}

				});
	}

	HashMap<String, BandInfo> getBandInfo() {
		return bandInfo;
	}

	Set<String> getBandNames() {
		return bandInfo.keySet();
	}

	BandInfo getBandInfo(String bandName) {
		return bandInfo.get(bandName);
	}

	float getMaxOccupancy() {
		return maxOccupancy;
	}

	float getMinOccupancy() {
		return minOccupancy;
	}

	
	long getAcquistionCount() {
		return acquistionCount;
	}

	long gettEndReadings() {
		return tEndReadings;
	}

	long gettStartDayBoundary() {
		return tStartDayBoundary;
	}

	String getMeasurementType() {
		return measurementType;
	}

	long gettStartReadings() {
		return tStartReadings;
	}

	String gettStartLocalFormattedTimeStamp() {
		return tStartLocalFormattedTimeStamp;
	}

	String gettEndLocalFormattedTimeStamp() {
		return tEndLocalFormattedTimeStamp;
	}

	public String getCotsSensorModel() {
		return systemMessageJsonObject.get(Defines.COTS_SENSOR).isObject()
				.get(Defines.MODEL).isString().stringValue();
	}

	public String getSensorAntennaType() {
		return systemMessageJsonObject.get(Defines.ANTENNA).isObject().get(Defines.MODEL)
				.isString().stringValue();
	}

	private String getFormattedFrequencyRanges() {
		StringBuilder retval = new StringBuilder();
		for (String r : this.bandInfo.keySet()) {
			retval.append(r + " <br/>");
		}
		return retval.toString();
	}

	public String getTstartLocalTimeAsString() {
		return this.tStartLocalFormattedTimeStamp;
	}

	public String getTendReadingsLocalTimeAsString() {
		return this.tEndLocalFormattedTimeStamp;
	}
	
	public HashSet<FrequencyRange> getFreqRanges() {
		return this.frequencyRanges;
	}
	
	
	public HTML getBandDescription(String bandName) {
		BandInfo bi = this.bandInfo.get(bandName);
		if (bi == null ) {
			logger.log(Level.SEVERE, "Band  " + bandName + " not found : " + this.getSensorId());
			return null;
		}
		return new HTML(bi.getDescription());
	}
	

	public HTML getSensorDescription() {

		HTML retval =  new HTML( "<b>Sensor Info </b>"
				+ "<div align=\"left\", height=\"300px\">"
				+ "<br/>Sensor ID = "
				+ sensorId
				+ "<br/>Location: Lat = "
				+ NumberFormat.getFormat("00.00").format(lat)
				+ "; Long = "
				+ NumberFormat.getFormat("00.00").format(lng)
				+ "; Alt = "
				+ this.formatToPrecision(2, alt)
				+ " Ft."
				+ "<br/> Sensor ID = "
				+ sensorId
				+ "<br/> Sensor Model = "
				+ getCotsSensorModel()
				+ "<br/>Antenna Type = "
				+ getSensorAntennaType()
				+ "<br/> Measurement Type = "
				+ measurementType
				+ "<br/>Measurement: Start = "
				+ this.gettStartLocalFormattedTimeStamp()
				+ "; End = "
				+ this.gettEndLocalFormattedTimeStamp()
				+ "<br/>Occupancy: Max = "
				+ this.formatToPrecision(2, maxOccupancy * 100)
				+ "%"
				+ " Min = "
				+ this.formatToPrecision(2, minOccupancy * 100)
				+ "%"
				+ "<br/>Aquisition Count = "
				+ acquistionCount
				+ "<br/><br/></div>");
		retval.setStyleName("sensorInfo");
		return retval;
	}

	public String getSensorId() {
		return this.sensorId;
	}
	
	public void setSelectedBand(String bandName) {
		this.selectedBand = this.bandInfo.get(bandName);
	}

	public BandInfo getSelectedBand() {
		return this.selectedBand;
	}

	public boolean containsSys2detect(String sys2Detect) {
		for (FrequencyRange range : this.frequencyRanges) {
			if (range.sys2detect.equals(sys2Detect)) {
				return true;
			}
		}
		return false;
	}

}
