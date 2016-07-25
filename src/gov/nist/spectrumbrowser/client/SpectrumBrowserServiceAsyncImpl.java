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

import gov.nist.spectrumbrowser.admin.Admin;
import gov.nist.spectrumbrowser.common.AbstractSpectrumBrowserService;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Logger;

import com.google.gwt.user.client.Window;


public class SpectrumBrowserServiceAsyncImpl 
		extends AbstractSpectrumBrowserService implements
		SpectrumBrowserServiceAsync  {
	
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	
	public SpectrumBrowserServiceAsyncImpl(String baseUrl) {
		this.baseUrl = baseUrl;
	}

	@Override
	public void getLocationInfo(String sessionId,
			SpectrumBrowserCallback<String> callback) {
		logger.finer("getLocationInfo " + sessionId);
		String uri = "getLocationInfo/" + sessionId;
		dispatch(uri, callback);
	}

	@Override
	public void getDataSummary( String sensorId,double lat, double lng, double alt,
			 long minTime, int dayCount, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri;
		if (minTime >= 0 && dayCount > 0) {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId + "?minTime=" + minTime + "&dayCount="
					+ dayCount + "&minFreq=" + minFreq + "&maxFreq=" + maxFreq;
		} else if (minTime > 0) {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId + "?minTime=" + minTime + "&minFreq="+ minFreq + "&maxFreq=" + maxFreq;
		} else {
			uri = "getDataSummary/" + sensorId + "/" + lat + "/" + lng + "/" + alt + "/"
					+ sessionId;
		}
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,uri, callback);
	}

	
	@Override
	public void getPowerVsTimeAndSpectrum(String sensorId,
			long time, long freq, long minTime, long maxTime, long minFreq,
			long maxFreq, SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "getPowerVsTimeAndSpectrum/" + sessionId + "/"
				+ sensorId + "/" + minTime + "/" + maxTime + "/" + minFreq
				+ "/" + maxFreq + "/" + time + "/" + freq;
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,uri, callback);

	}

	@Override
	public void generateDailyStatistics(String sensorId,
			long minTime, long minFreq, long maxFreq, int minPower,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "getPowerVsTimeAndSpectrum/" + sensorId + "/" + minTime
				+ "/" + minFreq + "/" + sessionId + "?minPower=" + minPower;
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		dispatch(baseUrl,url, callback);

	}

	@Override
	public void getDailyMaxMinMeanStats(String sensorId,
			double latitude, double longitude, double altitude,
			long minDate, long dayCount, String sys2detect, long minFreq, long maxFreq,
			long subBandMinFreq, long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri;
		String spos = sensorId + "/" + latitude + "/" + longitude + "/" + altitude;
		
		if (minFreq == subBandMinFreq && maxFreq == subBandMaxFreq) {
			uri = "getDailyMaxMinMeanStats/" + spos +  "/" +  minDate
				+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
				+ sessionId;
		} else if ( minFreq == subBandMinFreq) {
			uri = "getDailyMaxMinMeanStats/" + spos + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMaxFreq=" + subBandMaxFreq;
		} else if ( maxFreq == subBandMaxFreq) {
			uri = "getDailyMaxMinMeanStats/" + spos + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq;
		} else {
			uri = "getDailyMaxMinMeanStats/" + spos + "/" + minDate
					+ "/" + dayCount + "/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/"
					+ sessionId + "?subBandMinFreq=" + subBandMinFreq + "&" 
					+ "subBandMaxFreq=" + subBandMaxFreq;
		}
		dispatch(baseUrl,uri, callback);

	}

	

	@Override
	public void getOneDayStats(String sensorId,
			double lat, double lon, double alt,
			long startTime, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback)
			throws IllegalArgumentException {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);

		String uri = "getOneDayStats/" + sensorId + "/" + lat + "/" + lon + "/" + alt +
				"/" + startTime + "/" +sys2detect + "/" +  minFreq + "/" + maxFreq + "/"
				+ sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sensorId, long acquisitionTime,
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
		    String sensorId, long acquisitionTime,
			String sys2detect,
			long minFreq, long maxFreq,
			int cutoff, SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy" + "/"
				+ sensorId + "/" + acquisitionTime +"/" + sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSpectrum(String sensorId,
			long startTime, long timeOffset,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSpectrum(String sensorId,
			long startTime, long timeOffset, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generateSpectrum/" + sensorId + "/" + startTime + "/"
				+ timeOffset + "/" + sessionId + "?subBandMinFrequency=" + minFreq +
				"&subBandMaxFrequency=" + maxFreq;
		dispatch(baseUrl,uri, callback);
	}
	@Override
	public void generatePowerVsTime(String sensorId,
			long startTime, long freq, SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId;
		dispatch(baseUrl,uri, callback);

	}

	@Override
	public void generatePowerVsTime(String sensorId,
			long startTime, long freq, int leftBound, int rightBound,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generatePowerVsTime/" + sensorId + "/" + startTime + "/"
				+ freq + "/" + sessionId + "?leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleAcquisitionSpectrogramAndOccupancy(
			String sensorId, long acquisitionTime,
			String sys2detect, long minFreq, long maxFreq,
			int leftBound, int rightBound, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateSingleAcquisitionSpectrogramAndOccupancy/"
				+ sensorId + "/" + acquisitionTime + "/" + sys2detect + "/" + minFreq + "/"
				+ maxFreq + "/" + sessionId
				+ "?cutoff=" + cutoff + "&leftBound=" + leftBound
				+ "&rightBound=" + rightBound;
		dispatch(baseUrl,uri, callback);
	}

	
	@Override
	public void generateSingleDaySpectrogramAndOccupancy(
			String sensorId,
			double lat,
			double lon,
			double alt,
			long acquistionTime,
			String sys2detect,
			long minFreq,
			long maxFreq,
			long subBandMinFreq,
			long subBandMaxFreq,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" 
				+ lat + "/" + lon + "/" + alt + "/"
				+ acquistionTime + "/" + sys2detect + "/"+ minFreq + "/" + maxFreq + "/" + sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq=" + subBandMaxFreq;
		dispatch(baseUrl,uri, callback);
	}

	@Override
	public void generateSingleDaySpectrogramAndOccupancy(
			String sensorId, double lat, double lon, double alt, long acquisitionTime, String sys2detect, long minFreq,
			long maxFreq, long subBandMinFreq, long subBandMaxFreq, int cutoff,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);

		String uri = "generateSingleDaySpectrogramAndOccupancy/"
				+ sensorId + "/" 
				+ lat + "/"
				+ lon + "/"
				+ alt + "/"
				+ acquisitionTime + "/" 
				+ sys2detect + "/" 
				+ minFreq + "/" 
				+ maxFreq + "/" 
				+ sessionId + "?" 
			+ "subBandMinFreq=" + subBandMinFreq + "&subBandMaxFreq" + subBandMaxFreq+ "&cutoff=" + cutoff;
		dispatch(baseUrl,uri, callback);
		
	}

	

	@Override
	public void generateZipFileForDownload(String sensorId,
			long startTime, int dayCount, String sys2detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "generateZipFileFileForDownload"+  "/" + sensorId +"/" + startTime + "/" + dayCount + "/" +
			sys2detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,uri,callback);
	}
	
	@Override
	public void getCaptureEvents(String sensorId,  long selectedStartTime, int dayCount,  SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "getCaptureEvents"+  "/" + sensorId +"/" +  Long.toString(selectedStartTime) + "/" + dayCount + "/" +  sessionId;
		dispatch(baseUrl,uri,callback);
	}

	@Override
	public void emailUrlToUser(
			String sensorId,
			String uri, 
			String emailAddress,SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "emailDumpUrlToUser" + "/"  + emailAddress + "/" + sessionId +  "?uri=" + uri;
		dispatch(url,callback);
		
	}

	
	@Override
	public void checkForDumpAvailability(String sensorId, String uri,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String uri2 = "checkForDumpAvailability/" + sessionId + "?uri=" + uri;
		dispatch(baseUrl,uri2,callback);
	}

	@Override
	public void getLastAcquisitionTime(String sensorId,
			String sys2Detect, long minFreq, long maxFreq,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String url = "getLastAcquisitionTime/" + sensorId + "/" +sys2Detect + "/" + minFreq + "/" + maxFreq + "/" + sessionId;
		dispatch(baseUrl,url,callback);
	}

	@Override
	public void getAcquisitionCount(String sensorId, double lat, double lon, double alt, String sys2Detect, long minFreq,
			long maxFreq, long selectedStartTime, int dayCount,
			SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String url = "getAcquisitionCount/" + sensorId + "/" + lat + "/" + lon + "/" + alt + "/" + sys2Detect + "/" + minFreq + "/" + maxFreq + "/" 
			+ selectedStartTime + "/" + dayCount + "/" + sessionId;
		dispatch(url,callback);
	}

	@Override
	public void requestNewAccount(String jsonContent, SpectrumBrowserCallback<String> callback) {

		String url = "requestNewAccount";
		dispatchWithJsonContent(url, jsonContent, callback);
	}

	@Override
	public void getLastAcquisitionTime(String sensorId,
			SpectrumBrowserCallback<String> callback) {
		String url = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "getLastSensorAcquisitionTimeStamp/" + sensorId + "/" + sessionId;
		dispatch (url,uri,callback);
		
	}
	
	@Override
	public void changePassword(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String url = "changePassword";
		dispatchWithJsonContent(url, jsonContent, callback);
	}
	
	@Override
	public void requestNewPassword(String jsonContent, SpectrumBrowserCallback<String> callback) {
		String url = "requestNewPassword";
		dispatchWithJsonContent(url, jsonContent, callback);
	}

    @Override
	public void isAuthenticationRequired(
			SpectrumBrowserCallback<String> callback) {

		String uri = "isAuthenticationRequired";
		dispatch(uri,callback);
	}
    
    @Override
	public void isAuthenticationRequired(String url,
			SpectrumBrowserCallback<String> callback) {
		String uri = "/spectrumbrowser/isAuthenticationRequired";
		dispatch(url,uri,callback);
	}

	@Override
	public void logOff(SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionToken();
		super.logOut(sessionId, callback);
		
	}
	
	@Override
	public void logOff(String sensorId, SpectrumBrowserCallback<String> callback) {
		String baseUrl = SpectrumBrowser.getBaseUrl(sensorId);
		String sessionId = SpectrumBrowser.getSessionTokenForSensor(sensorId);
		String uri = "logOut/"+ sessionId;
		dispatch(baseUrl,uri,callback);
	}

	@Override
	public void getScreenConfig(SpectrumBrowserCallback<String> callback) {
		String uri = "getScreenConfig";
		super.dispatch(uri, callback);
		
	}
	
	@Override
	public void checkSessionTimeout(SpectrumBrowserCallback<String> callback) {
		String sessionId = SpectrumBrowser.getSessionToken();
		String uri = "checkSessionTimeout/" + sessionId;
		super.dispatch(uri,callback);
	}

}
